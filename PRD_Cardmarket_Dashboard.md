# PRD: Cardmarket Sales/Purchase Dashboard

> **AI-/Best-Effort-Hinweis:** Dieses PRD wurde zu 100 % mit KI generiert. Keine Gewaehr;
> siehe [NOTICE.md](NOTICE.md).

Stand: 2026-07-08

Basis: Cardmarket-Historie in `D:\OneDrive\Dokumente\CM History` und Datenmodell in `Datenmodell.md`.

## 1. Produktziel

Es soll eine schlanke, private Webanwendung entstehen, die Cardmarket-Excel-Exporte importiert, normalisiert, zusammengehoerige Datensaetze korrekt verknuepft und als Sales/Purchase Dashboard darstellt.

Die Anwendung soll historische Exporte einmalig laden koennen und danach monatlich neue Exporte importieren. Nutzer sollen Bestellungen, Artikel, Kosten, Umsaetze und Zeitraeume durchsuchen, filtern, vergleichen und grafisch auswerten koennen.

## 2. Zielgruppe

Primaerer Nutzer ist der Account-Inhaber mit eigenen Cardmarket-Daten.

Typische Nutzung:

- Monatliche Cardmarket-Exporte importieren
- Sales und Purchases nach Zeitraum analysieren
- Artikel, Sets, Kategorien und Handelspartner suchen
- Bestellungen inklusive Positionen nachvollziehen
- Umsatz-, Einkaufs- und Kostenentwicklung als Diagramme betrachten
- Reports fuer Steuer, Controlling oder persoenliche Auswertung erstellen

## 3. Problemstellung

Die Cardmarket-Daten liegen als viele monatliche Excel-Dateien vor. Die Dateien sind nach Richtung, Ebene und Datumsbasis getrennt:

- `PURCHASED` oder `SOLD`
- `ARTICLES` oder `SHIPMENTS`
- `BYPURCHASEDATE` oder `BYPAYMENTDATE`

Dadurch liegen zusammengehoerige Informationen verteilt in mehreren Dateien:

- Eine Sendung steht in Shipment-Exporten.
- Die einzelnen Artikelpositionen stehen in Article-Exporten.
- Kaufdatum und Zahlungsdatum koennen in unterschiedlichen Exporten stehen.
- Dieselben fachlichen Bestellungen koennen in mehreren Exportdateien wieder auftauchen.

Das Produkt muss diese getrennten Sichten in ein konsistentes Modell ueberfuehren, statt Dateien nur nebeneinander anzuzeigen.

## 4. Erfolgsmetriken

- 100 Prozent der vorhandenen lesbaren Exporte koennen importiert werden.
- Wiederholter Import derselben Datei erzeugt keine doppelten Bestellungen oder Artikelzeilen.
- Zu mindestens 99 Prozent der Artikelzeilen wird die passende Sendung ueber `Shipment nr.` / `OrderID` verknuepft.
- Filterantworten fuer typische Suchanfragen liegen unter 500 ms bei ca. 25.000 bis 100.000 Zeilen.
- Ein neuer Monatsimport dauert fuer die uebliche Dateimenge unter 30 Sekunden.
- Reports fuer frei waehlbare Zeitraeume koennen ohne manuellen Excel-Abgleich erzeugt werden.

## 5. MVP-Umfang

Der MVP ist eine lokale oder private Web-App mit folgenden Kernfunktionen:

1. Importbereich fuer `.XLS` und `.CSV`
2. Importhistorie mit Status, Fehlern, Dubletten und Zeilenzahlen
3. Normalisierte Datenansicht fuer Sendungen und Artikelpositionen
4. Verknuepfung von Shipments, Article Lines, Produkten, Events und Importdateien
5. Globale Filter fuer Datum, Richtung, Artikel, Produkt-ID, Set, Kategorie, Username, Land, Betrag und Kommentar
6. Dashboard mit KPI-Kacheln, Zeitreihen und Top-Listen
7. Reports fuer frei waehlbare Datumszeitraeume
8. Detailseite fuer einzelne Sendungen mit Artikelpositionen, Kosten, Events und Quellen

## 6. Nicht-Ziele fuer den MVP

- Kein Live-Zugriff auf Cardmarket
- Keine automatische API-Synchronisation
- Keine Mehrbenutzerverwaltung
- Keine vollstaendige Lagerbewertung mit FIFO/LIFO
- Keine automatische Gewinnermittlung pro verkauftem Einzelartikel, solange keine eindeutige Inventarzuordnung zwischen Einkauf und Verkauf existiert
- Kein oeffentliches Hosting ohne Authentifizierung und Datenschutzkonzept

