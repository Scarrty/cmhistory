# Betrieb und Konfiguration

## Dashboard starten

```powershell
Set-Location "C:\CardmarketDashboard"
.\.venv\Scripts\python -m uvicorn cm_dashboard.web.app:app `
  --host 127.0.0.1 `
  --port 8000 `
  --no-access-log
```

Browser: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

`--no-access-log` verhindert, dass Bestellnummern und Filterparameter in normalen
Zugriffslogs landen. Den Host nicht auf `0.0.0.0` aendern: Die Anwendung besitzt keine
Authentifizierung.

## Dashboard beenden

Im Serverfenster `Ctrl+C` druecken und warten, bis der Prozess beendet ist. Vor Import,
Rebuild, Backup oder Wiederherstellung immer zuerst den Server stoppen.

## Pfade

Explizite Parameter sind fuer wiederholbare Betriebsablaeufe empfohlen:

```powershell
.\.venv\Scripts\python -m cm_dashboard.cli import `
  --source "C:\CardmarketDashboard\exports" `
  --db "C:\CardmarketDashboard\data\cardmarket.db"
```

Alternativ stehen Umgebungsvariablen zur Verfuegung:

```powershell
$env:CM_DASHBOARD_SOURCE = "C:\CardmarketDashboard\exports"
$env:CM_DASHBOARD_DB = "C:\CardmarketDashboard\data\cardmarket.db"
```

Ohne Konfiguration gelten das aktuelle Arbeitsverzeichnis als Quellordner und
`data\cardmarket.db` darunter als Datenbankpfad.

## Anderen Port verwenden

Wenn Port 8000 belegt ist:

```powershell
.\.venv\Scripts\python -m uvicorn cm_dashboard.web.app:app `
  --host 127.0.0.1 --port 8010 --no-access-log
```

Danach `http://127.0.0.1:8010/` oeffnen.

## Upgrade auf eine neue Version

1. Server stoppen.
2. Datenbank und `accepted_issues.json` sichern.
3. Neues Wheel aus dem offiziellen Repository-Release herunterladen.
4. Paket aktualisieren:

```powershell
.\.venv\Scripts\python -m pip install --upgrade `
  ".\downloads\cm_dashboard-NEUE_VERSION-py3-none-any.whl"
```

5. Release-Hinweise lesen.
6. Wenn gefordert, Datenbank aus den Originalexporten mit `rebuild` neu aufbauen.
7. `validate` ausfuehren und Dashboard starten.

Version 1.0.0 verwendet Normalisierungsversion 3. Datenbanken aus Vorabversionen muessen neu
aufgebaut werden.

## OneDrive und Netzlaufwerke

SQLite sollte waehrend des Betriebs nicht gleichzeitig durch Synchronisationssoftware kopiert
oder konfliktaufgeloest werden. Fuer einen stabilen Dauerbetrieb `data` ausserhalb eines aktiv
synchronisierten OneDrive-Ordners ablegen. Exporte duerfen separat gesichert werden.

## Technische Grenzen

- Einzelplatzbetrieb
- Ein schreibender Importprozess zur Zeit
- Kein Web-Upload
- Keine Benutzer, Rollen oder Sessions
- Kein Hintergrunddienst oder Queue
- Keine automatische Sicherung
- Keine Cloud- oder Internetfreigabe
