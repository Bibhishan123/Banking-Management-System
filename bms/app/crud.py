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


try:
    from .emailer import send_account_created_email_in_background as _send_email_bg
    _EMAIL_BG_AVAILABLE = True
except Exception:
    _EMAIL_BG_AVAILABLE = False
    try:
        from .emailer import send_account_created_email as _send_email_sync  # type: ignore
    except Exception:
        _send_email_sync = None


def _dispatch_create_email(account: models.Account) -> None:
    """
    Dispatch an account-created notification.

    Prefer an asynchronous/background sender if available; otherwise launch
    a short-lived daemon thread to call a synchronous sender. All exceptions
    are caught and logged so email failures do not affect database operations.

    Args:
        account: The Account instance that was created.
    """
    try:
        if _EMAIL_BG_AVAILABLE:
            _send_email_bg(account)
        elif _send_email_sync:
            t = threading.Thread(target=_send_email_sync, args=(account,), daemon=True)
            t.start()
    except Exception:
        logger.exception("Failed to dispatch account-created email for account id=%s", getattr(account, "id", None))


def create_account(db: Session, name: str, number: str, balance: Decimal = Decimal("0.0")) -> models.Account:
    """
    Create and persist a new Account.

    Validates inputs (non-empty name and number, numeric balance), enforces
    unique account number at the application level, commits the new row and
    refreshes the instance. Attempts to dispatch an account-created email but
    does not fail the operation if email sending fails.

    Args:
        db: SQLAlchemy Session to use for the operation.
        name: Account holder name (non-empty string).
        number: Account unique number (non-empty string).
        balance: Initial balance (Decimal or convertible to Decimal).

    Returns:
        The created models.Account instance.

    Raises:
        ValueError: On invalid input types/values.
        DuplicateError: If an account with the given number already exists.
        DatabaseError: On SQLAlchemy commit/DB failure.
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

    try:
        _dispatch_create_email(account)
    except Exception:
        pass

    return account


def get_account_by_id(db: Session, account_id: int) -> models.Account:
    """
    Return an Account by primary key.

    Args:
        db: SQLAlchemy Session to use.
        account_id: Primary key of the account.

    Returns:
        The matching models.Account.

    Raises:
        NotFoundError: If no account exists with the given id.
    """
    account = db.get(models.Account, account_id)
    if account is None:
        logger.debug("Account not found by id=%s", account_id)
        raise NotFoundError(f"Account id={account_id} not found")
    return account


def get_account_by_number(db: Session, number: str) -> models.Account:
    """
    Return an Account by its unique account number.

    Args:
        db: SQLAlchemy Session to use.
        number: Account number to look up.

    Returns:
        The matching models.Account.

    Raises:
        NotFoundError: If no account exists with the given number.
    """
    account = db.execute(select(models.Account).where(models.Account.number == number.strip())).scalars().first()
    if account is None:
        logger.debug("Account not found by number=%s", number)
        raise NotFoundError(f"Account number={number} not found")
    return account


def list_accounts(db: Session, limit: int = 100, offset: int = 0) -> List[models.Account]:
    """
    Return a paginated list of accounts ordered by id.

    Args:
        db: SQLAlchemy Session to use.
        limit: Maximum number of accounts to return (clamped to 1..1000).
        offset: Number of rows to skip (must be >= 0).

    Returns:
        List of models.Account instances.

    Raises:
        ValueError: If limit or offset are not integers.
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
    Apply validated changes to an existing Account and persist them.

    Allowed change keys: "name", "number", "balance". Validates non-empty
    strings for name/number and converts balance to Decimal. Enforces unique
    account number if changed.

    Args:
        db: SQLAlchemy Session to use.
        account_id: Primary key of the account to update.
        changes: Dict of fields to update.

    Returns:
        The updated models.Account instance.

    Raises:
        ValueError: If changes is empty or contains invalid keys/values.
        NotFoundError: If the account does not exist.
        DuplicateError: If the new account number is already in use.
        DatabaseError: On SQLAlchemy commit/DB failure.
    """
    if not changes:
        raise ValueError("No changes provided")

    allowed = {"name", "number", "balance"}
    invalid = set(changes.keys()) - allowed
    if invalid:
        raise ValueError(f"Invalid update keys: {invalid}")

    account = get_account_by_id(db, account_id)
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
    """
    Delete an account by id.

    Args:
        db: SQLAlchemy Session to use.
        account_id: Primary key of the account to delete.

    Raises:
        NotFoundError: If no account exists with the given id.
        DatabaseError: On SQLAlchemy commit/DB failure.
    """
    account = get_account_by_id(db, account_id)
    try:
        db.delete(account)
        db.commit()
        logger.info("Deleted account id=%s number=%s", account.id, account.number)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database error while deleting account id=%s: %s", account_id, exc)
        raise DatabaseError("Failed to delete account") from exc
