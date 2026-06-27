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

    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    safe_name = dosar.nr_dosar.replace("/", "-")
    output_path = OUTPUT_DIR / f"{safe_name}.pdf"

    doc = None
    try:
        doc = fitz.open(str(PDF_TEMPLATE))
        page = doc[0]

        zona_antet = fitz.Rect(70, 130, 530, 250)
        page.draw_rect(
            zona_antet,
            color=(1, 1, 1),
            fill=(1, 1, 1),
        )

        tribunal = (dosar.tribunal or "").upper()
        debitor = dosar.debitor or "-"
        nr_dosar = dosar.nr_dosar or "-"
        nr_inreg = dosar.nr_inregistrare or "-"
        data = dosar.data_inreg or "-"

        inserari = [
            (tribunal.upper(), 72, 148, True),
            ("INSOLVENTA", 72, 171, True),
            (f"Dosar nr. {nr_dosar}", 72, 195, False),
            (f"Debitor: {debitor}", 72, 219, False),
            (f"Nr. {nr_inreg} din {data}", 414, 243, False),
        ]

        for text, x, y, bold in inserari:
            try:
                page.insert_text(
                    (x, y),
                    text,
                    fontsize=10.5,
                    fontname="Helvetica-Bold" if bold else "Helvetica",
                    color=(0, 0, 0),
                )
            except Exception as e:
                log.warning(f"Text insert failed: {text} -> {e}")

        doc.save(str(output_path))
        return output_path

    except Exception as e:
        raise PDFGenerationError(f"PDF generation failed: {e}")
    finally:
        if doc:
            doc.close()