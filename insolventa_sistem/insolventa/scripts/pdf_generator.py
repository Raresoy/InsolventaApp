import logging
from pathlib import Path

import fitz

from config.settings import PDF_TEMPLATE, OUTPUT_DIR

log = logging.getLogger(__name__)


class PDFGenerationError(Exception):
    pass



def completeaza_pdf(dosar):
    if not PDF_TEMPLATE.exists():
        raise PDFGenerationError("Template PDF lipsa")

    output_path = OUTPUT_DIR / f"{dosar.nr_dosar.replace('/', '-')}.pdf"

    doc = fitz.open(str(PDF_TEMPLATE))

    page = doc[0]

    zona_antet = fitz.Rect(70, 130, 530, 250)

    page.draw_rect(
        zona_antet,
        color=(1, 1, 1),
        fill=(1, 1, 1),
    )

    inserari = [
        (f"TRIBUNALUL {dosar.tribunal.upper()}", 72, 148, True),
        (dosar.sectie, 72, 171, True),
        (f"Dosar nr. {dosar.nr_dosar}", 72, 195, False),
        (f"Debitor: {dosar.debitor}", 72, 219, False),
        (
            f"Nr. {dosar.nr_inregistrare} din {dosar.data_inreg}",
            414,
            243,
            False,
        ),
    ]

    for text, x, y, bold in inserari:
        page.insert_text(
            (x, y),
            text,
            fontsize=10.5,
            fontname="helv-bold" if bold else "helv",
            color=(0, 0, 0),
        )

    doc.save(str(output_path))
    doc.close()

    return output_path
