# Monatlicher Import

Dieser Ablauf wird verwendet, sobald neue Cardmarket-Berichte vorliegen.

## Empfohlene Reihenfolge

### 1. Dashboard beenden

Im PowerShell-Fenster des Servers `Ctrl+C` druecken. Import und Webserver sollen nicht
gleichzeitig auf dieselbe SQLite-Datei zugreifen.

### 2. Datenbank sichern

```powershell
Set-Location "C:\CardmarketDashboard"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
Copy-Item ".\data\cardmarket.db" ".\data\cardmarket-$stamp.db"
```

### 3. Neue Cardmarket-Berichte exportieren

Den abgeschlossenen Monat wie unter [Cardmarket-Exporte](Cardmarket-Exporte) beschrieben
erzeugen. Pro logischem Bericht nur eine Excel- oder CSV-Datei ablegen.

### 4. Dateien in den Exportordner kopieren

Neue Dateien nach `C:\CardmarketDashboard\exports` kopieren. Bereits importierte Dateien nicht
umbenennen, ueberschreiben oder entfernen.

### 5. Quellen pruefen

```powershell
.\.venv\Scripts\python -m cm_dashboard.cli inspect-source `
  --source ".\exports"
```

Die Zahl der gueltigen Dateien muss um die Zahl der neuen Berichte steigen. Neue unbekannte
Dateien vor dem Import klaeren.

### 6. Inkrementell importieren

```powershell
.\.venv\Scripts\python -m cm_dashboard.cli import `
  --source ".\exports" `
  --db ".\data\cardmarket.db"
```

- Neue Dateien werden importiert.
- Unveraenderte, bereits bekannte Dateien werden anhand ihres Hashs uebersprungen.
- Eine fehlerhafte Datei wird zurueckgerollt; andere neue Dateien koennen trotzdem importiert
  werden.
- Ein gleicher Pfad mit geaendertem Inhalt wird als Konflikt behandelt und nicht still ersetzt.

### 7. Validieren

```powershell
.\.venv\Scripts\python -m cm_dashboard.cli validate `
  --db ".\data\cardmarket.db"
```

Neue Fehler und Warnungen mit dem vorherigen Monat vergleichen. Insbesondere die
Zeitraumabdeckung, Artikel-Sendungs-Verknuepfung und Summenabgleiche pruefen.

### 8. Dashboard starten

```powershell
.\.venv\Scripts\python -m uvicorn cm_dashboard.web.app:app `
  --host 127.0.0.1 --port 8000 --no-access-log
```

Unter `/imports`, `/shipments` und `/articles` eine Stichprobe fuer den neuen Monat ausfuehren.

## Wann ist ein Rebuild erforderlich?

Statt `import` muss `rebuild` verwendet werden, wenn:

- eine bereits importierte Datei unter gleichem Namen geaendert wurde,
- die Anwendung eine veraltete Normalisierungsversion meldet,
- historische Dateien bewusst korrigiert oder ergaenzt wurden,
- ein Release-Hinweis den Neuaufbau verlangt.

```powershell
.\.venv\Scripts\python -m cm_dashboard.cli rebuild `
  --source ".\exports" `
  --db ".\data\cardmarket.db"
```

Der Rebuild ist atomar. Trotzdem vor betrieblichen Aenderungen ein Backup behalten.

## Bekannte Abdeckungsluecken quittieren

Dauerhaft fehlende, fachlich geklaerte Zeitraeume koennen in `accepted_issues.json` neben der
Datenbank quittiert werden:

```json
{
  "accepted_coverage": [
    {
      "fingerprint": "missing_period_coverage|PURCHASED|ARTICLES|PURCHASEDATE|2024-06-01|2024-06-30",
      "note": "Dieser historische Bericht wurde nie erzeugt"
    }
  ]
}
```

Den Fingerprint liefert `validate`. Nur sicher geklaerte Luecken quittieren; Importfehler oder
Summenabweichungen niemals auf diese Weise ausblenden.
