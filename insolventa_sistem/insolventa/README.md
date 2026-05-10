# Sistem Automat Monitorizare Dosare Insolvență

Sistem care verifică automat portal.just.ro, completează oferta PDF și trimite email la tribunal.
**Cost lunar: 0 EUR. Rulează singur, fără intervenție.**

---

## Cuprins

1. [Configurare inițială (o singură dată)](#1-configurare-initiala)
2. [Cum adaptezi PDF-ul template](#2-cum-adaptezi-pdf-ul-template)
3. [Cum adaugi un tribunal nou](#3-cum-adaugi-un-tribunal-nou)
4. [Cum modifici textul emailului](#4-cum-modifici-textul-emailului)
5. [Verificare că totul funcționează](#5-verificare-ca-totul-functioneaza)
6. [Ce să faci dacă nu funcționează](#6-ce-sa-faci-daca-nu-functioneaza)

---

## 1. Configurare inițială

### Ce ai nevoie pregătit:
- [ ] Cont Gmail dedicat (ex: `oferte.lichidator@gmail.com`)
- [ ] Cont GitHub (gratuit, de pe github.com)
- [ ] Template-ul PDF al ofertei

### Pași de urmat (o singură dată):

#### A. Activează App Password în Gmail

1. Intră în contul Gmail dedicat
2. Du-te la **Contul meu Google** → **Securitate**
3. Activează **Verificarea în doi pași** (dacă nu e activată)
4. Caută **Parole pentru aplicații** și creează una nouă
5. Notează parola generată (16 caractere, ex: `abcd efgh ijkl mnop`)

#### B. Creează repository-ul GitHub

1. Intră pe [github.com](https://github.com) → **New repository**
2. Nume: `monitor-insolventa` | Bifează **Private** | Apasă **Create**
3. Încarcă toate fișierele din acest proiect în repository
4. Pune fișierul `template.pdf` în folderul rădăcină al repository-ului

#### C. Adaugă secretele în GitHub

1. În repository, du-te la **Settings** → **Secrets and variables** → **Actions**
2. Apasă **New repository secret** și adaugă fiecare secret de mai jos:

| Nume secret | Ce conține | Exemplu |
|-------------|-----------|---------|
| `GMAIL_USER` | Adresa Gmail | `oferte.lichidator@gmail.com` |
| `GMAIL_PASSWORD` | App Password Gmail | `abcd efgh ijkl mnop` |
| `TRIBUNALE_JSON` | Tribunalele și emailurile lor | vezi mai jos |
| `EMAIL_SUBIECT` | Subiectul emailului | `Oferta lichidator – Dosar {nr_dosar}` |
| `EMAIL_CORP` | Textul emailului | textul tău standard |

**Formatul pentru TRIBUNALE_JSON** (copiază și modifică):
```json
{
  "Tribunalul Cluj": "registratura.cluj@just.ro",
  "Tribunalul Bucuresti": "registratura.bucuresti@just.ro"
}
```

**Formatul pentru EMAIL_CORP** (variabilele `{...}` se completează automat):
```
Stimate Grefier,

Va transmitem alaturat oferta de lichidator judiciar pentru dosarul {nr_dosar},
debitor {debitor}, inregistrat la {tribunal} pe data de {data}.

Cu stima,
Cabinet Lichidator
```

#### D. Testează manual prima rulare

1. În repository, du-te la **Actions** → **Monitor Insolventa**
2. Apasă **Run workflow** → **Run workflow**
3. Urmărește progresul — dacă apare bifa verde ✅, totul funcționează

---

## 2. Cum adaptezi PDF-ul template

**Când:** Când primești template-ul de la client sau când îl înlocuiești cu unul nou.

### Pasul 1 — Detectează tipul PDF-ului

Pe calculatorul tău local, rulează:
```bash
pip install pymupdf
python scripts/detecteaza_coordonate.py template.pdf
```

Scriptul îți va spune:
- **Dacă PDF-ul are câmpuri de formular:** afișează numele câmpurilor (ex: `nr_dosar`, `debitor`)
- **Dacă PDF-ul este text static:** afișează coordonatele textului din antet

### Pasul 2A — PDF cu câmpuri de formular

Deschide `scripts/monitor.py` și găsește secțiunea:
```python
campuri_mapate = {
    "nr_dosar":        dosar["nr_dosar"],
    "debitor":         dosar["debitor"],
    ...
}
```
Înlocuiește cheile (stânga) cu **numele exacte ale câmpurilor** din scriptul de detectare.

### Pasul 2B — PDF text static

Găsește în `scripts/monitor.py` secțiunea:
```python
inserari = [
    (dosar["nr_dosar"],        170, 720),
    (dosar["debitor"],         170, 700),
    ...
]
```
Înlocuiește valorile `170, 720` cu **coordonatele x, y** afișate de scriptul de detectare.

### Pasul 3 — Încarcă noul template

Înlocuiește fișierul `template.pdf` din repository cu noul fișier PDF.

---

## 3. Cum adaugi un tribunal nou

1. Du-te în repository → **Settings** → **Secrets and variables** → **Actions**
2. Apasă pe secretul **`TRIBUNALE_JSON`** → **Update secret**
3. Adaugă tribunalul nou în lista JSON:

```json
{
  "Tribunalul Cluj": "registratura.cluj@just.ro",
  "Tribunalul Bucuresti": "registratura.bucuresti@just.ro",
  "Tribunalul Timis": "registratura.timis@just.ro"
}
```
4. Apasă **Update secret** — gata, sistemul va monitoriza și noul tribunal la următoarea rulare.

---

## 4. Cum modifici textul emailului

### Subiectul emailului:
1. **Settings** → **Secrets** → apasă pe `EMAIL_SUBIECT` → **Update secret**
2. Modifică textul. Variabilele disponibile: `{nr_dosar}`, `{debitor}`

### Corpul emailului:
1. **Settings** → **Secrets** → apasă pe `EMAIL_CORP` → **Update secret**
2. Modifică textul. Variabilele disponibile:
   - `{nr_dosar}` — numărul dosarului (ex: `1234/30/2025`)
   - `{debitor}` — numele firmei/persoanei
   - `{tribunal}` — instanța (ex: `Tribunalul Cluj`)
   - `{data}` — data înregistrării
   - `{expeditor}` — adresa ta de Gmail

---

## 5. Verificare că totul funcționează

### Verificare zilnică (automată — nu trebuie să faci nimic)
Sistemul rulează singur. Poți verifica în orice moment:
1. Du-te în repository → **Actions**
2. Rulările apar în listă cu ✅ (succes) sau ❌ (eroare)

### Verificare log-uri
1. Apasă pe o rulare → caută **Artifacts** în jos
2. Descarcă `log-[număr]` pentru a vedea ce s-a întâmplat

### Verificare baza de date
1. Descarcă `dosare-db` din Artifacts
2. Fișierul `dosare.db` poate fi deschis cu [DB Browser for SQLite](https://sqlitebrowser.org/) (gratuit)

---

## 6. Ce să faci dacă nu funcționează

### ❌ Rularea apare cu X roșu în Actions

1. Apasă pe rularea eșuată → apasă pe **monitor**
2. Citește mesajul de eroare roșu

**Erori comune:**

| Eroare | Cauza | Soluție |
|--------|-------|---------|
| `Authentication failed` | App Password greșit | Regenerează App Password în Gmail și actualizează secretul |
| `FileNotFoundError: template.pdf` | PDF-ul lipsește din repository | Încarcă `template.pdf` în rădăcina repository-ului |
| `JSONDecodeError` | Format greșit TRIBUNALE_JSON | Verifică că JSON-ul are ghilimele drepte `"` nu „curbe" |
| `Connection timeout` | portal.just.ro nu răspunde | Normal ocazional — va reuși la următoarea rulare |

### ❌ Emailurile nu ajung la tribunal

1. Verifică în Gmail (folderul **Trimise**) dacă emailul a fost trimis
2. Dacă da — problema e la adresa tribunalului. Verifică `TRIBUNALE_JSON`
3. Dacă nu — verifică log-ul pentru mesajul de eroare exact

### ❌ PDF-ul completat are datele în locul greșit

Rulează din nou `scripts/detecteaza_coordonate.py` pe template-ul tău și actualizează coordonatele în `monitor.py`. Vezi [Secțiunea 2](#2-cum-adaptezi-pdf-ul-template).

### ❌ Nu mai găsește dosare (deși există pe portal)

portal.just.ro poate să-și schimbe structura HTML. Contactează freelancerul care a implementat sistemul pentru actualizarea scraper-ului.

---

## Structura fișierelor

```
monitor-insolventa/
├── template.pdf                    ← Oferta ta PDF (furnizata de tine)
├── requirements.txt                ← Librarii Python necesare
├── scripts/
│   ├── monitor.py                  ← Scriptul principal
│   └── detecteaza_coordonate.py   ← Script ajutator pentru setup PDF
├── .github/
│   └── workflows/
│       └── monitor.yml             ← Configurare GitHub Actions
└── README.md                       ← Acest ghid
```

---

*Sistem implementat pentru monitorizare automată dosare insolvență — portal.just.ro*
