import os
import smtplib
from email.message import EmailMessage
from typing import Tuple, Optional
from datetime import datetime

def _bool(v: Optional[str]) -> bool:
    return str(v or "").strip().lower() in {"1", "true", "yes", "y", "on"}

def send_email(
    to: str,
    subject: str,
    text: str,
    html: Optional[str] = None,
    from_addr: Optional[str] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Returns (ok, error_message). If SMTP env is missing, we log to console and return ok=True.
    """
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    from_email = from_addr or os.getenv("FROM_EMAIL", "no-reply@traqcheck.local")

    # Dev fallback: log-only
    if not host or not user or not password:
        print("[DEV-EMAIL] Would send email:")
        print(f"  To: {to}")
        print(f"  Subject: {subject}")
        print(f"  Text:\n{text}")
        if html:
            print(f"  HTML:\n{html}")
        return True, None

    try:
        msg = EmailMessage()
        msg["From"] = from_email
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(text)
        if html:
            msg.add_alternative(html, subtype="html")

        with smtplib.SMTP(host, port) as s:
            s.starttls()
            s.login(user, password)
            s.send_message(msg)
        return True, None
    except Exception as e:
        return False, str(e)


def send_sms(to: str, text: str) -> Tuple[bool, Optional[str]]:
    """
    Returns (ok, error_message). If Twilio env is missing, we log to console and return ok=True.
    """
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    from_num = os.getenv("TWILIO_FROM")

    # Dev fallback: log-only
    if not sid or not token or not from_num:
        print("[DEV-SMS] Would send SMS:")
        print(f"  To: {to}")
        print(f"  Text:\n{text}")
        return True, None

    try:
        from twilio.rest import Client  # type: ignore
        client = Client(sid, token)
        msg = client.messages.create(body=text, from_=from_num, to=to)
        # msg.sid is available; you can persist if wanted
        return True, None
    except Exception as e:
        return False, str(e)
