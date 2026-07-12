# Cardmarket History Dashboard

Lokales Sales/Purchase-Dashboard fuer historische und kuenftige Cardmarket-Exporte.
Die Anwendung liest XLS, XLSX und CSV, bewahrt Rohzeilen mit Quellenbezug auf, normalisiert
Artikel und Sendungen und verknuepft beide Ebenen ueber `direction + order_id`.

## Funktionsumfang

- Wiederholbarer Ordnerimport mit Hash-Pruefung, Datei-Savepoints und Fehlerfortsetzung
- Atomarer Neuaufbau der SQLite-Datenbank ohne Austausch einer funktionierenden Alt-DB bei Fehlern
- Deduplizierung paralleler CSV/XLS-Exporte bei Erhalt echter identischer Mehrfachpositionen
- Sendungen, Kauf-/Zahlungsevents, Artikel, Produkte, Bezeichnungen, Sets und Kategorien
- Datenqualitaetspruefungen fuer Abdeckung, Verknuepfung und Summenabgleich
- Deutsches, responsives Dashboard mit Monatsdiagramm und maskierten Personendaten
- Serverseitige Pagination sowie Filter fuer Zeitraum, Richtung, Artikel, Produkt, Set,
  Kategorie, Handelspartner, Land, Waehrung, Betrag, Menge, Kommentar, Import und Verknuepfung
- CSV-Zeitraumreport mit denselben Reporting-Filtern

Die technische Struktur und die Datenfluesse stehen in
[docs/architecture.md](docs/architecture.md). Der fachliche Quellenbefund steht in
[Datenmodell.md](Datenmodell.md).

## Voraussetzungen

- Stabiles Python 3.12 oder neuer
- PowerShell fuer die dokumentierten Windows-Befehle
- Cardmarket-Exporte mit den vorhandenen Dateinamens- und Spaltenfamilien

Die Anwendung arbeitet lokal. Sie benoetigt keine Cardmarket-API und uebertraegt keine
Quelldaten an externe Dienste.

## Installation

```powershell
cd "D:\OneDrive\Dokumente\CM History"
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

## Erster Datenbankaufbau

```powershell
.\.venv\Scripts\python -m cm_dashboard.cli inspect-source --source "."
.\.venv\Scripts\python -m cm_dashboard.cli rebuild --source "." --db "data\cardmarket.db"
.\.venv\Scripts\python -m cm_dashboard.cli validate --db "data\cardmarket.db"
```

`rebuild` importiert in eine temporaere Datenbank, prueft SQLite-Integritaet und Foreign Keys
und ersetzt die Zieldatenbank erst nach vollstaendigem Erfolg.

## Monatlicher Import

Neue Exportdateien werden in den Quellordner gelegt. Danach:

```powershell
.\.venv\Scripts\python -m cm_dashboard.cli inspect-source --source "."
.\.venv\Scripts\python -m cm_dashboard.cli import --source "." --db "data\cardmarket.db"
.\.venv\Scripts\python -m cm_dashboard.cli validate --db "data\cardmarket.db"
```

Unveraenderte Dateien werden uebersprungen. Eine bereits importierte Datei mit gleichem Pfad,
aber anderem Inhalt wird nicht still mit alten Fakten vermischt; sie erfordert einen bewussten
`rebuild`. Einzelne defekte neue Dateien werden als fehlgeschlagen gespeichert, waehrend der
Rest des Ordners weiter importiert wird. Details stehen in
[docs/monthly_import.md](docs/monthly_import.md).

## Weboberflaeche

```powershell
.\.venv\Scripts\python -m uvicorn cm_dashboard.web.app:app `
  --host 127.0.0.1 --port 8000 --no-access-log
```

Der Standard-Datenbankpfad ist `data\cardmarket.db` im aktuellen Arbeitsverzeichnis. Ein
anderer Pfad wird ueber die Umgebungsvariable `CM_DASHBOARD_DB` gesetzt; fuer die
CLI-Befehle gilt zusaetzlich `CM_DASHBOARD_SOURCE` fuer den Quellordner. Explizite
`--source`/`--db`-Argumente haben Vorrang vor den Umgebungsvariablen.

Danach lokal oeffnen:

- `http://127.0.0.1:8000/` - Kennzahlen, Filter und Monatsdiagramm
- `http://127.0.0.1:8000/imports` - alle Importdateien und Validierungshinweise
- `http://127.0.0.1:8000/shipments` - Sendungsexplorer und Details
- `http://127.0.0.1:8000/articles` - Artikelexplorer und Produktdetails
- `http://127.0.0.1:8000/reports/period.csv` - gefilterter Zeitraumreport

Die App lehnt unbekannte Host-Header ab und ist fuer `127.0.0.1` ausgelegt. Sie besitzt keine
Authentifizierung und darf deshalb nicht an `0.0.0.0` oder ins Internet gebunden werden.

## Reporting-Semantik

- `PAYMENTDATE` ist die sichtbare Standard-Datumsbasis, weil sie im aktuellen Artikelbestand
  alle bekannten Sendungen abdeckt. `PURCHASEDATE` kann explizit gewaehlt werden.
- Kauf- und Zahlungsansicht werden nie unbemerkt addiert; das wuerde dieselben physischen
  Artikelpositionen doppelt zaehlen.
