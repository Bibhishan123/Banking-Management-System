import threading
import smtplib
from email.message import EmailMessage
from .config import Config

cfg = Config()


def send_account_created_email(account):
    """
    Synchronous email sender for development/testing.
    Configure SMTP via env variables defined in config.Config.
    Raises on failure so callers can log/handle as needed.
    """
    msg = EmailMessage()
    msg["Subject"] = f"Account created: {account.number}"
    msg["From"] = "no-reply@example.com"
    msg["To"] = "owner@example.com"
    msg.set_content(f"Account {account.name} ({account.number}) created with balance {account.balance}")

    with smtplib.SMTP(cfg.SMTP_HOST, cfg.SMTP_PORT, timeout=5) as s:
        if cfg.SMTP_USER and cfg.SMTP_PASS:
            s.login(cfg.SMTP_USER, cfg.SMTP_PASS)
        s.send_message(msg)


def send_account_created_email_in_background(account):
    """
    Convenience wrapper: run synchronous send in a daemon thread.
    Returns the Thread object.
    """
    t = threading.Thread(target=send_account_created_email, args=(account,), daemon=True)
    t.start()
    return t
