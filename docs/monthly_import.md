# Monatlicher Importablauf

Diese Anleitung beschreibt den wiederkehrenden Import neuer Cardmarket-Exporte in die lokale
SQLite-Datenbank.

## 1. Vorbereiten

1. Webserver und laufende Importe beenden.
2. Neue Exporte direkt in den Quellordner legen.
3. Vorhandene historische Dateien nicht umbenennen oder ersetzen.

Unterstuetzte Dateitypen: `.xls`, `.xlsx` und semikolongetrennte `.csv`.

Unterstuetzte Exportfamilien:

- `PURCHASED ARTICLES-BY...`
- `PURCHASED SHIPMENTS-BY...`
- `SOLD ARTICLES-BY...`
- `SOLD SHIPMENTS-BY...`

Der Dateiname muss Richtung, Ebene, Datumsbasis und Zeitraum enthalten, zum Beispiel:

```text
SOLD ARTICLES-BYPAYMENTDATE-2026-08-01_2026-08-31.XLSX
PURCHASED SHIPMENTS-BYPAYMENTDATE-2026-08-01_2026-08-31.XLS
```

## 2. Dateien erkennen

```powershell
cd "D:\OneDrive\Dokumente\CM History"
.\.venv\Scripts\python -m cm_dashboard.cli inspect-source --source "."
```

Pruefen:

- Die Gesamtzahl steigt um die erwarteten neuen Dateien.
- Keine neue Datei erscheint unter `unknown files`.
- Richtung, Datumsbasis und Zeitraum im Dateinamen stimmen fachlich.

## 3. Inkrementell importieren

```powershell
.\.venv\Scripts\python -m cm_dashboard.cli import --source "." --db "data\cardmarket.db"
```

Die Ausgabe unterscheidet:

- `imported files`: neue, erfolgreich normalisierte Dateien
- `skipped files`: bekannte Dateien mit identischem Hash
- `failed files`: isoliert zurueckgerollte Dateien mit gespeichertem Fehlerhinweis

Der Befehl liefert einen Fehlercode, wenn mindestens eine Datei fehlschlaegt. Andere gueltige
Dateien werden trotzdem verarbeitet. Ein Dateiimport wird entweder mit Roh- und Faktdaten
vollstaendig abgeschlossen oder vollstaendig zurueckgerollt.

## 4. Sonderfall: vorhandene Datei geaendert

Wird unter einem bereits importierten Pfad ein anderer Dateiinhalt gefunden, stoppt die
Anwendung die stille Wiederverwendung und markiert einen Konflikt. Nicht weiter inkrementell
importieren. Zuerst klaeren, warum sich die historische Quelle geaendert hat; danach bewusst:

```powershell
.\.venv\Scripts\python -m cm_dashboard.cli rebuild --source "." --db "data\cardmarket.db"
```

Der Neuaufbau schreibt in eine temporaere DB und ersetzt `cardmarket.db` erst nach erfolgreichem
Import aller Dateien sowie bestandener SQLite- und Foreign-Key-Pruefung. Eine funktionierende
Alt-DB bleibt bei einem Fehler erhalten.

## 5. Validieren

```powershell
.\.venv\Scripts\python -m cm_dashboard.cli validate --db "data\cardmarket.db"
```

Danach `/imports` pruefen. Erwartbare Informations- oder Warnhinweise koennen sein:

- `duplicate_article_source_overlap`: parallele CSV/XLS-Quellen wurden dedupliziert
- `shipment_grouping_summary`: Shipment-Fortsetzungen wurden ihrem Header zugeordnet
- `missing_period_coverage`: Gegenexport oder Zeitraumabdeckung fehlt
- `missing_shipment_event_date`: ein konkretes Shipmentdatum fehlt in der Quelle

Nicht akzeptieren:

- `import_failed`
- `source_file_changed` ohne geklaerte Ursache
- unbekannte Header oder Pflichtfelder
- neue Mengen-/Wert- oder Shipment-Summenabweichungen
- SQLite-Integritaets- oder Foreign-Key-Fehler

## 6. Fachliche Stichprobe

In der Weboberflaeche mindestens pruefen:

1. `/imports`: neue Datei hat Status `Importiert`.
2. `/shipments`: eine neue Order ist in der richtigen Richtung vorhanden.
3. Sendungsdetail: Kosten, Ereignisse und Artikelpositionen sind verknuepft.
4. `/articles`: Artikeltext, Produkt-ID, Set, Kategorie, Menge und Betrag stimmen.
5. Dashboard: gewaehlter Monat und Datumsbasis liefern plausible Werte.
6. CSV-Report: derselbe Zeitraum und dieselbe Datumsbasis stimmen mit dem Dashboard ueberein.

`PAYMENTDATE` ist der aktuelle Reporting-Standard. Ein Vergleich mit `PURCHASEDATE` ist sinnvoll,
aber beide Sichten duerfen nicht addiert werden, weil sie dieselben Geschaeftspositionen abbilden.

## 7. Dashboard starten

```powershell
.\.venv\Scripts\python -m uvicorn cm_dashboard.web.app:app `
  --host 127.0.0.1 --port 8000 --no-access-log
```

Nur lokal an `127.0.0.1` binden. Der MVP besitzt keine Authentifizierung.
