# Release 1.0.0

> **100 % AI-generated / Best Effort:** Alle Projektartefakte wurden mit KI-Systemen generiert.
> Keine Gewaehr; [vollstaendiger Hinweis](https://github.com/Scarrty/cmhistory/blob/v1.0.0/NOTICE.md).

Veroeffentlicht am **13. Juli 2026**.

## Einordnung

Version 1.0.0 ist die erste stabile Veroeffentlichung des lokalen Cardmarket History
Dashboards. Sie bildet den geprueften MVP fuer wiederholbare historische und monatliche
Cardmarket-Importe ab.

## Funktionsumfang

- Import von `.xls`, `.xlsx` und semikolongetrennten `.csv`
- Gekaufte und verkaufte Artikel sowie Sendungen
- Kauf- und Zahlungsdatum als getrennte Reporting-Sichten
- Rohdaten-Nachvollziehbarkeit und Quellenhashes
- Deduplizierung paralleler CSV-/Excel-Exporte
- Atomarer Neuaufbau und dateiweise atomarer Monatsimport
- Verknuepfung ueber Richtung und Bestellnummer
- Dashboard, Monatsdiagramm, Explorer, Details und CSV-Zeitraumreport
- Umfangreiche Filter, Pagination und Datenqualitaetspruefungen
- Maskierte Personendaten in der normalen Oberflaeche
- Sichtbarer 100-%-AI-generated- und Best-Effort-Hinweis
- MIT-Lizenz

## Upgrade von einer Vorabversion

Version 1.0.0 verwendet Normalisierungsversion 3. Eine bestehende Datenbank aus Version 0.1.0
oder einem frueheren Entwicklungsstand muss neu erzeugt werden:

```powershell
.\.venv\Scripts\python -m pip install --upgrade `
  ".\downloads\cm_dashboard-1.0.0-py3-none-any.whl"
.\.venv\Scripts\python -m cm_dashboard.cli rebuild `
  --source ".\exports" --db ".\data\cardmarket.db"
.\.venv\Scripts\python -m cm_dashboard.cli validate `
  --db ".\data\cardmarket.db"
```

Vorher Server stoppen und Datenbank, Originalexporte sowie `accepted_issues.json` sichern.

## Release-Artefakte

- `cm_dashboard-1.0.0-py3-none-any.whl`: empfohlene Installation
- `cm_dashboard-1.0.0.tar.gz`: Python-Quelldistribution
- `SHA256SUMS.txt`: SHA-256-Pruefsummen der beiden Paketartefakte
- automatisch von GitHub erzeugte Repository-Archive

Artefakte nur von der offiziellen
[Release-Seite](https://github.com/Scarrty/cmhistory/releases/tag/v1.0.0) beziehen.

## Verifikation

Vor der Veroeffentlichung werden ausgefuehrt:

- Ruff
- mypy
- pytest einschliesslich privater Vollbestandspruefungen
- `pip check`
- `pip-audit`
- sdist- und Wheel-Build
- Ressourcenpruefung des Wheels
- Quellinventar, vollstaendiger Datenbank-Rebuild und Validierung

## Bewusste Grenzen

Nicht enthalten sind Mehrbenutzerbetrieb, Hosting, Web-Uploads, automatische Backups,
Waehrungsumrechnung, Inventar/FIFO, Steuerreports und belastbare Einzelmargen.

Vollstaendige Aenderungshistorie: [CHANGELOG.md](https://github.com/Scarrty/cmhistory/blob/main/CHANGELOG.md)