- Betrag bedeutet im Artikelexplorer `article_lines.total`, im Sendungsexplorer
  `shipments.total_value`.
- Werte werden nicht zwischen Waehrungen umgerechnet. Vor einer kuenftigen Nutzung mehrerer
  Waehrungen muss ein fachliches Umrechnungsmodell festgelegt werden.
- Der CSV-Report ist eine Artikelwert-/Monatsaggregation. Er ist kein Steuer-, Gewinn- oder
  Inventarreport.
- Die Spalte `total` im CSV-Report ist ein Bruttovolumen (Kauf- plus Verkaufssummen der
  gefilterten Zeilen), keine Saldo- oder Gewinngroesse. Kauf- und Verkaufssummen stehen
  getrennt in `purchase_total` und `sales_total`. Die Spalte `net_total` ist der Saldo
  (Verkaeufe minus Kaeufe); in Monatszeilen ist sie je Richtung vorzeichenbehaftet
  (Verkaeufe positiv, Kaeufe negativ). Auch `net_total` ist keine Gewinngroesse, weil
  Gebuehren, Versand und Bestandsveraenderungen nicht enthalten sind.

## Validierung verstehen

`validate` berechnet abgeleitete Hinweise neu. Die Importseite bewahrt zusaetzlich konkrete
Dateifehler und fehlende Shipment-Events auf. Typische Codes:

- `missing_period_coverage`: eine erwartete Gegen-Datei oder Monatsabdeckung fehlt
- `duplicate_article_source_overlap`: dieselben Geschaeftszeilen liegen in CSV und XLS vor und
  wurden nur einmal normalisiert
- `shipment_grouping_summary`: Shipment-Header und Fortsetzungszeilen wurden gruppiert
- `missing_shipment_event_date`: ein Shipment-Export enthaelt kein verwertbares Eventdatum

Warnungen sind zu pruefen, aber nicht automatisch Datenverlust. Fehler beim Lesen,
Normalisieren oder bei geaenderten Quelldateien erfordern eine Korrektur bzw. einen Neuaufbau.

Bekannte, dauerhafte Abdeckungsluecken (Exporte, die nie existiert haben) koennen quittiert
werden, damit sie das Validierungsergebnis nicht dauerhaft verrauschen: `validate` gibt fuer
jede `missing_period_coverage`-Warnung einen `fingerprint` aus. Dieser wird in die Datei
`accepted_issues.json` neben der Datenbank eingetragen:

```json
{
  "accepted_coverage": [
    {
      "fingerprint": "missing_period_coverage|PURCHASED|ARTICLES|PURCHASEDATE|2024-06-01|2024-06-30",
      "note": "Export wurde 2024 nie erzeugt"
    }
  ]
}
```

Quittierte Luecken werden ausgeblendet und als eine Info-Zeile
(`accepted_period_coverage_summary`) zusammengefasst. Die Datei ist unabhaengig von der
Datenbank und ueberlebt einen `rebuild`; neue, nicht quittierte Luecken erscheinen weiterhin.

## Entwicklung und Verifikation

```powershell
.\.venv\Scripts\python -m ruff check src tests scripts
.\.venv\Scripts\python -m mypy
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m pip check
.\.venv\Scripts\python -m pip_audit
.\.venv\Scripts\python -m build
.\.venv\Scripts\python scripts\verify_distribution.py --dist dist
```

Die vollstaendige lokale Pruefung inklusive aller privaten Quelldateien und frischem
Datenbankaufbau startet mit:

```powershell
.\scripts\verify_mvp.ps1
```

GitHub Actions fuehrt fuer Python 3.12 Linting, Typpruefung, Tests, Dependency-Audit und
Distributionspruefung ohne Zugriff auf private Exporte aus. Tests, die den privaten
Vollbestand voraussetzen, laufen nur mit `CM_DASHBOARD_RUN_FULL_SOURCE_TESTS=1` und werden
sonst uebersprungen.

## Datenschutz und Betrieb

- XLS/XLSX/CSV, SQLite-Datenbanken, Logs, virtuelle Umgebungen und Build-Ausgaben sind ignoriert.
- Normale Seiten maskieren Benutzernamen und Namen und lesen keine Adress- oder VAT-Felder aus.
- Access-Logs sind fuer den normalen Start deaktiviert, damit Order-IDs und Filter nicht in
  lokalen Logdateien landen.
- Das aktuelle Repository enthaelt keine bekannten konkreten Quelldatenwerte. Aeltere Git-Historie
  kann vor der Redigierung eingecheckte Fragmente enthalten; eine Historienumschreibung erfordert
  eine separate, koordinierte Entscheidung.
- SQLite und gleichzeitige OneDrive-Synchronisierung koennen Dateisperren oder Konfliktkopien
  erzeugen. Import und Webserver nicht parallel betreiben; fuer dauerhaften Betrieb sollte die
  aktive DB ausserhalb eines synchronisierten Ordners liegen.

## Bewusste MVP-Grenzen

Nicht enthalten sind Web-Uploads, asynchrone Jobs, Mehrbenutzerbetrieb, Rollen, Hosting,
automatische Backups, PDF/Excel-Reports, Steuerlogik, FIFO/Inventar und belastbare Einzelmargen.
Weitere fachlich offene Punkte stehen im
[Projekt-Audit](OUTPUT/PROJECT_AUDIT_AND_OPTIMIZATION.md).

## Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).
