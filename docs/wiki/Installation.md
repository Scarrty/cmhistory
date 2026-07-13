# Installation

## Systemanforderungen

- Windows 10 oder 11 fuer die hier dokumentierten PowerShell-Befehle
- Python 3.12 oder neuer, 64 Bit empfohlen
- Etwa 500 MB freier Speicher zusaetzlich zu den Exporten
- Lokaler Browser
- Keine Datenbank, kein Docker und kein Cardmarket-API-Zugang erforderlich

## Empfohlene Ordnerstruktur

```text
C:\CardmarketDashboard\
|-- .venv\
|-- downloads\
|-- exports\
`-- data\
```

`exports` enthaelt ausschliesslich Cardmarket-Dateien. `data` enthaelt die erzeugte
SQLite-Datenbank. Diese Trennung verhindert, dass Build-Artefakte oder Dokumente als Quellen
gescannt werden.

## Installation unter Windows aus dem Release

1. Python von [python.org](https://www.python.org/downloads/windows/) installieren. Bei der
   Installation **Add Python to PATH** aktivieren.
2. Unter [Releases](https://github.com/Scarrty/cmhistory/releases/latest) die Datei
   `cm_dashboard-1.0.0-py3-none-any.whl` und `SHA256SUMS.txt` herunterladen.
3. PowerShell oeffnen und ausfuehren:

```powershell
New-Item -ItemType Directory -Path "C:\CardmarketDashboard" -Force
New-Item -ItemType Directory -Path "C:\CardmarketDashboard\downloads" -Force
New-Item -ItemType Directory -Path "C:\CardmarketDashboard\exports" -Force
New-Item -ItemType Directory -Path "C:\CardmarketDashboard\data" -Force
Move-Item "$HOME\Downloads\cm_dashboard-1.0.0-py3-none-any.whl" `
  "C:\CardmarketDashboard\downloads\"
Set-Location "C:\CardmarketDashboard"
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install `
  ".\downloads\cm_dashboard-1.0.0-py3-none-any.whl"
```

Vor der Installation kann der Download mit der im Release veroeffentlichten Pruefsumme
verglichen werden:

```powershell
Get-FileHash `
  ".\downloads\cm_dashboard-1.0.0-py3-none-any.whl" `
  -Algorithm SHA256
Get-Content ".\downloads\SHA256SUMS.txt"
```

Der Hash des Wheels muss exakt der entsprechenden Zeile in `SHA256SUMS.txt` entsprechen.

Wenn `py -3.12` nicht gefunden wird, zuerst pruefen:

```powershell
py --list
python --version
```

Bei einer installierten neueren Python-Version kann stattdessen `python -m venv .venv`
verwendet werden.

## Installation aus dem Repository

Diese Variante ist fuer Entwicklung oder einen exakt reproduzierbaren Quellstand gedacht:

```powershell
git clone https://github.com/Scarrty/cmhistory.git "C:\CardmarketDashboard\source"
Set-Location "C:\CardmarketDashboard\source"
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

Private Cardmarket-Exporte niemals in das geklonte Repository committen.

## Optional: macOS oder Linux

Die Anwendung ist plattformunabhaengig, der vollstaendige Projektlauf wird primaer unter
Windows gepflegt. Die entsprechenden Shell-Befehle lauten:

```bash
mkdir -p "$HOME/CardmarketDashboard/exports" "$HOME/CardmarketDashboard/data"
cd "$HOME/CardmarketDashboard"
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install ./cm_dashboard-1.0.0-py3-none-any.whl
```

## Installation pruefen

```powershell
Set-Location "C:\CardmarketDashboard"
.\.venv\Scripts\python -c "import cm_dashboard; print(cm_dashboard.__version__)"
.\.venv\Scripts\python -m cm_dashboard.cli --help
```

Erwartet wird Version `1.0.0` und eine Liste der Befehle `inspect-source`, `import`, `rebuild`
und `validate`.

Weiter: [Erster Datenbankaufbau](Erster-Datenbankaufbau).
