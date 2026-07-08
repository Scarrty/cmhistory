# Cardmarket History Dashboard

Lokales Cardmarket Sales/Purchase Dashboard fuer die Exportdateien dieses Accounts.

Die Anwendung importiert Cardmarket XLS/CSV-Exporte, normalisiert Artikel und Shipments,
verknuepft zusammengehoerige Datensaetze ueber Order-IDs und stellt die Daten als
filterbares lokales Dashboard bereit.

## Status

Der MVP ist als lokales Python/FastAPI/SQLite-Projekt umgesetzt. Enthalten sind:

- Quellordner-Scan fuer Cardmarket XLS/CSV-Dateien
- Filename-Klassifizierung nach Richtung, Entitaet, Datumsbasis und Zeitraum
- Raw-Staging mit Datei- und Zeilenreferenz
- Normalisierung von Artikeln, Shipments, Events, Produkten, Labels, Sets und Kategorien
- Verknuepfung von Artikelzeilen mit Shipments ueber Order-ID
- Idempotenter Re-Import ohne doppelte normalisierte Fakten
- Validierungsreport fuer bekannte Datenqualitaets- und Abdeckungsprobleme
- Lokale Weboberflaeche mit Dashboard, Importstatus, Shipment-, Artikel- und Produktansichten
- CSV-Export fuer einfache Zeitraumreports

## Setup

```powershell
cd "D:\OneDrive\Dokumente\CM History"
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

## Import und Validierung

```powershell
.\.venv\Scripts\python -m cm_dashboard.cli inspect-source --source "D:\OneDrive\Dokumente\CM History"
.\.venv\Scripts\python -m cm_dashboard.cli import --source "D:\OneDrive\Dokumente\CM History" --db "data\cardmarket.db"
.\.venv\Scripts\python -m cm_dashboard.cli validate --db "data\cardmarket.db"
```

Der Import kann erneut ausgefuehrt werden, wenn neue Monatsdateien im Quellordner liegen.
Bereits importierte Dateien werden anhand Hash und Business Keys idempotent behandelt.

## Web App starten

```powershell
.\.venv\Scripts\python -m uvicorn cm_dashboard.web.app:app --reload
```

Danach lokal oeffnen:

- `http://127.0.0.1:8000/` fuer Dashboard und Monatsdiagramm
- `http://127.0.0.1:8000/imports` fuer Importdateien und Validierungsissues
- `http://127.0.0.1:8000/shipments` fuer Bestell-/Shipment-Suche
- `http://127.0.0.1:8000/articles` fuer Artikel- und Produktfilter
- `http://127.0.0.1:8000/reports/period.csv` fuer CSV-Reports mit Query-Filtern

## Monatliche Exporte

Neue Cardmarket-Exports werden direkt in den lokalen Quellordner gelegt. Danach:

1. `inspect-source` ausfuehren und pruefen, ob die Datei erkannt wurde.
2. `import` erneut ausfuehren.
3. `validate` ausfuehren und Warnungen pruefen.
4. Web App starten oder aktualisieren.

Details stehen in [docs/monthly_import.md](docs/monthly_import.md).

## Datenschutz

Cardmarket-Quelldateien enthalten private Account-, Handels- und personenbezogene Daten.
Sie werden nicht versioniert. Die `.gitignore` schliesst unter anderem aus:

- `*.XLS`, `*.xls`
- `*.XLSX`, `*.xlsx`
- `*.CSV`, `*.csv`
- `data/*.db`
- `.venv/`

Normale Listen- und Detailseiten maskieren Nutzernamen und zeigen keine Adress-, Namens-
oder VAT-Details an.

## Entwicklung pruefen

```powershell
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m ruff check src tests
```

Die umfangreichere lokale Vollpruefung wird mit dem MVP-Verifikationsskript gebuendelt.
