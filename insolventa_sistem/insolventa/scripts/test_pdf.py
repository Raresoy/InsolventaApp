import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
from pdf_renderer import PDFRenderer

DOSAR_TEST = {
    "nr_dosar": "123/111/2026",
    "debitor": "FIRMA TEST SRL",
    "nr_inregistrare": "42",
    "data_inreg": "07.05.2026",
}

print("🧪 Rulez test PDF...")

renderer = PDFRenderer("templates/template.pdf")

OUTPUT = Path("output/test_output.pdf")

output = renderer.render(DOSAR_TEST, str(OUTPUT))

print("✅ PDF generat:", output)