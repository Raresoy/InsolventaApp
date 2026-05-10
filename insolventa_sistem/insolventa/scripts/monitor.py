"""
Sistem monitorizare dosare insolventa - portal.just.ro
Detecteaza dosare noi, completeaza PDF si trimite email automat.
"""

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
import pymupdf  # pip install pymupdf

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("monitor.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ─── Config din variabile de mediu (GitHub Secrets) ─────────────────────────
GMAIL_USER     = os.environ["GMAIL_USER"]       # ex: oferte.lichidator@gmail.com
GMAIL_PASSWORD = os.environ["GMAIL_PASSWORD"]   # App Password Gmail (16 caractere)
TRIBUNALE_JSON = os.environ["TRIBUNALE_JSON"]   # JSON: {"Tribunalul Cluj": "cluj@just.ro", ...}
EMAIL_SUBIECT  = os.environ.get("EMAIL_SUBIECT", "Oferta lichidator judiciar – Dosar {nr_dosar} – {debitor}")
EMAIL_CORP     = os.environ.get("EMAIL_CORP", """Stimate Grefier,

Va transmitem alaturat oferta de lichidator judiciar pentru dosarul {nr_dosar},
debitor {debitor}, inregistrat la {tribunal} pe data de {data}.

Cu stima,
{expeditor}
""")

PDF_TEMPLATE   = Path("template.pdf")
DB_PATH        = Path("dosare.db")
OUTPUT_DIR     = Path("output_pdfs")
DELAY_SECUNDE  = 3  # delay intre requesturi catre portal.just.ro


# ─── Baza de date ────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dosare (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            nr_dosar      TEXT UNIQUE,
            debitor       TEXT,
            nr_inregistrare TEXT,
            tribunal      TEXT,
            data_inreg    TEXT,
            procesat_la   TEXT
        )
    """)
    conn.commit()
    return conn


def dosar_exista(conn, nr_dosar: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM dosare WHERE nr_dosar = ?", (nr_dosar,)
    ).fetchone()
    return row is not None


def salveaza_dosar(conn, dosar: dict):
    conn.execute(
        """INSERT OR IGNORE INTO dosare
           (nr_dosar, debitor, nr_inregistrare, tribunal, data_inreg, procesat_la)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            dosar["nr_dosar"],
            dosar["debitor"],
            dosar["nr_inregistrare"],
            dosar["tribunal"],
            dosar["data_inreg"],
            datetime.now().isoformat(),
        ),
    )
    conn.commit()
    log.info(f"✔ Dosar salvat in DB: {dosar['nr_dosar']}")


# ─── Scraping portal.just.ro ─────────────────────────────────────────────────
BASE_URL = "https://portal.just.ro/SitePages/cautare.aspx"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
})


