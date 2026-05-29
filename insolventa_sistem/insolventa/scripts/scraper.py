import time
import requests
import urllib3
from bs4 import BeautifulSoup

from config.settings import DELAY_SEC, MAX_RETRY
from scripts.models import Dosar

urllib3.disable_warnings()

TRIBUNALE_ID = {
    "Tribunalul Bihor":           111,
    "Tribunalul Satu Mare":       83,
    "Tribunalul Arad":            108,
    "Tribunalul Timis":           30,
    "Tribunalul Bistrita-Nasaud": 112,
    "Tribunalul Cluj":            117,
    "Tribunalul Maramures":       100,
    "Tribunalul Salaj":           84,
    "Tribunalul Sibiu":           85,
    "Tribunalul Harghita":        96,
    "Tribunalul Mures":           102,
    "Tribunalul Neamt":           103,
}

SESSION = requests.Session()
SESSION.verify = False
SESSION.headers.update({"User-Agent": "Mozilla/5.0"})


def get_debitor(id_dosar, id_inst):
    """Intră pe pagina individuală a dosarului și extrage numele debitorului."""
    try:
        url = f"https://portal.just.ro/{id_inst}/SitePages/Dosar.aspx?id_dosar={id_dosar}&id_inst={id_inst}"
        time.sleep(DELAY_SEC)
        r = SESSION.get(url, verify=False, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")

        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) >= 2:
                calitate = cols[1].get_text(strip=True).lower()
                if calitate == "debitor":
                    nume = cols[0].get_text(strip=True)
                    if nume:
                        return nume

    except Exception as e:
        print(f"[SCRAPER] get_debitor error: {e}")

    return "-"


def cauta_dosare(tribunal, data):
    id_inst = TRIBUNALE_ID.get(tribunal)

    if not id_inst:
        print(f"[SCRAPER] ID necunoscut pentru: {tribunal}")
        return []

    url = f"https://portal.just.ro/{id_inst}/SitePages/dosare.aspx?id_inst={id_inst}"

    for attempt in range(MAX_RETRY):
        try:
            print(f"[SCRAPER] {tribunal} (id={id_inst}) attempt {attempt + 1}")
            time.sleep(DELAY_SEC)

            r = SESSION.get(url, verify=False, timeout=30)
            r.raise_for_status()

            return parse_results(r.text, tribunal, data, id_inst)

        except Exception as e:
            print(f"[ERROR] {tribunal}: {e}")
            time.sleep(3 * (attempt + 1))

    return []


def parse_results(html, tribunal, data_azi, id_inst):
    soup = BeautifulSoup(html, "html.parser")

    table = None
    for t in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in t.find_all("th")]
        if "Număr" in headers and "Materie juridică" in headers:
            table = t
            break

    if not table:
        print(f"[SCRAPER] Tabel negasit pentru {tribunal}")
        return []

    results = []

    for row in table.find_all("tr")[1:]:
        cols = row.find_all("td")
        if len(cols) < 4:
            continue

        # extrage link si id_dosar
        a_tag = cols[0].find("a")
        if not a_tag:
            continue

        nr_dosar   = a_tag.get_text(strip=True)
        href       = a_tag.get("href", "")
        data_inreg = cols[1].get_text(strip=True)
        materie    = cols[3].get_text(strip=True)

        if not nr_dosar:
            continue

        # Filtru 1: doar dosarele de azi
        if data_inreg != data_azi:
            continue

        # Filtru 2: doar insolventa/faliment
        if not any(x in materie.lower() for x in ["insolv", "faliment"]):
            continue

        # extrage id_dosar din href: Dosar.aspx?id_dosar=XXX&id_inst=YYY
        id_dosar = None
        if "id_dosar=" in href:
            try:
                id_dosar = href.split("id_dosar=")[1].split("&")[0]
            except Exception:
                pass

        # extrage debitorul real de pe pagina individuala
        debitor = "-"
        if id_dosar:
            debitor = get_debitor(id_dosar, id_inst)
            print(f"[SCRAPER] Debitor extras: {debitor}")

        results.append(
            Dosar(
                case_uid=f"{nr_dosar}-{tribunal}",
                nr_dosar=nr_dosar,
                debitor=debitor,
                nr_inregistrare="-",
                tribunal=tribunal,
                data_inreg=data_inreg,
            )
        )

    print(f"[SCRAPER] {tribunal}: {len(results)} dosare insolventa azi")
    return results