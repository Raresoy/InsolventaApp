"""
Script de test local — verifica completarea PDF fara a accesa portal.just.ro.
Genereaza un PDF de proba cu date fictive.

Utilizare:
    pip install -r requirements.txt
    python scripts/test_pdf.py template.pdf

Rezultat: output_pdfs/oferta_TEST-123-111-2026.pdf
Deschide fisierul si verifica ca datele apar corect in antet.
"""

import sys
import os
from pathlib import Path

# Simuleaza un dosar real
DOSAR_TEST = {
    "nr_dosar":        "123/111/2026",
    "debitor":         "FIRMA TEST S.R.L.",
    "nr_inregistrare": "42",
    "tribunal":        "Bihor",
    "sectie":          "SECȚIA A II A CIVILĂ",
    "data_inreg":      "07.05.2026",
}

# Adauga folderul parinte in path pentru a importa monitor.py
sys.path.insert(0, str(Path(__file__).parent))

# Seteaza variabile de mediu minime ca sa nu crape importul
os.environ.setdefault("GMAIL_USER",     "test@test.com")
os.environ.setdefault("GMAIL_PASSWORD", "test")
os.environ.setdefault("TRIBUNALE_JSON", '{"Tribunalul Bihor": "bihor@just.ro"}')

from monitor import completeaza_pdf, PDF_TEMPLATE, OUTPUT_DIR

if __name__ == "__main__":
    if len(sys.argv) > 1:
        import monitor
        monitor.PDF_TEMPLATE = Path(sys.argv[1])

    if not PDF_TEMPLATE.exists() and len(sys.argv) < 2:
        print(f"❌ Nu gasesc template.pdf. Ruleaza din folderul radacina:")
        print(f"   python scripts/test_pdf.py template.pdf")
        sys.exit(1)

    print(f"🧪 Test completare PDF cu dosar fictiv:")
    for k, v in DOSAR_TEST.items():
        print(f"   {k}: {v}")
    print()

    try:
        output = completeaza_pdf(DOSAR_TEST)
        print(f"\n✅ SUCCESS! PDF generat: {output}")
        print(f"   Deschide fisierul si verifica ca datele sunt in pozitia corecta.")
        print(f"   Daca pozitia e gresita, ajusteaza coordonatele x,y din monitor.py")
    except Exception as e:
        print(f"\n❌ EROARE: {e}")
        import traceback
        traceback.print_exc()