def cauta_dosare_tribunal(tribunal_nume: str, data_azi: str) -> list[dict]:
    """
    Cauta dosare de insolventa pentru un tribunal si data data.
    Returneaza lista de dict-uri cu datele dosarului.
    """
    dosare = []
    log.info(f"🔍 Caut dosare la {tribunal_nume} pentru {data_azi}...")

    try:
        # Pas 1: GET pagina principala pentru a obtine ViewState si tokens CSRF
        time.sleep(DELAY_SECUNDE)
        resp = SESSION.get(BASE_URL, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Extrage campurile hidden necesare pentru POST
        viewstate       = _get_hidden(soup, "__VIEWSTATE")
        viewstategenerator = _get_hidden(soup, "__VIEWSTATEGENERATOR")
        eventvalidation = _get_hidden(soup, "__EVENTVALIDATION")

        # Pas 2: POST cu parametrii de cautare
        time.sleep(DELAY_SECUNDE)
        payload = {
            "__VIEWSTATE":          viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION":    eventvalidation,
            "__EVENTTARGET":        "",
            "__EVENTARGUMENT":      "",
            "ctl00$ContentPlaceHolder1$txtDataDe":  data_azi,
            "ctl00$ContentPlaceHolder1$txtDataPana": data_azi,
            "ctl00$ContentPlaceHolder1$ddlMaterie":  "Insolvenţă",
            "ctl00$ContentPlaceHolder1$ddlInstanta": tribunal_nume,
            "ctl00$ContentPlaceHolder1$btnCautare":  "Caută",
        }
        resp2 = SESSION.post(BASE_URL, data=payload, timeout=30)
        resp2.raise_for_status()

        soup2 = BeautifulSoup(resp2.text, "html.parser")
        dosare = _parseaza_rezultate(soup2, tribunal_nume, data_azi)

    except requests.RequestException as e:
        log.error(f"❌ Eroare HTTP la {tribunal_nume}: {e}")
    except Exception as e:
        log.error(f"❌ Eroare neasteptata la {tribunal_nume}: {e}", exc_info=True)

    return dosare


def _get_hidden(soup: BeautifulSoup, name: str) -> str:
    tag = soup.find("input", {"name": name})
    return tag["value"] if tag else ""


def _parseaza_rezultate(soup: BeautifulSoup, tribunal: str, data_azi: str) -> list[dict]:
    """
    Parseaza tabelul de rezultate de pe portal.just.ro.
    NOTA: Selectoarele CSS pot necesita ajustare daca portalul isi schimba structura HTML.
    """
    dosare = []
    tabel = soup.find("table", {"id": lambda x: x and "GridView" in (x or "")})
    if not tabel:
        log.info(f"  Nu s-au gasit dosare noi la {tribunal}.")
        return dosare

    randuri = tabel.find_all("tr")[1:]  # skip header
    for rand in randuri:
        celule = rand.find_all("td")
        if len(celule) < 4:
            continue
        dosar = {
            "nr_dosar":       celule[0].get_text(strip=True),
            "debitor":        celule[1].get_text(strip=True),
            "nr_inregistrare": celule[2].get_text(strip=True),
            "tribunal":       tribunal,
            "data_inreg":     data_azi,
        }
        if dosar["nr_dosar"]:
            dosare.append(dosar)
            log.info(f"  📄 Dosar gasit: {dosar['nr_dosar']} — {dosar['debitor']}")

    return dosare


# ─── Completare PDF ──────────────────────────────────────────────────────────
OUTPUT_DIR.mkdir(exist_ok=True)


def completeaza_pdf(dosar: dict) -> Path:
    """
    Completeaza template-ul PDF cu datele dosarului prin overlay text.

    Coordonatele sunt detectate din template-ul real (Mătășel Adrian).
    PDF-ul foloseste sistem de coordonate cu originea in stanga-SUS (pymupdf),
    deci y creste in jos — valorile de mai jos sunt y-urile reale din PDF.

    Structura antet detectata:
      y≈137  TRIBUNALUL ...      (rand 1 — sectia/instanta)
      y≈160  SECȚIA A II A ...   (rand 2 — sectia)
      y≈184  Dosar nr. X         (rand 3 — numarul dosarului)
      y≈208  Debitor: X          (rand 4 — debitorul)
      y≈232  Nr. X din X         (rand 5 — dreapta, nr. inregistrare + data)

    NOTA: insert_text foloseste y ca baseline (linia de baza a textului).
    Adaugam ~10pt fata de y0 detectat pentru a pozitiona corect.
    """
    if not PDF_TEMPLATE.exists():
        raise FileNotFoundError(f"Template PDF nu gasit: {PDF_TEMPLATE}")

    output_path = OUTPUT_DIR / f"oferta_{dosar['nr_dosar'].replace('/', '-')}.pdf"

    doc  = pymupdf.open(str(PDF_TEMPLATE))
    page = doc[0]

    log.info("  📝 Completez antetul PDF cu datele dosarului...")

    # ── Sterge textul vechi din zona antetului variabil (randurile 1-5) ──────
    # Acoperim cu un dreptunghi alb peste textul existent inainte de a scrie
    zona_antet = pymupdf.Rect(70, 130, 530, 250)
    page.draw_rect(zona_antet, color=(1, 1, 1), fill=(1, 1, 1))

    # ── Scrie textul nou ─────────────────────────────────────────────────────
    # Format: (text, x, y_baseline, fontsize, bold)
    # Tribunal si sectia — bold, ca in original
    sectie = dosar.get("sectie", "SECȚIA A II A CIVILĂ")  # optional in dosar dict

    inserari = [
        # (text,                                    x,    y,     fontsize, bold)
        (f"TRIBUNALUL {dosar['tribunal'].upper()}", 72.0, 148.0, 10.5,    True),
        (sectie,                                    72.0, 171.5, 10.5,    True),
        (f"Dosar nr. {dosar['nr_dosar']}",          72.0, 195.5, 10.5,    False),
        (f"Debitor: {dosar['debitor']}",             72.0, 219.3, 10.5,    False),
        # Nr. inregistrare + data — aliniat dreapta (x≈414 din detectare)
        (f"Nr. {dosar['nr_inregistrare']} din {dosar['data_inreg']}", 414.0, 243.0, 10.5, False),
    ]

    for text, x, y, fontsize, bold in inserari:
        fontname = "helv-bold" if bold else "helv"
        try:
            page.insert_text(
                (x, y),
                text,
                fontsize=fontsize,
                fontname=fontname,
                color=(0, 0, 0),
            )
        except Exception as e:
            # helv-bold poate lipsi in unele versiuni pymupdf — fallback
            page.insert_text((x, y), text, fontsize=fontsize, fontname="helv", color=(0, 0, 0))
            log.warning(f"  ⚠ Font bold indisponibil, folosit helv: {e}")

    doc.save(str(output_path))
    doc.close()
    log.info(f"  ✅ PDF generat: {output_path}")
    return output_path


# ─── Trimitere email ─────────────────────────────────────────────────────────
def trimite_email(dosar: dict, pdf_path: Path, email_tribunal: str):
    """Trimite email cu PDF atasat catre tribunalul respectiv."""
    subiect = EMAIL_SUBIECT.format(
        nr_dosar=dosar["nr_dosar"],
        debitor=dosar["debitor"],
    )
    corp = EMAIL_CORP.format(
        nr_dosar=dosar["nr_dosar"],
        debitor=dosar["debitor"],
        tribunal=dosar["tribunal"],
        data=dosar["data_inreg"],
        expeditor=GMAIL_USER,
    )

    msg = MIMEMultipart()
    msg["From"]    = GMAIL_USER
    msg["To"]      = email_tribunal
    msg["Subject"] = subiect
    msg.attach(MIMEText(corp, "plain", "utf-8"))

    with open(pdf_path, "rb") as f:
        atasament = MIMEApplication(f.read(), _subtype="pdf")
        atasament.add_header(
            "Content-Disposition",
            "attachment",
            filename=pdf_path.name,
        )
        msg.attach(atasament)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.login(GMAIL_USER, GMAIL_PASSWORD)
            server.sendmail(GMAIL_USER, email_tribunal, msg.as_string())
        log.info(f"  📧 Email trimis la {email_tribunal} pentru {dosar['nr_dosar']}")
    except smtplib.SMTPException as e:
        log.error(f"  ❌ Eroare trimitere email: {e}")
        raise


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    log.info("=" * 60)
    log.info(f"🚀 Rulare monitor insolventa — {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    data_azi   = date.today().strftime("%d.%m.%Y")
    tribunale  = json.loads(TRIBUNALE_JSON)  # {"Tribunalul Cluj": "cluj@just.ro", ...}
    conn       = init_db()

    dosare_noi_total = 0

    for tribunal_nume, email_tribunal in tribunale.items():
        dosare_gasite = cauta_dosare_tribunal(tribunal_nume, data_azi)

        for dosar in dosare_gasite:
            if dosar_exista(conn, dosar["nr_dosar"]):
                log.info(f"  ⏭ Dosar deja procesat: {dosar['nr_dosar']}")
                continue

            log.info(f"  🆕 Dosar NOU: {dosar['nr_dosar']}")
            try:
                pdf_path = completeaza_pdf(dosar)
                trimite_email(dosar, pdf_path, email_tribunal)
                salveaza_dosar(conn, dosar)
                dosare_noi_total += 1
            except Exception as e:
                log.error(f"  ❌ Eroare procesare dosar {dosar['nr_dosar']}: {e}", exc_info=True)

        time.sleep(DELAY_SECUNDE)

    conn.close()
    log.info(f"✅ Terminat. Dosare noi procesate: {dosare_noi_total}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
