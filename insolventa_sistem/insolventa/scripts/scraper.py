import time
import requests
from bs4 import BeautifulSoup
import certifi

from config.settings import BASE_URL, DELAY_SEC, MAX_RETRY
from scripts.models import Dosar


# =========================
# SESSION GLOBAL
# =========================

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


# =========================
# HELPERS
# =========================

def get_hidden(soup, name):
    tag = soup.find("input", {"name": name})
    return tag["value"] if tag else ""


# =========================
# MAIN SCRAPER
# =========================

def cauta_dosare(tribunal, data):

        # ─── TEST MODE ───
    from scripts.models import Dosar
    return [
        Dosar(
            case_uid=f"TEST-111-2026-{tribunal}",
            nr_dosar="111/30/2026",
            debitor="FIRMA TEST SRL",
            nr_inregistrare="42",
            tribunal=tribunal,
            data_inreg=data,
        )
    ]
    # ─── END TEST MODE ───

    for attempt in range(MAX_RETRY):

        try:
            print(f"[SCRAPER] {tribunal} attempt {attempt + 1}")

            time.sleep(DELAY_SEC)

            # -------------------------
            # GET PAGE (FIXED SSL)
            # -------------------------
            r = session.get(
                BASE_URL,
                timeout=30,
                verify=False  
            )

            r.raise_for_status()

            soup = BeautifulSoup(r.text, "html.parser")

            # -------------------------
            # BUILD PAYLOAD
            # -------------------------
            payload = {
                "__VIEWSTATE": get_hidden(soup, "__VIEWSTATE"),
                "__VIEWSTATEGENERATOR": get_hidden(soup, "__VIEWSTATEGENERATOR"),
                "__EVENTVALIDATION": get_hidden(soup, "__EVENTVALIDATION"),

                "ctl00$ContentPlaceHolder1$txtDataDe": data,
                "ctl00$ContentPlaceHolder1$txtDataPana": data,
                "ctl00$ContentPlaceHolder1$ddlMaterie": "Insolvenţă",
                "ctl00$ContentPlaceHolder1$ddlInstanta": tribunal,
                "ctl00$ContentPlaceHolder1$btnCautare": "Caută",
            }

            time.sleep(DELAY_SEC)

            # -------------------------
            # POST REQUEST
            # -------------------------
            r2 = session.post(
                BASE_URL,
                data=payload,
                timeout=30,
                verify=False   # 🔥 IMPORTANT ALSO HERE
            )

            r2.raise_for_status()

            return parse_results(r2.text, tribunal, data)

        except Exception as e:
            print(f"[ERROR] {tribunal}: {e}")
            time.sleep(3 * (attempt + 1))

    return []


# =========================
# PARSER
# =========================

def parse_results(html, tribunal, data):

    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", {"id": lambda x: x and "GridView" in x})

    if not table:
        print("[SCRAPER] No results table found")
        return []

    rows = table.find_all("tr")[1:]

    results = []

    for r in rows:

        cols = r.find_all("td")

        if len(cols) < 3:
            continue

        nr_dosar = cols[0].get_text(strip=True)
        debitor = cols[1].get_text(strip=True)
        nr_inreg = cols[2].get_text(strip=True)

        if not nr_dosar:
            continue

        results.append(
            Dosar(
                case_uid=f"{nr_dosar}-{tribunal}",
                nr_dosar=nr_dosar,
                debitor=debitor,
                nr_inregistrare=nr_inreg,
                tribunal=tribunal,
                data_inreg=data
            )
        )

    return results