## 7. Datenquellen

Unterstuetzte Dateien:

- Alte Excel-Dateien `.XLS`
- CSV-Dateien `.CSV`

Dateinamensschema:

```text
^(PURCHASED|SOLD) (ARTICLES|SHIPMENTS)-BY(PAYMENTDATE|PURCHASEDATE)-YYYY-MM-DD_YYYY-MM-DD.(XLS|CSV)$
```

Bekannte Strukturen:

- Artikeldateien:
  - `Shipment nr.`
  - `Date of purchase` oder `Date of payment`
  - `Article`
  - `Product ID`
  - `Localized Product Name`
  - `Expansion`
  - `Category`
  - `Amount`
  - `Article Value`
  - `Total`
  - `Currency`
  - `Comments`

- Sendungsdateien:
  - `OrderID`
  - `Username`
  - `Name`
  - `Street`
  - `City`
  - `Country`
  - `Is Professional`
  - `VAT Number`
  - `Date of Purchase` oder `Date of Payment`
  - `Article Count`
  - `Merchandise Value`
  - `Shipment Costs`
  - `Trustee service fee` bei Purchases
  - `Commission` bei Sales
  - `Total Value`
  - `Currency`
  - `Description`
  - `Product ID`
  - `Localized Product Name`

## 8. Datenverknuepfung

### 8.1 Fachliche Identitaet

Eine Bestellung bzw. Sendung wird primaer ueber folgende Kombination identifiziert:

```text
direction + order_id
```

Dabei gilt:

- `OrderID` aus Shipment-Exporten entspricht `Shipment nr.` aus Article-Exporten.
- `PURCHASED` und `SOLD` bleiben getrennte Richtungen.
- Kaufdatum und Zahlungsdatum sind Events derselben Sendung, keine getrennten Sendungen.

### 8.2 Sendung zu Artikelpositionen

Artikelpositionen werden ueber `direction + Shipment nr.` mit `direction + OrderID` verknuepft.

Wenn eine Artikelposition keine passende Sendung findet:

- Sie wird trotzdem importiert.
- Sie erhaelt den Status `unmatched`.
- Das Dashboard zeigt offene Verknuepfungsprobleme im Importbereich an.

### 8.3 Kauf- und Zahlungsdatum

Kauf- und Zahlungszeitpunkt werden als Events gespeichert:

- `purchase`
- `payment`

Wenn dieselbe Sendung aus beiden Datumsbasen importiert wird, werden beide Events an derselben Sendung gespeichert.

### 8.4 Produktverknuepfung

Produkte werden primaer ueber `Product ID` verknuepft.

Zusatzattribute:

- Artikelname
- Lokalisierter Produktname
- Expansion/Set
- Kategorie

Wenn `Product ID` fehlt oder widerspruechlich ist, wird eine weiche Produktidentitaet aus `article_name + localized_product_name + expansion + category` gebildet und als Qualitaetswarnung markiert.

### 8.5 Dublettenlogik

Ein erneuter Import derselben Datei darf keine neuen fachlichen Datensaetze erzeugen.

Dublettenregeln:

- Datei: `file_name` ist eindeutig.
- Sendung: `direction + order_id` ist eindeutig.
- Event: `shipment_id + event_type` ist eindeutig.
- Artikelzeile: `shipment_id + product_id + article_name + amount + article_value + total + comments` plus optional `source_row_number`.

Bei widerspruechlichen Daten:

- Bestehender Datensatz bleibt erhalten.
- Neuer Wert wird als Konflikt protokolliert.
- Nutzer kann im Importprotokoll sehen, welche Felder abweichen.

## 9. Funktionale Anforderungen

### 9.1 Import

Der Nutzer kann einzelne Dateien oder mehrere Dateien per Drag & Drop importieren.

Anforderungen:

- Automatische Erkennung von Richtung, Ebene, Datumsbasis und Zeitraum aus dem Dateinamen
- Unterstuetzung fuer `.XLS` und `.CSV`
- Vorschau vor finalem Import
- Validierung der Pflichtspalten
- Normalisierung von Datumsformaten
- Normalisierung von Dezimalzahlen mit Punkt oder Komma
- Speicherung der Originaldatei-Metadaten
- Idempotenter Re-Import
- Importprotokoll mit Erfolgen, Warnungen und Fehlern
- Moeglichkeit, neue Monatsdateien spaeter nachzuladen

Akzeptanzkriterien:

