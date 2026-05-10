import os
import time
import sqlite3
import smtplib
import logging
import json
from datetime import date, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# PDF renderer
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
from pdf_renderer import PDFRenderer

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

TEST_MODE = True   # 👈 schimbă pe False când vrei scraping real

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("monitor.log", encoding="utf-8"),
    ],
)

log = logging.getLogger(__name__)

OUTPUT_DIR = BASE_DIR / "output_pdfs"
OUTPUT_DIR.mkdir(exist_ok=True)

DB_PATH = BASE_DIR / "dosare.db"

BASE_URL = "https://portal.just.ro/SitePages/cautare.aspx"

# ─────────────────────────────────────────────
# PDF
# ─────────────────────────────────────────────

renderer = PDFRenderer(
    template_path=str(BASE_DIR / "templates/template.pdf")
)

def make_pdf(d):
    safe_name = d["nr_dosar"].replace("/", "-")
    out = OUTPUT_DIR / f"oferta_{safe_name}.pdf"
    return renderer.render(d, str(out))


# ─────────────────────────────────────────────
# DB
# ─────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dosare (
            nr_dosar TEXT PRIMARY KEY,
            debitor TEXT,
            nr_inregistrare TEXT,
            tribunal TEXT,
            data_inreg TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    return conn


def exists(conn, nr):
    return conn.execute(
        "SELECT 1 FROM dosare WHERE nr_dosar=?",
        (nr,)
    ).fetchone() is not None


def save(conn, d):
    conn.execute("""
        INSERT OR IGNORE INTO dosare VALUES (?, ?, ?, ?, ?, ?)
    """, (
        d["nr_dosar"],
        d["debitor"],
        d["nr_inregistrare"],
        d["tribunal"],
        d["data_inreg"],
        datetime.now().isoformat(),
    ))
    conn.commit()


# ─────────────────────────────────────────────
# HTTP SESSION (SSL FIX DEV MODE)
# ─────────────────────────────────────────────

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SESSION = requests.Session()
SESSION.verify = False  # DEV ONLY
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0"
})

DELAY = 2


# ─────────────────────────────────────────────
# SCRAPER
# ─────────────────────────────────────────────

def cauta(tribunal, data_azi):

    # ─── TEST MODE ───
    if TEST_MODE:
        log.info("🧪 TEST MODE ACTIV")
        return [
            {
                "nr_dosar": "TEST/111/2026",
                "debitor": "COMPANIE TEST SRL",
                "nr_inregistrare": "1/10.05.2026",
                "tribunal": tribunal,
                "data_inreg": data_azi,
            }
        ]

    # ─── REAL MODE ───
    try:
        time.sleep(DELAY)
        r = SESSION.get(BASE_URL, timeout=30)

        soup = BeautifulSoup(r.text, "html.parser")

        payload = {
            "ctl00$ContentPlaceHolder1$txtDataDe": data_azi,
            "ctl00$ContentPlaceHolder1$txtDataPana": data_azi,
            "ctl00$ContentPlaceHolder1$ddlMaterie": "Insolvenţă",
            "ctl00$ContentPlaceHolder1$ddlInstanta": tribunal,
            "ctl00$ContentPlaceHolder1$btnCautare": "Caută",
        }

        time.sleep(DELAY)
        r2 = SESSION.post(BASE_URL, data=payload, timeout=30)

        soup2 = BeautifulSoup(r2.text, "html.parser")

        table = soup2.find("table", id=lambda x: x and "GridView" in x)

        if not table:
            log.info("No results found")
            return []

        out = []

        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue

            nr = cols[0].get_text(strip=True)
            if not nr:
                continue

            out.append({
                "nr_dosar": nr,
                "debitor": cols[1].get_text(strip=True),
                "nr_inregistrare": cols[2].get_text(strip=True),
                "tribunal": tribunal,
                "data_inreg": data_azi,
            })

        return out

    except Exception as e:
        log.error(f"Scraper error: {e}")
        return []


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():

    log.info("START MONITOR")

    data = date.today().strftime("%d.%m.%Y")

    tribunale = {
        "Tribunalul Bihor": "test@example.com"
    }

    conn = init_db()

    total = 0

    for tribunal, email in tribunale.items():

        log.info(f"TRIBUNAL: {tribunal}")

        dosare = cauta(tribunal, data)

        for d in dosare:

            if exists(conn, d["nr_dosar"]):
                continue

            log.info(f"NEW DOSAR: {d['nr_dosar']}")

            try:
                pdf = make_pdf(d)
                save(conn, d)
                total += 1

                log.info(f"PDF GENERATED: {pdf}")

            except Exception as e:
                log.error(f"PDF ERROR: {e}")

    conn.close()

    log.info(f"DONE: {total} dosare noi")


if __name__ == "__main__":
    main()