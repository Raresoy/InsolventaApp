from pathlib import Path
import json
import fitz  # pymupdf


class PDFRenderer:
    def __init__(self, template_path: str, coords_path: str = None):
        self.template_path = Path(template_path)
        self.coords = None

        # optional coords json (compatibil cu viitorul)
        if coords_path and Path(coords_path).exists():
            with open(coords_path, "r", encoding="utf-8") as f:
                self.coords = json.load(f)

    def render(self, dosar: dict, output_path: str):
        doc = fitz.open(str(self.template_path))
        page = doc[0]

        print("▶ PDF RENDER START")

        # fallback coords (SAFE DEFAULT dacă JSON nu e folosit)
        inserari = [
            (f"Dosar nr. {dosar['nr_dosar']}", 72, 182),
            (f"Debitor: {dosar['debitor']}", 72, 206),
            (f"Nr. {dosar['nr_inregistrare']} din {dosar['data_inreg']}", 414, 230),
        ]

        # dacă ai coords.json, îl poți activa aici ulterior
        if self.coords:
            print("ℹ Using coords.json (optional mode)")

        for text, x, y in inserari:
            print("✍ writing:", text)

            page.insert_text(
                (x, y),
                text,
                fontsize=10.5,
                fontname="helv",   # SAFE FONT (NU CRAPA)
                color=(0, 0, 0),
            )

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        doc.save(str(out))
        doc.close()

        print("▶ PDF RENDER DONE:", out)

        return out