- Eine bereits importierte Datei wird als bereits bekannt erkannt.
- Ein Monat kann importiert werden, ohne historische Monate erneut laden zu muessen.
- Fehlerhafte Dateien blockieren nicht den Import anderer Dateien.
- Importierte Datensaetze sind sofort filter- und reportfaehig.

### 9.2 Dashboard-Uebersicht

Die Startseite zeigt eine kompakte Uebersicht mit KPI-Kacheln und Diagrammen.

KPI-Kacheln:

- Sales Umsatz
- Purchase Volumen
- Verkaufsanzahl
- Einkaufsanzahl
- Artikelanzahl verkauft
- Artikelanzahl gekauft
- Versandkosten Sales
- Versandkosten Purchases
- Commission
- Trustee service fees
- Durchschnittlicher Warenkorb
- Anzahl offener Import-/Verknuepfungswarnungen

Diagramme:

- Umsatz und Einkauf pro Monat
- Anzahl Bestellungen pro Monat
- Artikelmengen pro Monat
- Top 10 Produkte nach Umsatz
- Top 10 Produkte nach Menge
- Top Kategorien
- Top Expansions/Sets
- Sales vs. Purchases Zeitreihe
- Kostenanteile: Versand, Commission, Trustee Fees

### 9.3 Datenexplorer

Der Datenexplorer ist eine tabellarische Ansicht mit starken Filtern.

Ansichten:

- Sendungen
- Artikelpositionen
- Produkte
- Handelspartner
- Importe

Globale Filter:

- Zeitraum
- Datumsbasis: Kaufdatum, Zahlungsdatum oder beide
- Richtung: gekauft, verkauft oder beide
- Artikelname
- Lokalisierter Produktname
- Produkt-ID
- Expansion/Set
- Kategorie
- Username
- Name
- Land
- Waehrung
- Betrag von/bis
- Menge von/bis
- Kommentar enthaelt
- Importdatei
- Importstatus
- Verknuepfungsstatus

Tabellenfunktionen:

- Sortieren
- Spalten ein-/ausblenden
- Schnellsuche
- Pagination
- Export der gefilterten Ansicht als CSV
- Klick auf Sendung oeffnet Detailseite
- Klick auf Produkt oeffnet Produktdetail

### 9.4 Sendungsdetail

Die Sendungsdetailseite zeigt alles, was fachlich zusammengehoert.

Inhalte:

- OrderID
- Richtung
- Username und Name
- Adresse, falls vorhanden
- Kaufdatum
- Zahlungsdatum
- Artikelpositionen
- Merchandise Value
- Shipment Costs
- Commission oder Trustee service fee
- Total Value
- Beschreibung
- Quell-Dateien
- Importwarnungen oder Konflikte

Akzeptanzkriterium:

- Fuer eine bekannte `OrderID` sind Shipment-Informationen und Article Lines auf derselben Detailseite sichtbar.

### 9.5 Produktdetail

Die Produktdetailseite aggregiert alle Kaeufe und Verkaeufe zu einer Produkt-ID.

Inhalte:

- Produkt-ID
- Artikelname
- Lokalisierter Name
- Expansion
- Kategorie
- Anzahl gekauft
- Anzahl verkauft
- Einkaufswert
- Verkaufswert
- Durchschnittlicher Einkaufswert
- Durchschnittlicher Verkaufswert
- Zeitreihe nach Monat
- Alle betroffenen Sendungen

Hinweis:

- Ein echter Gewinn pro Produkt ist nur dann belastbar, wenn Einkaufs- und Verkaufspositionen fachlich als Inventarbewegungen gekoppelt werden koennen. Im MVP wird daher zunaechst eine aggregierte Gegenueberstellung gezeigt, kein garantierter Einzelmargen-Nachweis.

### 9.6 Reports

Reports werden fuer frei waehlbare Zeitraeume erstellt.

Reporttypen MVP:

- Monatsreport
- Jahresreport
- Sales Report
- Purchase Report
- Combined Sales/Purchase Report
- Produktreport
- Kategorie-/Set-Report
- Kostenreport
- Importqualitaetsreport

Reportfilter:

- Zeitraum
- Richtung
- Datumsbasis
- Kategorie
- Expansion
- Produkt
- Username/Land

Reportausgabe:

- Interaktive Ansicht
- CSV-Export
- Optional spaeter PDF-Export

Pflichtkennzahlen:

