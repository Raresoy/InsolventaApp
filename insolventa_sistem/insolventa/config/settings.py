import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent\

load_dotenv(BASE_DIR / "variabile_mediu.env")

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"

DATA_DIR.mkdir(exist_ok=True, parents=True)
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
LOG_DIR.mkdir(exist_ok=True, parents=True)

TEMPLATE_DIR = BASE_DIR / "templates"
PDF_TEMPLATE = TEMPLATE_DIR / "template.pdf"
DB_PATH = DATA_DIR / "dosare.db"

BASE_URL = "https://portal.just.ro/SitePages/cautare.aspx"

# Tribunal -> email destinatar
TRIBUNALS = {
    "Tribunalul Bucuresti": os.environ["EMAIL_BUCURESTI"],
    "Tribunalul Cluj":      os.environ["EMAIL_CLUJ"],
}

DELAY_SEC = 2
MAX_RETRY = 3


# SMTP — citit din environment (GitHub Secrets)
SMTP_HOST = os.environ.get("SMTP_HOST", "sandbox.smtp.mailtrap.io")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "2525"))
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASS = os.environ["SMTP_PASS"]
EMAIL_FROM = os.environ.get("EMAIL_FROM", "insolventa@test.local")