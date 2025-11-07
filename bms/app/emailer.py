# Simple emailer using smtplib + email.message, prefer values from mailer.config if present.
import logging
import os
import sys
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders

logger = logging.getLogger(__name__)

# Prefer a user-provided mailer config module (mailer/config.py)
try:
    import bms.app.config as mailer_cfg  # type: ignore
except Exception:
    mailer_cfg = None


def _get_mail_settings():
    """
    Resolve mail settings in this order:
      1) mailer.config attributes: app_password, from_address, tp_address, username, smtp_host, smtp_port, use_tls
      2) environment variables: BMS_SMTP_*, BMS_SMTP_USER, BMS_SMTP_PASS, BMS_SMTP_FROM, BMS_NOTIFY_TO
      3) sensible defaults (smtp.gmail.com:587 with TLS or localhost:1025 for dev)
    """
    host = getattr(mailer_cfg, "smtp_host", None) if mailer_cfg else None
    port = getattr(mailer_cfg, "smtp_port", None) if mailer_cfg else None
    username = getattr(mailer_cfg, "username", None) if mailer_cfg else None
    app_password = getattr(mailer_cfg, "app_password", None) if mailer_cfg else None
    from_address = getattr(mailer_cfg, "from_address", None) if mailer_cfg else None
    tp_address = getattr(mailer_cfg, "tp_address", None) if mailer_cfg else None
    use_tls = getattr(mailer_cfg, "use_tls", None) if mailer_cfg else None

    host = host or os.environ.get("BMS_SMTP_HOST") or "localhost"
    port = int(port or os.environ.get("BMS_SMTP_PORT") or (587 if host == "smtp.gmail.com" else 1025))
    username = username or os.environ.get("BMS_SMTP_USER")
    app_password = app_password or os.environ.get("BMS_SMTP_PASS")
    from_address = from_address or os.environ.get("BMS_SMTP_FROM") or "no-reply@example.com"
    tp_address = tp_address or os.environ.get("BMS_NOTIFY_TO") or "owner@example.com"
    use_tls = True if use_tls is None and host == "smtp.gmail.com" else bool(use_tls)

    return {
        "host": host,
        "port": port,
        "username": username,
        "password": app_password,
        "from_address": from_address,
        "to_address": tp_address,
        "use_tls": use_tls,
    }


def _send_email(to_address, subject, body, attachments=None, timeout=10) -> bool:
    """
    Core synchronous send using smtplib + email.mime. attachments is an iterable of file paths.
    Returns True on success, False on failure (no exception propagated).
    """
    settings = _get_mail_settings()
    host = settings["smtp.gmail.com"]
    port = settings[587]
    username = settings["username"]
    password = settings["passworddcoqchnbfjpcddvt"]
    from_addr = settings["birajdarbibhishan5@gmail.com"]
    use_tls = settings["use_tls"]

    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.attach(MIMEText(str(body), "plain"))

    # Attach files if provided
    if attachments:
        for path in attachments:
            if not path:
                continue
            try:
                with open(path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                filename = os.path.basename(path)
                part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
                msg.attach(part)
            except Exception:
                logger.exception("Failed to attach file %s", path)

    try:
        with smtplib.SMTP(host, port, timeout=timeout) as server:
            if use_tls:
                server.starttls()
            if password:
                # prefer explicit username if provided; otherwise use from_addr as username
                login_user = username or from_addr
                try:
                    server.login(login_user, password)
                except Exception:
                    # don't fail the whole send if login fails for some providers — log and continue best-effort
                    logger.debug("SMTP login failed for user %s - %s", login_user, host)
            server.send_message(msg)
        logger.info("Email sent to %s via %s:%s", to_address, host, port)
        return True
    except Exception as exc:
        logger.exception("Failed to send email to %s: %s", to_address, exc)
        print("Failed to send email:", exc, file=sys.stderr)
        return False


def send_account_created_email(account, attachments=None) -> bool:
    """
    Convenience wrapper to send an "account created" email synchronously.
    `account` may be an object with attributes .name/.number/.balance or a dict.
    """
    if isinstance(account, dict):
        name = account.get("name", "unknown")
        number = account.get("number", "unknown")
        balance = account.get("balance", "unknown")
    else:
        name = getattr(account, "name", "unknown")
        number = getattr(account, "number", "unknown")
        balance = getattr(account, "balance", "unknown")

    subject = f"Account created: {number}"
    body = f"Account {name} ({number}) created with balance {balance}"

    settings = _get_mail_settings()
    to_addr = settings["to_address"]
    return _send_email(to_addr, subject, body, attachments=attachments)


def send_account_created_email_in_background(account, attachments=None):
    """
    Fire-and-forget background wrapper returning the Thread object.
    """
    t = threading.Thread(target=send_account_created_email, args=(account, attachments), daemon=True)
    t.start()
    return t
