"""
Script ajutator: detecteaza coordonatele textului din antetul PDF-ului template.
Ruleaza o singura data local pentru a afla unde sa inserezi datele dosarului.

Utilizare:
    pip install pymupdf
    python scripts/detecteaza_coordonate.py template.pdf
"""

import sys
import pymupdf


def detecteaza_text_si_coordonate(pdf_path: str):
    doc = pymupdf.open(pdf_path)
    pagina = doc[0]

    print(f"\n📄 Prima pagina din: {pdf_path}")
    print(f"   Dimensiuni pagina: {pagina.rect}\n")

    # Listeaza toate blocurile de text cu pozitiile lor
    blocks = pagina.get_text("dict")["blocks"]
    print("─" * 70)
    print(f"{'TEXT':<40} {'x0':>6} {'y0':>6} {'x1':>6} {'y1':>6}")
    print("─" * 70)

    for block in blocks:
        if block.get("type") != 0:  # 0 = text
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span["text"].strip()
                if text:
                    r = span["bbox"]  # (x0, y0, x1, y1)
                    print(f"{text[:39]:<40} {r[0]:>6.1f} {r[1]:>6.1f} {r[2]:>6.1f} {r[3]:>6.1f}")

    print("─" * 70)

    # Verifica daca are campuri AcroForm (API difera intre versiuni pymupdf)
    try:
        fields = doc.get_fields()           # pymupdf < 1.23
    except AttributeError:
        try:
            fields = {w.field_name: {} for p in doc for w in p.widgets() if w.field_name}
        except Exception:
            fields = {}
    if fields:
        print(f"\n✅ PDF are {len(fields)} campuri de formular (AcroForm):")
        for name, info in fields.items():
            print(f"   - '{name}' (tip: {info.get('type', '?')})")
        print("\n→ Foloseste Varianta A (AcroForm) in monitor.py")
        print("  Actualizeaza 'campuri_mapate' cu numele campurilor de mai sus.")
    else:
        print("\n⚠️  PDF-ul NU are campuri de formular. Se va folosi overlay text.")
        print("→ Foloseste Varianta B in monitor.py")
        print("  Actualizeaza coordonatele x,y din 'inserari' cu valorile de mai sus.")

    doc.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Utilizare: python detecteaza_coordonate.py template.pdf")
        sys.exit(1)
    detecteaza_text_si_coordonate(sys.argv[1])
