# Monthly Import Workflow

Diese Anleitung beschreibt, wie neue monatliche Cardmarket-Exports lokal hinzugefuegt,
importiert und geprueft werden.

## 1. Dateien ablegen

Lege neue Cardmarket-Dateien direkt in den Quellordner:

```text
D:\OneDrive\Dokumente\CM History
```

Unterstuetzt werden die bestehenden Exportfamilien:

- `PURCHASED ARTICLES-BY...`
- `PURCHASED SHIPMENTS-BY...`
- `SOLD ARTICLES-BY...`
- `SOLD SHIPMENTS-BY...`

Die Dateinamen muessen Richtung, Entitaet, Datumsbasis und Zeitraum enthalten, zum Beispiel:

```text
SOLD ARTICLES-BYPURCHASEDATE-2026-08-01_2026-08-31.XLS
PURCHASED SHIPMENTS-BYPAYMENTDATE-2026-08-01_2026-08-31.XLS
```

## 2. Quelle pruefen

```powershell
cd "D:\OneDrive\Dokumente\CM History"
.\.venv\Scripts\python -m cm_dashboard.cli inspect-source --source "D:\OneDrive\Dokumente\CM History"
```

Erwartung:

- Die neuen Dateien erscheinen in der Zahl der gueltigen Dateien.
- Unerkannte Dateien werden als Warnung ausgegeben.
- Private XLS/CSV-Dateien bleiben unversioniert.

## 3. Import erneut ausfuehren

```powershell
.\.venv\Scripts\python -m cm_dashboard.cli import --source "D:\OneDrive\Dokumente\CM History" --db "data\cardmarket.db"
```

Der Import ist fuer Wiederholungen gedacht. Bereits bekannte Dateien und normalisierte
Business Keys sollen keine doppelten Artikel-, Shipment- oder Produktdaten erzeugen.

## 4. Validierung ausfuehren

```powershell
.\.venv\Scripts\python -m cm_dashboard.cli validate --db "data\cardmarket.db"
```

Typische nicht-kritische Hinweise:

- Fehlende Monatsabdeckung, wenn es fuer eine Datumsbasis oder Richtung keine passende
  Gegen-Datei gibt.
- Hinweise zu gruppierten Shipment-Zeilen, weil Cardmarket Shipment-Exports Header- und
  Fortsetzungszeilen enthalten.
- Warnungen zu doppelten Artikel-Business-Keys, wenn CSV und XLS dieselben Geschaeftsdaten
  liefern.
- Unverknuepfte Artikel-Orders, wenn ein Artikel-Export existiert, aber kein passender
  Shipment-Export im Datenbestand liegt.

Kritisch waeren Parserfehler, unbekannte Spaltenfamilien, nicht erkannte Dateinamen oder
neue Pflichtfelder, die nicht normalisiert werden koennen.

## 5. Dashboard oeffnen

```powershell
.\.venv\Scripts\python -m uvicorn cm_dashboard.web.app:app --reload
```

Danach `http://127.0.0.1:8000/` oeffnen.

Wichtige Seiten:

- `/imports`: pruefen, ob die neuen Dateien importiert wurden und ob Warnungen vorliegen.
- `/shipments`: Bestellungen nach Zeitraum, Richtung, Datumsbasis, Username, Land oder Order-ID filtern.
- `/articles`: Artikel nach Produkt-ID, Artikeltext, Expansion, Kategorie, Richtung und Zeitraum filtern.
- `/reports/period.csv`: Zeitraumreport als CSV herunterladen. Query-Filter wie
  `start_date`, `end_date`, `direction`, `date_basis`, `product_id`, `expansion` und
  `category` koennen direkt angehaengt werden.

Beispiel:

```text
http://127.0.0.1:8000/reports/period.csv?start_date=2026-08-01&end_date=2026-08-31&direction=SOLD
```
