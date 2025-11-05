from typing import Any, Dict, List, Optional
from decimal import Decimal
import threading
import logging

from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from . import models
from .exceptions import NotFoundError, DuplicateError, DatabaseError

logger = logging.getLogger(__name__)


# Optional emailer helpers (best-effort, non-fatal)
try:
    # Prefer a background helper if the project provides one
    from .emailer import send_account_created_email_in_background as _send_email_bg
    _EMAIL_BG_AVAILABLE = True
except Exception:
    _EMAIL_BG_AVAILABLE = False
    try:
        # Fallback to synchronous sender if present
        from .emailer import send_account_created_email as _send_email_sync  # type: ignore
    except Exception:
        _send_email_sync = None


def _dispatch_create_email(account: models.Account) -> None:
    """Dispatch account-created notification (best-effort)."""
    try:
        if _EMAIL_BG_AVAILABLE:
            # emailer is expected to handle its own errors/logging
            _send_email_bg(account)
        elif _send_email_sync:
            # run sync sender in a daemon thread so CRUD is non-blocking
            t = threading.Thread(target=_send_email_sync, args=(account,), daemon=True)
            t.start()
    except Exception:
        logger.exception("Failed to dispatch account-created email for account id=%s", getattr(account, "id", None))


def create_account(db: Session, name: str, number: str, balance: Decimal = Decimal("0.0")) -> models.Account:
    """
    Create and persist a new Account.

    - Validates inputs.
    - Ensures unique account number.
    - Commits transaction and returns refreshed instance.
    - Triggers best-effort email notification in background.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a non-empty string")
    if not isinstance(number, str) or not number.strip():
        raise ValueError("number must be a non-empty string")

    try:
        balance = Decimal(balance)
    except Exception:
        raise ValueError("balance must be numeric/convertible to Decimal")

    # uniqueness check
    existing = db.execute(select(models.Account).where(models.Account.number == number.strip())).scalars().first()
    if existing:
        raise DuplicateError(f"Account with number {number!s} already exists")

    account = models.Account(name=name.strip(), number=number.strip(), balance=balance)
    db.add(account)
    try:
        db.commit()
        db.refresh(account)
        logger.info("Created account id=%s number=%s", account.id, account.number)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database error while creating account: %s", exc)
        raise DatabaseError("Failed to create account") from exc

    # send notification (best-effort, non-blocking)
    try:
        _dispatch_create_email(account)
    except Exception:
        # already logged in helper; do not raise
        pass

    return account


def get_account_by_id(db: Session, account_id: int) -> models.Account:
    """Return Account by primary key or raise NotFoundError."""
    account = db.get(models.Account, account_id)
    if account is None:
        logger.debug("Account not found by id=%s", account_id)
        raise NotFoundError(f"Account id={account_id} not found")
    return account


def get_account_by_number(db: Session, number: str) -> models.Account:
    """Return Account by unique account number or raise NotFoundError."""
    account = db.execute(select(models.Account).where(models.Account.number == number.strip())).scalars().first()
    if account is None:
        logger.debug("Account not found by number=%s", number)
        raise NotFoundError(f"Account number={number} not found")
    return account


def list_accounts(db: Session, limit: int = 100, offset: int = 0) -> List[models.Account]:
    """
    Return a paginated list of accounts ordered by id ascending.
    Enforces reasonable bounds on limit.
    """
    try:
        limit = max(1, min(1000, int(limit)))
        offset = max(0, int(offset))
    except Exception:
        raise ValueError("limit and offset must be integers")

    stmt = select(models.Account).order_by(models.Account.id).limit(limit).offset(offset)
    results = db.execute(stmt).scalars().all()
    logger.debug("Listed accounts limit=%s offset=%s returned=%s", limit, offset, len(results))
    return results


def update_account(db: Session, account_id: int, changes: Dict[str, Any]) -> models.Account:
    """
    Update allowed fields of an account. Allowed keys: name, number, balance.

    - Ensures account number uniqueness if changed.
    - Commits and returns refreshed Account.
    """
    if not changes:
        raise ValueError("No changes provided")

    allowed = {"name", "number", "balance"}
    invalid = set(changes.keys()) - allowed
    if invalid:
        raise ValueError(f"Invalid update keys: {invalid}")

    account = get_account_by_id(db, account_id)  # may raise NotFoundError

    # handle number change
    if "number" in changes:
        new_number = str(changes["number"]).strip()
        if not new_number:
            raise ValueError("number must be a non-empty string")
        if new_number != account.number:
            exists = db.execute(select(models.Account).where(models.Account.number == new_number)).scalars().first()
            if exists:
                raise DuplicateError(f"Account number {new_number} already in use")
            account.number = new_number

    if "name" in changes:
        new_name = str(changes["name"]).strip()
        if not new_name:
            raise ValueError("name must be a non-empty string")
        account.name = new_name

    if "balance" in changes:
        try:
            account.balance = Decimal(changes["balance"])
        except Exception:
            raise ValueError("balance must be numeric/convertible to Decimal")

    try:
        db.add(account)
        db.commit()
        db.refresh(account)
        logger.info("Updated account id=%s changes=%s", account.id, {k: changes[k] for k in changes})
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database error while updating account id=%s: %s", account_id, exc)
        raise DatabaseError("Failed to update account") from exc

    return account


def delete_account(db: Session, account_id: int) -> None:
    """Delete an account by id. Raises NotFoundError if missing."""
    account = get_account_by_id(db, account_id)
    try:
        db.delete(account)
        db.commit()
        logger.info("Deleted account id=%s number=%s", account.id, account.number)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database error while deleting account id=%s: %s", account_id, exc)
        raise DatabaseError("Failed to delete account") from exc