import logging
from datetime import datetime

from config.settings import TRIBUNALS
from scripts.db import Database
from scripts.scraper import cauta_dosare
from scripts.pdf_generator import completeaza_pdf
from scripts.emailer import send_email


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def run():

    log = logging.getLogger("main")

    log.info("=== START INSOLVENTA SYSTEM ===")

    db = Database()

    today = datetime.now().strftime("%d.%m.%Y")

    total_new = 0

    # 🔥 TEST EMAIL AT START
    send_email(
        "SYSTEM START",
        "Sistemul de monitorizare a pornit cu succes."
    )

    for tribunal in TRIBUNALS:

        log.info(f"Checking: {tribunal}")

        dosare = cauta_dosare(tribunal, today)

        log.info(f"Found: {len(dosare)}")

        for d in dosare:

            if db.exists(d.case_uid):
                continue

            db.insert(d)

            pdf_path = completeaza_pdf(d)

            log.info(f"PDF generated: {pdf_path}")

            send_email(
                f"Dosar nou: {d.nr_dosar}",
                f"""
                Tribunal: {d.tribunal}
                Dosar: {d.nr_dosar}
                Debitor: {d.debitor}
                Nr inregistrare: {d.nr_inregistrare}
                """
            )

            total_new += 1

    log.info(f"TOTAL NEW DOSARE: {total_new}")
    log.info("=== FINISH ===")


if __name__ == "__main__":
    run()