from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "dosare.db"
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"
PDF_TEMPLATE = BASE_DIR / "templates" / "template.pdf"

OUTPUT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

DELAY_SECUNDE = 4
MAX_EMAILS_PER_RUN = 20
MAX_RETRY = 3

BASE_URL = "https://portal.just.ro/SitePages/cautare.aspx"

GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_PASSWORD = os.environ["GMAIL_PASSWORD"]

EMAIL_SUBIECT = os.environ.get(
    "EMAIL_SUBIECT",
    "Oferta lichidator judiciar – Dosar {nr_dosar} – {debitor}"
)

EMAIL_CORP = os.environ.get(
    "EMAIL_CORP",
    """Stimate Grefier,

Va transmitem alaturat oferta de lichidator judiciar pentru dosarul {nr_dosar}.

Cu stima,
{expeditor}
"""
)