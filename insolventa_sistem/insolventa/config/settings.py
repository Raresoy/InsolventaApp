from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

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

TRIBUNALS = [
    "Tribunalul Bucuresti",
    "Tribunalul Cluj"
]

DELAY_SEC = 2
MAX_RETRY = 3


# =========================
# MAILTRAP CONFIG (TEST)
# =========================

SMTP_HOST = "sandbox.smtp.mailtrap.io"
SMTP_PORT = 2525

SMTP_USER = "9d823d1b1c4f01"
SMTP_PASS = "08485c85fe6875"

EMAIL_FROM = "insolventa@test.local"
EMAIL_TO = "youremail@example.com"