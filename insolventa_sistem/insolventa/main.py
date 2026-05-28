import logging
from datetime import datetime

from config.settings import TRIBUNALS
from scripts.db import Database
from scripts.scraper import cauta_dosare
from scripts.pdf_generator import completeaza_pdf
from scripts.emailer import send_email
from scripts.validator import valideaza_dosar, ValidationError
from scripts.logger import setup_logging


setup_logging()

import time

def run():
    log = logging.getLogger("main")
    log.info("=== START INSOLVENTA SYSTEM ===")

    db = Database()
    today = datetime.now().strftime("%d.%m.%Y")
    total_new = 0

    for tribunal, email_tribunal in TRIBUNALS.items():
        log.info(f"Checking: {tribunal}")

        dosare = cauta_dosare(tribunal, today)
        log.info(f"Found: {len(dosare)}")

        for d in dosare:
            if db.exists(d.case_uid):
                log.info(f"Deja procesat: {d.nr_dosar}")
                continue

            try:
                valideaza_dosar(d)
            except ValidationError as e:
                log.warning(f"Dosar invalid, skip: {e}")
                continue

            db.insert(d)

            try:
                pdf_path = completeaza_pdf(d)
                log.info(f"PDF generat: {pdf_path}")
            except Exception as e:
                log.error(f"PDF error pentru {d.nr_dosar}: {e}")
                continue

            try:
                send_email(
                    to=email_tribunal,
                    subject=f"Oferta lichidator – Dosar {d.nr_dosar} – {d.debitor}",
                    body=(
                        f"Tribunal: {d.tribunal}\n"
                        f"Dosar: {d.nr_dosar}\n"
                        f"Debitor: {d.debitor}\n"
                        f"Nr. inregistrare: {d.nr_inregistrare}\n"
                        f"Data: {d.data_inreg}\n"
                    ),
                    pdf_path=pdf_path,
                )
                time.sleep(2)
            except Exception as e:
                log.error(f"Email error pentru {d.nr_dosar}: {e}")

            total_new += 1

    db.close()
    log.info(f"TOTAL NEW DOSARE: {total_new}")
    log.info("=== FINISH ===")


if __name__ == "__main__":
    run()