- Anzahl Sendungen
- Anzahl Artikelpositionen
- Summe Merchandise Value
- Summe Shipment Costs
- Summe Total Value
- Summe Commission
- Summe Trustee Fees
- Durchschnittlicher Bestellwert
- Top Produkte
- Top Kategorien
- Top Expansions

### 9.7 Diagramme

Diagramme sollen interaktiv sein und denselben Filterkontext wie Tabellen verwenden.

MVP-Diagrammtypen:

- Linienchart fuer Zeitreihen
- Balkendiagramm fuer Top-Listen
- Gestapeltes Balkendiagramm fuer Sales/Purchase-Vergleich
- Donut oder Balken fuer Kostenaufteilung
- Heatmap oder Kalenderansicht spaeter optional

Interaktion:

- Hover zeigt Werte
- Klick auf Diagrammsegment setzt Filter
- Zeitraum kann von Tag, Monat, Quartal, Jahr umgeschaltet werden

## 10. Informationsarchitektur

Hauptnavigation:

- Dashboard
- Explorer
- Reports
- Produkte
- Importe
- Einstellungen

Empfohlene Seiten:

| Seite | Zweck |
|---|---|
| Dashboard | Schnelle Kennzahlen und Diagramme |
| Explorer | Freies Suchen, Filtern und Drilldown |
| Reports | Wiederholbare Zeitraum-Auswertungen |
| Produkte | Produkt- und Set-Perspektive |
| Importe | Upload, Status, Fehler, Historie |
| Einstellungen | Datenbank, Waehrung, Datenschutz, Backups |

## 11. UX-Anforderungen

Die Anwendung soll wie ein Arbeitsdashboard wirken: ruhig, dicht, schnell erfassbar und ohne Marketing-Optik.

Layout:

- Linke Navigation oder kompakte Top-Navigation
- Oben ein dauerhafter Zeitraumfilter
- KPI-Kacheln in einer kompakten Reihe
- Tabellen mit klarer Spaltendichte
- Diagramme direkt neben den wichtigsten Kennzahlen
- Detailseiten mit Kopfbereich, Summen und darunter Artikelpositionen

Bedienung:

- Filter sollen kombinierbar sein.
- Aktive Filter muessen sichtbar und einzeln entfernbar sein.
- Tabellen und Diagramme muessen denselben Filterzustand teilen.
- Der Nutzer soll von KPI zu Detaildaten drillen koennen.
- Importfehler muessen klar benannt werden, inklusive Datei und Zeile.

## 12. Datenmodell-Anforderungen

Das in `Datenmodell.md` beschriebene Modell ist Grundlage.

Mindesttabellen:

- `import_file`
- `shipment`
- `shipment_event`
- `shipment_line`
- `product`
- `expansion`
- `category`
- `party`
- `address` oder Adresssnapshot in `shipment`
- `article_export_row`
- `shipment_export_row`

Zusaetzlich empfohlen:

- `import_issue`
- `data_conflict`
- `saved_report`
- `saved_filter`

### import_issue

Speichert Warnungen und Fehler pro Import.

Felder:

- `import_issue_id`
- `import_file_id`
- `source_row_number`
- `severity`
- `issue_type`
- `message`
- `created_at`

### data_conflict

Speichert abweichende Werte bei Re-Import oder Exportueberlappung.

Felder:

- `data_conflict_id`
- `entity_type`
- `entity_id`
- `field_name`
- `old_value`
- `new_value`
- `source_import_file_id`
- `status`

## 13. Technische Anforderungen

Empfohlene Architektur fuer MVP:

- Web-Frontend
- Backend/API
- Relationale Datenbank
- Serverseitiger Importprozess
- Lokaler Dateispeicher fuer Import-Metadaten, optional nicht fuer Originaldateien

Geeignete technische Richtung:

- Frontend: React oder vergleichbar
- UI: tabellenstarkes Dashboard-Layout
- Charts: ECharts, Recharts oder vergleichbar
- Backend: Node.js, Python oder .NET
- Datenbank: SQLite fuer lokale Einzelplatzversion, PostgreSQL fuer spaetere Serverversion
- Excel-Import: Bibliothek mit Unterstuetzung fuer alte `.XLS`-Dateien

Wichtige technische Vorgaben:

- Import muss alte Excel-Binaerdateien lesen koennen.
- Parser darf Excel nicht zwingend als installierte Desktop-App voraussetzen.
- Datums- und Dezimalnormalisierung muss zentral getestet werden.
- Originalzeilen muessen in Staging-Tabellen nachvollziehbar bleiben.
- Alle Auswertungen laufen auf normalisierten Tabellen, nicht direkt auf Excel-Dateien.

