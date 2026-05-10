import logging
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from config.settings import (
    BASE_URL,
    DELAY_SECUNDE,
    LOG_DIR,
    MAX_RETRY,
)

from scripts.models import Dosar

log = logging.getLogger(__name__)

SESSION = requests.Session()

SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }
)


class ScraperError(Exception):
    pass


def cauta_dosare(
    tribunal_nume: str,
    data_azi: str,
) -> list[Dosar]:
    """
    Caută dosare pe portal.just.ro pentru tribunalul dat.
    """

    for attempt in range(MAX_RETRY):
        try:
            log.info(
                f"🔍 Caut dosare pentru {tribunal_nume} "
                f"(attempt {attempt + 1})"
            )

            # ---------------------------------------------------------
            # 1. GET pagina principală
            # ---------------------------------------------------------
            time.sleep(DELAY_SECUNDE)

            resp = SESSION.get(
                BASE_URL,
                timeout=30,
            )

            resp.raise_for_status()

            soup = BeautifulSoup(
                resp.text,
                "html.parser",
            )

            # ---------------------------------------------------------
            # 2. Extrage hidden fields ASP.NET
            # ---------------------------------------------------------
            payload = {
                "__VIEWSTATE": _get_hidden(
                    soup,
                    "__VIEWSTATE",
                ),
                "__VIEWSTATEGENERATOR": _get_hidden(
                    soup,
                    "__VIEWSTATEGENERATOR",
                ),
                "__EVENTVALIDATION": _get_hidden(
                    soup,
                    "__EVENTVALIDATION",
                ),
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "ctl00$ContentPlaceHolder1$txtDataDe": data_azi,
                "ctl00$ContentPlaceHolder1$txtDataPana": data_azi,
                "ctl00$ContentPlaceHolder1$ddlMaterie": "Insolvenţă",
                "ctl00$ContentPlaceHolder1$ddlInstanta": tribunal_nume,
                "ctl00$ContentPlaceHolder1$btnCautare": "Caută",
            }

            # ---------------------------------------------------------
            # 3. POST căutare
            # ---------------------------------------------------------
            time.sleep(DELAY_SECUNDE)

            resp2 = SESSION.post(
                BASE_URL,
                data=payload,
                timeout=30,
            )

            resp2.raise_for_status()

            # ---------------------------------------------------------
            # 4. Validare răspuns
            # ---------------------------------------------------------
            if "Dosar" not in resp2.text and "dosar" not in resp2.text:
                raise ScraperError(
                    "Portalul a returnat răspuns invalid"
                )

            # ---------------------------------------------------------
            # 5. Parse rezultate
            # ---------------------------------------------------------
            rezultate = parseaza_rezultate(
                resp2.text,
                tribunal_nume,
                data_azi,
            )

            log.info(
                f"✅ {len(rezultate)} dosare găsite "
                f"pentru {tribunal_nume}"
            )

            return rezultate

        except Exception as e:
            log.error(
                f"❌ Eroare scraping "
                f"{tribunal_nume} "
                f"(attempt {attempt + 1}): {e}"
            )

            _save_failed_html(
                tribunal_nume,
                attempt,
                locals().get("resp2"),
            )

            time.sleep(5 * (attempt + 1))

    raise ScraperError(
        f"Nu s-a putut interoga portalul pentru {tribunal_nume}"
    )


def parseaza_rezultate(
    html: str,
    tribunal: str,
    data_azi: str,
) -> list[Dosar]:
    """
    Parsează rezultatele din HTML.
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    # ---------------------------------------------------------
    # Caută tabelul relevant
    # ---------------------------------------------------------
    tabel = soup.find(
        "table",
        {
            "id": lambda x: x and "GridView" in x
        },
    )

    if not tabel:
        log.warning(
            f"⚠ Nu s-a găsit tabel rezultate pentru {tribunal}"
        )
        return []

    rows = tabel.find_all("tr")

    if len(rows) <= 1:
        return []

    rezultate = []

    # ---------------------------------------------------------
    # Parse fiecare rând
    # ---------------------------------------------------------
    for row in rows[1:]:
        cols = row.find_all("td")

        if len(cols) < 3:
            continue

        try:
            nr_dosar = cols[0].get_text(
                strip=True
            )

            debitor = cols[1].get_text(
                strip=True
            )

            nr_inregistrare = cols[2].get_text(
                strip=True
            )

            # Curățare text
            nr_dosar = " ".join(
                nr_dosar.split()
            )

            debitor = " ".join(
                debitor.split()
            )

            nr_inregistrare = " ".join(
                nr_inregistrare.split()
            )

            if not nr_dosar:
                continue

            dosar = Dosar(
                nr_dosar=nr_dosar,
                debitor=debitor,
                nr_inregistrare=nr_inregistrare,
                tribunal=tribunal,
                data_inreg=data_azi,
            )

            rezultate.append(dosar)

            log.info(
                f"📄 Dosar găsit: "
                f"{dosar.nr_dosar} "
                f"- {dosar.debitor}"
            )

        except Exception as e:
            log.error(
                f"❌ Eroare parsare rând: {e}"
            )

    return rezultate


def _get_hidden(
    soup: BeautifulSoup,
    name: str,
) -> str:
    """
    Extrage câmp hidden ASP.NET.
    """

    tag = soup.find(
        "input",
        {"name": name},
    )

    if not tag:
        raise ScraperError(
            f"Hidden field lipsă: {name}"
        )

    return tag.get("value", "")


def _save_failed_html(
    tribunal: str,
    attempt: int,
    response,
):
    """
    Salvează HTML-ul când scrapingul eșuează.
    """

    try:
        if not response:
            return

        filename = (
            LOG_DIR
            / f"failed_{tribunal}_{attempt}.html"
        )

        with open(
            filename,
            "w",
            encoding="utf-8",
        ) as f:
            f.write(response.text)

    except Exception as e:
        log.error(
            f"Nu am putut salva HTML debug: {e}"
        )