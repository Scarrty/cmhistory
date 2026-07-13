# Erster Datenbankaufbau

## 1. Exporte ablegen

Alle Originaldateien in den vorbereiteten Ordner kopieren:

```text
C:\CardmarketDashboard\exports
```

Unterstuetzt werden `.xls`, `.xlsx` und semikolongetrennte `.csv`. Die Dateinamen muessen dem
unter [Cardmarket-Exporte](Cardmarket-Exporte) beschriebenen Schema entsprechen.

## 2. Quellen inventarisieren

```powershell
Set-Location "C:\CardmarketDashboard"
.\.venv\Scripts\python -m cm_dashboard.cli inspect-source `
  --source ".\exports"
```

Die Ausgabe zeigt:

- `valid files`: erkannte Cardmarket-Dateien
- `unknown files`: nicht zum Vertrag passende Dateien
- Anzahl je Dateityp

Vor dem Aufbau muss `unknown files: 0` gelten. Unbekannte Dateien entfernen oder ihren
Ursprung und Namen klaeren; nicht blind umbenennen.

## 3. Datenbank atomar aufbauen

```powershell
.\.venv\Scripts\python -m cm_dashboard.cli rebuild `
  --source ".\exports" `
  --db ".\data\cardmarket.db"
```

Der Befehl:

1. erstellt eine temporaere SQLite-Datenbank,
2. liest jede Quelldatei,
3. bewahrt Rohzeilen und Quellenbezug auf,
4. normalisiert Artikel, Produkte, Sendungen und Ereignisse,
5. verknuepft Artikel und Sendungen ueber Richtung und Bestellnummer,
6. prueft SQLite-Integritaet und Fremdschluessel,
7. ersetzt die Zieldatenbank erst nach vollstaendigem Erfolg.

Bei einem Fehler bleibt eine bereits vorhandene funktionierende Datenbank erhalten. Die
Quelldateien werden nie veraendert.

## 4. Bestand validieren

```powershell
.\.venv\Scripts\python -m cm_dashboard.cli validate `
  --db ".\data\cardmarket.db"
```

Die Validierung unterscheidet `error`, `warning` und `info`:

- `error`: vor dem Betrieb beheben
- `warning`: Datenabdeckung oder fachliche Auffaelligkeit pruefen
- `info`: dokumentierte Normalisierung oder Gruppierung

Typische Hinweise:

| Code | Bedeutung |
|---|---|
| `missing_period_coverage` | Erwarteter Gegenbericht oder Zeitraum fehlt |
| `duplicate_article_source_overlap` | Gleiche Artikelzeilen lagen in mehreren Formaten vor und wurden einmal gezaehlt |
| `shipment_grouping_summary` | Shipment-Header und Fortsetzungszeilen wurden gruppiert |
| `missing_shipment_event_date` | Quelle enthaelt kein verwertbares Ereignisdatum |
| `orphan_shipment_row` | Fortsetzungszeile steht vor jedem Shipment-Header |

Warnungen bedeuten nicht automatisch Datenverlust. Die genaue Behandlung steht unter
[Fehlerbehebung](Fehlerbehebung).

## 5. Dashboard starten

```powershell
.\.venv\Scripts\python -m uvicorn cm_dashboard.web.app:app `
  --host 127.0.0.1 `
  --port 8000 `
  --no-access-log
```

Danach [http://127.0.0.1:8000/](http://127.0.0.1:8000/) oeffnen. Das PowerShell-Fenster muss
geoeffnet bleiben. Beenden mit `Ctrl+C`.

## 6. Fachliche Stichprobe

Nach dem ersten Aufbau mindestens pruefen:

1. `/imports` zeigt alle Dateien als importiert.
2. Ein bekannter Monat liefert plausible Kauf- und Verkaufswerte.
3. Eine bekannte Bestellnummer ist unter `/shipments` vorhanden.
4. Das Sendungsdetail zeigt verknuepfte Artikel.
5. Artikel-, Set- und Produktfilter liefern erwartete Treffer.
6. Der CSV-Zeitraumreport laesst sich erzeugen.

Weiter: [Dashboard und Reports](Dashboard-und-Reports).
