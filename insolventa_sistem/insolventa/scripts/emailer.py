import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path

from config.settings import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, EMAIL_FROM

log = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str, pdf_path: Path = None):
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = to
    msg.attach(MIMEText(body, "plain"))

    if pdf_path and Path(pdf_path).exists():
        with open(pdf_path, "rb") as f:
            part = MIMEApplication(f.read(), _subtype="pdf")
            part.add_header(
                "Content-Disposition",
                "attachment",
                filename=Path(pdf_path).name
            )
            msg.attach(part)
    elif pdf_path:
        log.warning(f"PDF nu exista la calea: {pdf_path}")

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        log.info(f"Email trimis catre {to}")
    except Exception as e:
        log.error(f"Email error catre {to}: {e}")
        raise