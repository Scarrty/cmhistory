# Cardmarket History Dashboard

Planungs- und Analyse-Repository fuer ein lokales Cardmarket Sales/Purchase Dashboard.

Ziel ist eine schlanke Webanwendung, die Cardmarket-Exportdateien importiert, normalisiert, zusammengehoerige Artikel- und Shipment-Datensaetze korrekt verknuepft und als filterbares Sales/Purchase Dashboard auswertbar macht.

## Status

Dieses Repository enthaelt aktuell noch keine Implementierung. Es enthaelt die fachliche Vorarbeit fuer den spaeteren MVP:

- Datenmodell aus den vorhandenen Cardmarket-Exporten
- Product Requirements Document
- kritische PRD-Feasibility-Review
- konkreter MVP-Implementierungsplan

## Wichtige Dokumente

| Datei | Zweck |
|---|---|
| `Datenmodell.md` | Strukturierte Interpretation der Cardmarket-Quelldaten und Zielmodell. |
| `PRD_Cardmarket_Dashboard.md` | Produktanforderungen fuer das Dashboard. |
| `OUTPUT/PRD_FEASIBILITY_REVIEW.md` | Kritische Pruefung des PRD gegen Datenmodell und XLS/CSV-Quellen. |
| `OUTPUT/MVP_IMPLEMENTATION_PLAN.md` | Schrittweiser, testbarer Umsetzungsplan fuer den MVP. |

## Datenbasis

Die Analyse basiert auf lokalen Cardmarket-Exporten im Arbeitsordner:

- alte Excel-Dateien (`.XLS`)
- CSV-Dateien (`.CSV`)
- Zeitraum laut Analyse: 2016-04-01 bis 2026-07-06
- 447 analysierte Quelldateien
- 21.172 gelesene Datenzeilen

Die Quelldateien enthalten private Account-, Handels- und teilweise personenbezogene Daten. Sie werden bewusst nicht versioniert.

## Datenschutz und Repository-Regeln

Die Datei `.gitignore` schliesst Cardmarket-Exportdateien aus:

- `*.XLS`
- `*.xls`
- `*.XLSX`
- `*.xlsx`
- `*.CSV`
- `*.csv`

Dadurch sollen private Cardmarket-Quelldaten nicht versehentlich auf GitHub gelangen. Im Repository sollen nur Dokumentation, Quellcode, Tests und nicht-sensitive Beispiel-/Fixture-Dateien liegen.

## Geplanter MVP

Der MVP soll lokal laufen und zuerst die Datenqualitaet sicher beherrschen:

1. Import und Klassifizierung aktueller und zukuenftiger Cardmarket-Exports.
2. Raw-Staging aller Quellzeilen mit Datei- und Zeilenreferenz.
3. Normalisierung von Artikeln, Shipments, Produkten, Events und Importdateien.
4. Korrekte Behandlung gruppierter Shipment-Zeilen.
5. Dubletten-Erkennung zwischen ueberlappenden CSV/XLS-Exports.
6. Filterbare Ansichten fuer Datum, Richtung, Artikel, Produkt, Set, Kategorie, Username, Land und Order-ID.
7. Einfache Zeitraum-Reports und Basisdiagramme.

Details stehen in `OUTPUT/MVP_IMPLEMENTATION_PLAN.md`.

## Naechste Schritte

Die naechste sinnvolle Arbeit ist die Umsetzung von Task 1 aus dem MVP-Implementierungsplan:

1. Python-Projektstruktur anlegen.
2. Lokale Import- und Validierungslogik testgetrieben aufbauen.
3. Erst danach die Weboberflaeche umsetzen.

Die Importkorrektheit hat Vorrang vor UI-Arbeit, weil die Feasibility-Review konkrete Risiken bei XLS-Parsing, Unicode, gruppierten Shipment-Zeilen und Dubletten gezeigt hat.
