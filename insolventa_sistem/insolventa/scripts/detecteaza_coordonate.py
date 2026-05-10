"""
Detectează coordonatele textului din template.pdf.

Scop:
- identifică pozițiile textelor variabile,
- verifică dacă PDF-ul are AcroForm fields,
- ajută la calibrarea overlay-ului.

Utilizare:
    python scripts/detecteaza_coordonate.py templates/template.pdf
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz


OUTPUT_JSON = Path("debug/pdf_coordinates.json")


def detecteaza_text_si_coordonate(
    pdf_path: str,
):
    pdf_file = Path(pdf_path)

    if not pdf_file.exists():
        print(f"❌ PDF inexistent: {pdf_file}")
        sys.exit(1)

    try:
        doc = fitz.open(pdf_file)

    except Exception as e:
        print(f"❌ Nu pot deschide PDF-ul: {e}")
        sys.exit(1)

    try:
        pagina = doc[0]

        print(f"\n📄 Prima pagina din: {pdf_file}")
        print(f"📐 Dimensiuni pagina: {pagina.rect}\n")

        blocks = pagina.get_text("dict")["blocks"]

        rezultate = []

        print("─" * 110)
        print(
            f"{'TEXT':<50}"
            f"{'x0':>8}"
            f"{'y0':>8}"
            f"{'x1':>8}"
            f"{'y1':>8}"
        )
        print("─" * 110)

        for block in blocks:
            if block.get("type") != 0:
                continue

            for line in block.get("lines", []):
                for span in line.get("spans", []):

                    text = span.get("text", "").strip()

                    if not text:
                        continue

                    # Elimină zgomot foarte mic
                    if len(text) <= 1:
                        continue

                    x0, y0, x1, y1 = span["bbox"]

                    rezultat = {
                        "text": text,
                        "x0": round(x0, 2),
                        "y0": round(y0, 2),
                        "x1": round(x1, 2),
                        "y1": round(y1, 2),
                        "font": span.get("font"),
                        "size": span.get("size"),
                    }

                    rezultate.append(rezultat)

                    print(
                        f"{text[:48]:<50}"
                        f"{x0:>8.1f}"
                        f"{y0:>8.1f}"
                        f"{x1:>8.1f}"
                        f"{y1:>8.1f}"
                    )

        print("─" * 110)

        # ---------------------------------------------------------
        # Salvează coordonatele în JSON
        # ---------------------------------------------------------
        OUTPUT_JSON.parent.mkdir(
            exist_ok=True,
        )

        with open(
            OUTPUT_JSON,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                rezultate,
                f,
                ensure_ascii=False,
                indent=2,
            )

        print(f"\n💾 Coordonate salvate în: {OUTPUT_JSON}")

        # ---------------------------------------------------------
        # Detectare AcroForm
        # ---------------------------------------------------------
        fields = {}

        try:
            fields = doc.get_fields()

        except AttributeError:
            try:
                fields = {
                    w.field_name: {}
                    for p in doc
                    for w in p.widgets()
                    if w.field_name
                }

            except Exception:
                fields = {}

        if fields:
            print(
                f"\n✅ PDF are {len(fields)} câmpuri formular (AcroForm):"
            )

            for name, info in fields.items():
                print(
                    f"   - '{name}' "
                    f"(tip: {info.get('type', '?')})"
                )

            print("\n➡ Recomandare:")
            print("   Folosește completare AcroForm.")
            print("   Evită overlay text.")

        else:
            print(
                "\n⚠️ PDF-ul NU are câmpuri formular."
            )

            print("\n➡ Recomandare:")
            print("   Folosește overlay text.")
            print("   Calibrează coordonatele din pdf_generator.py")

    finally:
        doc.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "\nUtilizare:"
        )
        print(
            "python scripts/detecteaza_coordonate.py templates/template.pdf"
        )
        sys.exit(1)

    detecteaza_text_si_coordonate(
        sys.argv[1]
    )