## 14. Datenschutz und Sicherheit

Die Daten enthalten personenbezogene Informationen:

- Namen
- Usernames
- Strassen
- Orte
- Laender
- VAT-Nummern

Anforderungen:

- Anwendung standardmaessig privat/lokal betreiben
- Kein externer Upload ohne explizite Entscheidung
- Optionales Ausblenden personenbezogener Spalten
- Backup-/Restore-Funktion fuer Datenbank
- Exportfunktion soll Filter respektieren
- Bei spaeterem Hosting: Authentifizierung, HTTPS und Rollenmodell

## 15. Performance-Anforderungen

Zielvolumen:

- Historisch: mindestens 447 Dateien und ca. 21.000 Datenzeilen
- Zukunft: mindestens 10 Jahre weitere Monatsdaten
- Auslegung MVP: 100.000 bis 250.000 Artikelzeilen ohne spuerbare Traegheit

Anforderungen:

- Indizes auf `order_id`, `direction`, `event_at`, `product_id`, `category`, `expansion`, `username`
- Aggregationen fuer Dashboard koennen gecacht werden
- Import laeuft asynchron mit Statusanzeige
- Tabellen laden serverseitig paginiert

## 16. Qualitaetsanforderungen

Tests:

- Dateinamenparser
- Spaltenerkennung
- Datumsparser
- Dezimalparser
- Dublettenerkennung
- Verknuepfung `OrderID` zu `Shipment nr.`
- Merge von Kauf- und Zahlungsdatum
- CSV/XLS-Ueberlappung
- Reportsummen gegen bekannte Beispielmonate

Validierung:

- Summe der Artikelpositionen je Sendung soll gegen `Merchandise Value` plausibilisiert werden.
- `Article Count` soll gegen Anzahl/Menge der Artikelzeilen plausibilisiert werden.
- `Total Value` soll gegen Merchandise, Versand und Fees plausibilisiert werden.
- Unmatched Rows werden sichtbar ausgewiesen.

## 17. Release-Plan

### Phase 1: Import und Datenbasis

- Datenbankmodell anlegen
- Import fuer `.XLS` und `.CSV`
- Staging-Tabellen
- Normalisierung
- Dublettenlogik
- Verknuepfung von Sendungen und Artikelpositionen
- Importprotokoll

### Phase 2: Explorer und Detailseiten

- Sendungsliste
- Artikelpositionsliste
- Globale Filter
- Sendungsdetail
- Produktdetail
- CSV-Export gefilterter Tabellen

### Phase 3: Dashboard und Reports

- KPI-Dashboard
- Zeitreihen
- Top-Listen
- Zeitraumreports
- Reportexport
- Importqualitaetsreport

### Phase 4: Komfort und Erweiterung

- Gespeicherte Filter
- Gespeicherte Reports
- PDF-Export
- Backup/Restore
- Optionale Inventar-/Margenlogik
- Optionale Cardmarket-API-Anbindung, falls verfuegbar und gewuenscht

## 18. Offene Entscheidungen

- Soll die erste Version rein lokal laufen oder als private Server-Webapp?
- Soll SQLite fuer den Start reichen oder direkt PostgreSQL genutzt werden?
- Sollen Originaldateien nach Import gespeichert werden oder nur Metadaten und Rohzeilen?
- Sollen personenbezogene Daten voll sichtbar bleiben oder standardmaessig maskiert werden?
- Soll spaeter eine echte Inventarlogik fuer Gewinn pro verkauftem Artikel entstehen?
- Welche Reportformate sind zuerst wichtig: CSV, Excel, PDF?

## 19. MVP-Akzeptanzkriterien

Der MVP gilt als fertig, wenn:

- Alle vorhandenen historischen Dateien importiert oder mit klarer Fehlermeldung abgelehnt werden.
- Neue Monatsdateien ohne Codeaenderung importiert werden koennen.
- Re-Importe keine fachlichen Dubletten erzeugen.
- Eine Sendung alle passenden Artikelpositionen, Kauf-/Zahlungsevents und Kosten zeigt.
- Der Nutzer nach Datum, Artikel, Produkt-ID, Set, Kategorie, Richtung, Username, Land, Betrag und Kommentar filtern kann.
- Das Dashboard Sales und Purchases fuer beliebige Zeitraeume visualisiert.
- Reports fuer Monats- und Jahreszeitraeume erzeugt und als CSV exportiert werden koennen.
- Importprobleme und unverknuepfte Datensaetze sichtbar sind.
