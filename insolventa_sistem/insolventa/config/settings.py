import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
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
    "Tribunalul Bihor":           os.environ["EMAIL_BIHOR"],
    "Tribunalul Satu Mare":       os.environ["EMAIL_SATU_MARE"],
    "Tribunalul Arad":            os.environ["EMAIL_ARAD"],
    "Tribunalul Timis":           os.environ["EMAIL_TIMIS"],
    "Tribunalul Bistrita-Nasaud": os.environ["EMAIL_BISTRITA"],
    "Tribunalul Cluj":            os.environ["EMAIL_CLUJ"],
    "Tribunalul Maramures":       os.environ["EMAIL_MARAMURES"],
    "Tribunalul Salaj":           os.environ["EMAIL_SALAJ"],
    "Tribunalul Sibiu":           os.environ["EMAIL_SIBIU"],
    "Tribunalul Harghita":        os.environ["EMAIL_HARGHITA"],
    "Tribunalul Mures":           os.environ["EMAIL_MURES"],
    "Tribunalul Neamt":           os.environ["EMAIL_NEAMT"],
}

DELAY_SEC = 2
MAX_RETRY = 3

# SMTP - citit din environment (GitHub Secrets)
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASS = os.environ["SMTP_PASS"]
EMAIL_FROM = os.environ.get("EMAIL_FROM", os.environ["SMTP_USER"])