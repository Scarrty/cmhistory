# Fehlerbehebung

## `python`, `py` oder das virtuelle Environment wird nicht gefunden

```powershell
py --list
python --version
Test-Path ".\.venv\Scripts\python.exe"
```

Bei fehlendem Environment die Schritte unter [Installation](Installation) wiederholen. Alle
weiteren Befehle aus dem Installationsordner ausfuehren.

## `No module named cm_dashboard`

Das Paket ist nicht in diesem virtuellen Environment installiert:

```powershell
.\.venv\Scripts\python -m pip install --upgrade `
  ".\downloads\cm_dashboard-1.0.0-py3-none-any.whl"
```

## `unknown files` ist groesser als null

Der Quellordner enthaelt Dateien, deren Name oder Endung nicht zum Importvertrag passt.

1. Ausgabe von `inspect-source` lesen.
2. Browser-Kopien wie `(1)` entfernen.
3. Dokumente, Backups und Datenbanken aus dem Exportordner verschieben.
4. Nicht blind umbenennen; zuerst pruefen, ob es wirklich ein passender Cardmarket-Bericht ist.

## `source_file_changed` oder Hinweis auf geaenderte Quelldatei

Unter einem bereits importierten Pfad liegt ein anderer Inhalt. Ursache klaeren und danach den
Server stoppen, Backup erstellen und einen bewussten `rebuild` ausfuehren. Nicht weiter
inkrementell importieren.

## `Database contains facts from an older normalization version`

Die Softwareversion erwartet eine andere Normalisierung. Originalexporte beibehalten und:

```powershell
.\.venv\Scripts\python -m cm_dashboard.cli rebuild `
  --source ".\exports" --db ".\data\cardmarket.db"
```

## `import_failed`

Der konkrete Dateifehler steht in der CLI-Ausgabe und unter `/imports`.

- Datei laesst sich nicht lesen: erneut direkt von Cardmarket herunterladen.
- Pflichtspalte fehlt: Reporttyp und Dateiformat pruefen.
- Zeile besitzt mehr Werte als Header: Datei nicht manuell reparieren, sondern Quelle erneut
  exportieren.
- Einzelne defekte Datei aus dem Exportordner isolieren, Ursache klaeren und erneut importieren.

## `missing_period_coverage`

Mindestens ein erwarteter Gegenbericht fehlt. Dateiliste fuer Richtung, Ebene, Datumsbasis und
Zeitraum mit der Tabelle unter [Cardmarket-Exporte](Cardmarket-Exporte) vergleichen.

Nur eine dauerhaft fehlende und fachlich geklaerte historische Datei darf per
`accepted_issues.json` quittiert werden.

## `duplicate_article_source_overlap`

Gleiche Geschaeftszeilen wurden in parallelen Quellen gefunden, haeufig als CSV- und Excel-
Export desselben Berichts. Die normalisierte Auswertung zaehlt diese Zeilen einmal. Fuer neue
Monate nur ein Format je logischem Bericht speichern.

## `shipment_grouping_summary`

Informationsmeldung: Cardmarket-Sendungsdateien bestehen aus Shipment-Headern und eingerueckten
Fortsetzungszeilen. Die Anwendung hat diese gruppiert. Das ist allein kein Fehler.

## `orphan_shipment_row`

Eine Fortsetzungszeile steht vor einem Shipment-Header und konnte nicht zugeordnet werden. Die
betroffene Datei und Zeilennummer pruefen und den Bericht nach Moeglichkeit neu exportieren.

## Port 8000 ist belegt

Entweder den alten Dashboard-Prozess mit `Ctrl+C` beenden oder einen anderen Port verwenden:

```powershell
.\.venv\Scripts\python -m uvicorn cm_dashboard.web.app:app `
  --host 127.0.0.1 --port 8010 --no-access-log
```

## `Invalid host header`

Die App akzeptiert nur lokale Hostnamen. Direkt `http://127.0.0.1:8000/` oder
`http://localhost:8000/` verwenden. Kein Proxy und keine Netzwerkadresse verwenden.

## `database is locked`

Server und andere Importprozesse stoppen. Pruefen, ob ein Tabellenprogramm, SQLite-Browser,
Backup- oder Synchronisationsprogramm die Datei geoeffnet haelt. Danach den Befehl erneut
ausfuehren.

## Dashboard startet, zeigt aber keine Daten

```powershell
.\.venv\Scripts\python -m cm_dashboard.cli validate --db ".\data\cardmarket.db"
```

Dann pruefen:

- Start erfolgte im richtigen Arbeitsordner.
- `CM_DASHBOARD_DB` zeigt nicht auf eine andere Datenbank.
- Gewaehlte Datumsbasis und Filter decken vorhandene Exporte ab.
- `/imports` enthaelt importierte Dateien.

## Problem bleibt bestehen

Vor einem GitHub-Issue eine reproduzierbare Fehlerbeschreibung erstellen. Keine echten Exporte,
Datenbanken, Namen, Anschriften oder Bestellnummern hochladen. Geeignet sind:

- Software- und Python-Version
- ausgefuehrter Befehl
- vollstaendige Fehlermeldung nach Entfernung personenbezogener Werte
- synthetische Beispieldatei ohne Echtdaten
