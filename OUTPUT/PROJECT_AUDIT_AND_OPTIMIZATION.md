# Projekt-Audit und Optimierungsbericht

Stand der Bestandsaufnahme: 2026-07-10

## 1. Projektverstaendnis

### Zweck

Das Projekt ist ein lokales Cardmarket Sales/Purchase Dashboard. Es liest historische und
zukuenftige Cardmarket-Exporte, bewahrt die Rohzeilen nachvollziehbar auf, normalisiert
Bestellungen, Ereignisse, Artikel und Produkte und stellt daraus filterbare Browseransichten
sowie einfache Zeitraumreports bereit.

Die kanonische fachliche Quelle sind 447 lokale Exportdateien (442 XLS, 5 CSV) aus dem
Zeitraum 2016-04-01 bis 2026-07-06. `Datenmodell.md` und das PRD sind abgeleitete
Interpretationen. Die private Quelldatenbasis ist nicht Teil des Git-Repositories.

### Architektur

| Bereich | Umsetzung | Bewertung vor Aenderungen |
|---|---|---|
| Laufzeit | Python 3.12+, lokal aktuell Python 3.14.0rc1 | Kleine, passende Basis; die lokale Vorabversion benoetigt einen Kompatibilitaets-Workaround. |
| Import | CLI und Module unter `src/cm_dashboard/importing` | Echte Verarbeitung, aber Dateiimporte sind nicht durchgehend atomar und Fehler eines Files stoppen den Ordnerimport. |
| Persistenz | SQLite, SQL-Migration `migrations/001_init.sql` | Fuer das Volumen ausreichend; einige Constraints weichen vom Fachmodell ab. |
| Reporting | Parametrisierte SQL-Abfragen in `reporting/queries.py` | Schnell, aber Datumsbasen werden ohne Auswahl doppelt summiert. |
| Web | FastAPI, serverseitiges Jinja, wenig JavaScript | Angemessen schlank; keine SPA-Komplexitaet. Verbindungen werden pro Request nicht geschlossen. |
| Tests | pytest, 84 bestanden, 1 optionaler Full-Source-Test uebersprungen | Gute Modulabdeckung, aber wichtige Integritaetsfehler sind durch einseitige Fixtures nicht abgedeckt. |
| Qualitaet | Ruff | Ausgangszustand fehlerfrei; statische Typpruefung und CI fehlen. |

### Zentrale Datenfluesse

1. Der Scanner klassifiziert Dateien ueber Dateiname, Richtung, Ebene, Datumsbasis und Zeitraum.
2. Der Tabellenleser liest die erste Tabelle und prueft deren Spalten.
3. Rohzeilen werden mit Datei- und Zeilennummer in SQLite gespeichert.
4. Shipment-Fortsetzungszeilen erben die letzte Order-ID und Kopfdaten.
5. Artikel und Shipments werden normalisiert und ueber Richtung/Order-ID verknuepft.
6. Reporting-Abfragen liefern Tabellen, Kennzahlen, Monatsreihen und CSV-Ausgaben.
7. Die Web-App maskiert Nutzernamen und fragt keine vollstaendigen Adress- oder VAT-Werte ab.

### Externe Abhaengigkeiten

- FastAPI, Starlette, Jinja2 und Uvicorn fuer die lokale Web-App.
- SQLite aus der Python-Standardbibliothek.
- Bisher `xlrd` fuer XLS; `python-calamine` wurde als Ersatz gegen alle 442 XLS-Dateien
  geprueft: 0 Lesefehler, 0 Zeilenzahlabweichungen, 0 Headerabweichungen. Das Projekt ist
  MIT-lizenziert und unterstuetzt XLS/XLSX; Quelle: https://github.com/dimastbk/python-calamine
- pytest, HTTP-Testclient und Ruff fuer Entwicklung und Verifikation.
- Keine Cardmarket-API, kein externer Dienst, keine Queue und kein Hintergrundjob.

## 2. Funktionsstand vor Aenderungen

### Vollstaendig bzw. real implementiert

- Klassifizierung aller aktuellen 447 Quelldateien.
- Lesen der aktuellen XLS- und CSV-Exporte.
- Rohdaten-Staging mit Quellenbezug.
- Gruppierung von 10.596 Shipment-Rohzeilen in 2.164 Header und 8.432 Fortsetzungen.
- Normalisierung von Shipments, Events, Artikeln, Produkten, Labels, Sets und Kategorien.
- Verknuepfung aller aktuell normalisierten Artikelzeilen mit Shipments.
- Lokale Dashboard-, Import-, Shipment-, Artikel- und Produktseiten.
- Maskierung personenbezogener Felder in normalen Ansichten.
- Zeitraumreport als CSV.

### Teilweise implementiert

- Idempotenz: unveraenderte Re-Importe duplizieren viele Fakten nicht, aber geaenderte Dateien
  hinterlassen alte normalisierte Zeilen; numerisch gleichwertige Werte wie `8` und `8.0`
  erzeugen unterschiedliche String-Schluessel.
- Dubletten: CSV/XLS-Spiegelungen werden nur teilweise erkannt; echte identische
  Mehrfachpositionen innerhalb einer Bestellung werden dagegen faelschlich zusammengelegt.
- Importstatus: Dateien werden vor Abschluss als `imported` markiert; `imported_at` bleibt leer.
- Importqualitaet: CLI-Validierung existiert, ihre Ergebnisse werden aber nicht vollstaendig fuer
  die Importseite gespeichert. Abdeckungswarnungen fehlen in der Datenbankvalidierung.
- Filter: Kernfilter existieren, aber Menge, Betrag, Kommentar, Waehrung, Importquelle,
  Verknuepfungsstatus und Pagination fehlen.
- Dashboard/Reports: einfache Artikelwerte werden gezeigt; Shipment-Kosten, Commission,
  Trustee Fees, Abdeckungsstatus und umfassende Reporttypen fehlen.
- XLSX: Dateiname und Scanner akzeptieren XLSX, der Leser lehnt es ab.

### Nicht implementiert oder bewusst ausserhalb des MVP

- Upload/Drag-and-drop und Importvorschau in der Weboberflaeche.
- Asynchroner Import mit Fortschrittsanzeige.
- Handelspartneransicht, Einstellungen, Backup/Restore und gespeicherte Filter/Reports.
- PDF-/Excel-Export, Steuerlogik, Inventar/FIFO und belastbare Einzelmargen.
- Authentifizierung, Rollen und Mehrbenutzerbetrieb; die Anwendung ist lokal-only.
- Monitoring/Telemetry und produktives Hosting.

Es wurden keine Mock-Backends oder nur dekorative UI-Aktionen gefunden. Die vorhandenen Seiten
greifen auf echte SQLite-Daten zu.

## 3. Kritische Bestandsaufnahme

### Kritisch

#### K1: Berichte und Produktansichten zaehlen Kauf- und Zahlungsansicht gemeinsam

- Problem: `date_basis=None` filtert `article_lines` nicht. Beide Exportsichten derselben
  Geschaeftsposition werden summiert.
- Beleg: Aktuelle DB ohne Basis: 10.560 Zeilen / 41.232,51 EUR. Fachlich deduplizierte Sicht
  ohne Datumsbasis: 5.328 Zeilen / 21.252,03 EUR.
- Auswirkung: Dashboard-KPIs, Produktwerte und CSV-Reports sind standardmaessig materiell falsch.
- Ursache: Datumsbasis ist Teil des Artikel-Business-Keys, aber kein Pflicht-/Standardfilter.
- Loesung: Eine sichtbare, validierte Datumsbasis fuer alle Artikel-Aggregationen erzwingen;
  aufgrund der vollstaendigen aktuellen Abdeckung PAYMENTDATE als dokumentierten Standard nutzen.
- Risiko der Aenderung: Mittel; angezeigte Werte sinken, weil die bisherige Doppelzaehlung endet.
- Betroffen: `reporting/queries.py`, `web/app.py`, Templates, Reporttests.
- Tests: Zwei Sichten derselben Position importieren und exakt eine Basis aggregieren.

#### K2: Die Artikel-Dublettenlogik ist in beide Richtungen falsch

- Problem: Decimal-Werte werden als nichtkanonische Strings serialisiert (`8` != `8.0`).
  Gleichzeitig fehlt ein Vorkommensindex fuer zwei fachlich echte identische Positionen.
- Beleg: Von 44 bekannten CSV/XLS-Spiegelzeilen werden nur 12 zusammengelegt; 32 bleiben doppelt.
  Vier echte doppelte XLS-Zeilen werden dagegen entfernt und erzeugen Mengen-/Wertabweichungen.
- Auswirkung: Normalisierte Artikelwerte sind zu hoch oder zu niedrig.
- Ursache: Ein einzelner UNIQUE-Business-Key soll sowohl Dateispiegelungen als auch
  Positionsidentitaet abbilden.
- Loesung: Decimal-Werte kanonisch serialisieren und identische Zeilen innerhalb jeder Datei
  fortlaufend nummerieren; derselbe Vorkommensindex dedupliziert parallele CSV/XLS-Dateien.
- Risiko der Aenderung: Hoch fuer bestehende DBs; deshalb Normalisierungsversion und atomarer
  Neuaufbau statt stiller Mischmigration.
- Betroffen: `deduplication.py`, `raw_store.py`, `article_import.py`, Migration/CLI.
- Tests: Alle fuenf CSV/XLS-Paare, `8` vs. `8.0`, echte identische Doppelposition.

#### K3: Personenbezogene Quelldatenfragmente sind im oeffentlichen Repository versioniert

- Problem: Analyse- und Testdateien enthalten eine reale Strassenadresse sowie reale Nutzer-
  und Bestellkennungen. Das Repository `Scarrty/cmhistory` ist oeffentlich.
- Auswirkung: Datenschutz- und Geschaeftsdatenrisiko trotz korrekt ignorierter XLS/CSV-Dateien.
- Ursache: Regressionstests zitieren private Real-Fixtures mit konkreten erwarteten Werten.
- Loesung: Konkrete Werte im aktuellen Stand redigieren; Tests auf synthetische Daten oder
  strukturelle Aussagen umstellen. Eine Historienumschreibung nur nach expliziter Entscheidung.
- Risiko der Aenderung: Niedrig im aktuellen Stand; Historienumschreibung waere hoch.
- Betroffen: `OUTPUT/*.md`, mehrere Tests.
- Tests: Secret-/PII-Suchlauf ueber versionierte Dateien.

### Hoch

#### H1: Shipment-Identitaet widerspricht dem Fachmodell

- Problem: `shipments.order_id` ist global UNIQUE; PRD und Datenmodell definieren
  `direction + order_id`.
- Auswirkung: Eine kuenftige gleichlautende Kauf- und Verkaufs-ID ueberschreibt die andere
  Richtung und verknuepft Artikel falsch.
- Beleg: `migrations/001_init.sql`, `shipment_import.py`, `article_import.py`. Aktuell gibt es
  noch 0 richtungsuebergreifende Kollisionen, das Risiko ist prospektiv.
- Loesung: Rueckwaertskompatible SQLite-Migration auf UNIQUE(direction, order_id) und alle
  Lookups/Links richtungssensitiv machen.
- Risiko: Mittel; Migration muss Foreign Keys und bestehende IDs erhalten.
- Tests: Gleiche Order-ID in beiden Richtungen bleibt getrennt und korrekt verknuepft.

#### H2: Dateiimporte sind nicht atomar und nicht fehlertolerant

- Problem: Mehrere verschachtelte Connection-Kontexte committen Teilstufen. Der Status wird vor
  Normalisierung auf `imported` gesetzt; ein Fehler beendet den kompletten Ordnerlauf.
- Auswirkung: Teilimporte, falsche Statusanzeige und blockierte Monatsimporte.
- Loesung: Ein Savepoint pro Datei, Status erst nach Erfolg, Fehlerissue nach Rollback,
  Fortsetzung mit weiteren Dateien und fehlerhafter Gesamt-Exitcode.
- Risiko: Mittel.
- Tests: Normalisierungsfehler hinterlaesst keine Roh-/Faktdaten; zweite Datei wird trotzdem
  importiert; Status/Issue sind korrekt.

#### H3: Bestehende Dateien werden trotz Hash immer vollstaendig neu verarbeitet

- Problem: Der Hash wird gespeichert, aber nicht fuer einen Fast-Path verwendet.
- Auswirkung: Monatliche Importe lesen und schreiben alle 447 Dateien erneut.
- Loesung: Unveraenderte, erfolgreich importierte Datei ueberspringen; geaenderten Inhalt unter
  gleichem Pfad als Konflikt behandeln; expliziten atomaren DB-Neuaufbau bereitstellen.
- Risiko: Mittel.
- Tests: Zweiter Lauf meldet `skipped`; geaenderte Datei wird nicht still gemischt.

#### H4: Validierung ist in CLI, DB und UI inkonsistent

- Problem: Die Importseite zeigt nur 5 waehrend des Imports erzeugte Issues; die CLI findet
  17 DB-Hinweise. Fehlende Monatsabdeckung wird nur gegen den Quellordner berechnet.
- Auswirkung: Nutzer sieht auf der zentralen Qualitaetsseite nicht alle bekannten Risiken.
- Loesung: DB-basierte Coverage-Pruefung, reproduzierbares Ersetzen abgeleiteter Issues und
  Persistenz nach dem Batchimport.
- Risiko: Niedrig bis mittel.
- Tests: Keine Issue-Vervielfachung nach Wiederholung; UI zeigt Coverage und Datenchecks.

### Mittel

#### M1: Web-Connections werden nicht geschlossen

- Auswirkung: Ressourcenleck und auf Windows potenziell laenger gehaltene DB-Handles.
- Loesung: Schema einmal beim App-Aufbau anwenden, read-only Connections je Request explizit
  schliessen und Busy Timeout setzen.

#### M2: Mobile Layout ist horizontal ueberbreit

- Beleg bei 390px Viewport: Dokumentbreite 818px, KPI-Spalten je 395px.
- Ursache: Min-Content-Breite der Tabellen propagiert durch Grid/Panel.
- Loesung: `min-width: 0` an Layoutgrenzen, Tabellen nur im eigenen Scrollcontainer, responsive
  Filter/KPIs und erneute Browserpruefung.

#### M3: Listen sind bei 500 Zeilen still abgeschnitten

- Auswirkung: Der Nutzer kann grosse Treffermengen nicht vollstaendig durchsuchen.
- Loesung: Serverseitige Pagination mit Trefferzahl, stabiler Reihenfolge und erhaltenen Filtern.

#### M4: Filterwerte sind freie Texte ohne Validierung

- Auswirkung: Tippfehler liefern leere Ergebnisse; ungueltige Datumswerte werden lexikografisch
  mit ISO-Strings verglichen.
- Loesung: Enums/Datumspruefung, Auswahlfelder fuer Richtung/Basis, 422 bei ungueltigen Parametern.

#### M5: Sicherheits- und Datenschutz-Hardening fehlt

- Keine schreibenden Web-Endpunkte, kein SQL-Injection-Befund und Jinja-Autoescaping sind positiv.
- Es fehlen Host-Allowlist/DNS-Rebinding-Schutz, restriktive Response-Header und dokumentierte
  Access-Log-/OneDrive-Risiken. Auth ist fuer localhost bewusst kein MVP-Bestandteil.

#### M6: Dependency- und Build-Gates sind unvollstaendig

- `pip-audit` findet in der lokalen Umgebung pytest 8.4.2 mit einem behobenen Temp-Verzeichnis-
  Problem sowie einen veralteten/vulnerablen pip. pytest >=9.0.3 behebt die relevante Luecke.
- Starlette warnt, dass der alte `httpx`-Testclient veraltet ist; aktuelle Starlette-Versionen
  empfehlen `httpx2`.
- Typpruefung, CI und ein wirklich fehlschlagendes PowerShell-Verifikationsskript fehlen.

### Niedrig

- Doppelte kleine Normalisierungshelfer in Importmodulen.
- Direkte SQL-Abfragen fuer Import-/Produktseiten ausserhalb der Reporting-Schicht.
- Keine Migrationschecksummen; fuer den lokalen MVP derzeit vertretbar.
- Englische UI in einem deutschsprachigen Einzelplatzprojekt.
- Kein strukturierter Anwendungslogger; derzeit keine komplexen Hintergrundablaeufe.

## 4. Performance-Baseline

Auf `data/verify_mvp.db` mit 447 Importfiles und 10.560 aktuell normalisierten Artikelzeilen:

| Abfrage | Mittelwert ueber 50 Laeufe |
|---|---:|
| Zeitraum-KPIs mit Datumsbasis | 6,55 ms |
| Monatsaggregation | 7,10 ms |
| Artikelsuche | 5,51 ms |
| Shipment-Suche | 1,76 ms |

Die Abfragen liegen deutlich unter dem PRD-Ziel von 500 ms. Es gibt keinen Anlass fuer Cache,
Materialized Views oder eine andere Datenbank. Korrektheit, Pagination und Connection-Lifecycle
sind wichtiger als Mikrooptimierungen.

## 5. Priorisierter Verbesserungsplan

| Prio | Arbeitspaket | Aenderungsrisiko | Verifikation |
|---|---|---:|---|
| 1 | PII im aktuellen Git-Stand redigieren und Secret/PII-Pruefung ergaenzen | Niedrig | Repository-Suche, Tests |
| 2 | Calamine-Leser fuer XLS/XLSX, Dependency-Bereinigung | Mittel | Alle 442 XLS, synthetisches XLSX, Header/Zeilen/Unicode |
| 3 | Artikel-Business-Key kanonisch und vorkommenssensitiv machen | Hoch | 5 Spiegelpaare, echte Mehrfachzeilen, Summenabgleich |
| 4 | Richtungssensitive Shipment-Identitaet migrieren | Mittel | Migration von Alt-DB, Dual-ID-Test, FK-/Integrity-Check |
| 5 | Import transaktional, fehlertolerant und hash-basiert machen | Mittel | Rollback-, Continue-, Skip- und Konflikttests |
| 6 | Normalisierungsversion und atomaren DB-Neuaufbau einfuehren | Mittel | Alter Bestand bleibt bis erfolgreichem Replace intakt |
| 7 | Datumsbasis in Dashboard/Artikel/Produkt/CSV sichtbar erzwingen | Mittel | Cross-Basis-Regressions- und UI-Tests |
| 8 | Validierung vereinheitlichen und Importseite vervollstaendigen | Niedrig | Wiederholbare Issue-Zahlen, Coverage-/Plausibilitaetstests |
| 9 | Connections und lokale Web-Sicherheitsheader haerten | Niedrig | Request-/Header-/Host-/Handle-Tests |
| 10 | Mobile Breite, Auswahlfelder, Fehler-/Leerzustaende und Pagination verbessern | Mittel | Desktop/Mobil-Browserpruefung und Webtests |
| 11 | pytest/httpx aktualisieren, Typcheck, CI und Verifikationsskript haerten | Mittel | Frische Installation, mypy, ruff, pytest, Build, Audit |
| 12 | README, Importanleitung und diesen Abschlussbericht aktualisieren | Niedrig | Befehle gegen frische DB ausfuehren |

## 6. Bewusst nicht eigenmaechtig entschieden

- Ob Kauf- oder Zahlungsdatum fachlich dauerhaft der bevorzugte Standard sein soll. Fuer die
  technische Korrektur wird PAYMENTDATE vorlaeufig sichtbar als Standard verwendet, weil diese
  Sicht im aktuellen Artikelbestand alle 1.082 Orders abdeckt; der Nutzer kann umschalten.
- Ob das oeffentliche Repository nach Redigierung des aktuellen Stands komplett umgeschrieben
  werden soll. Das erfordert Force-Push und Koordination mit allen Klonen.
- Ob die Datenbank ausserhalb des OneDrive-synchronisierten Projektordners liegen soll.
- Ob spaeter Hosting/Authentifizierung, steuerliche Reports oder Inventarlogik benoetigt werden.
- Wie geaenderte historische Exporte fachlich zusammengefuehrt werden sollen. Bis zu einer Regel
  wird gleicher Pfad mit anderem Hash nicht still inkrementell vermischt.

## 7. Ausgangsverifikation

| Pruefung | Ergebnis vor Aenderungen |
|---|---|
| Git | Sauber, `main` synchron zu `origin/main` |
| Tests | 84 bestanden, 1 optional uebersprungen |
| Ruff | Bestanden |
| pip check | Bestanden |
| Dependency Audit | 6 Findings: 5 in lokalem pip, 1 in pytest 8.4.2 |
| SQLite integrity_check | `ok` |
| SQLite foreign_key_check | 0 Befunde |
| Aktuelle Verknuepfung | 0 unverknuepfte normalisierte Artikelzeilen |
| XLS-Vergleich xlrd/Calamine | 442 gelesen, 0 Fehler, 0 Zeilen-/Headerabweichungen |
| Desktop UI | Rendert; Kennzahlen sind wegen fehlender Datumsbasis doppelt |
| Mobile UI 390px | Fehler: 818px Dokumentbreite und horizontaler Seiten-Scroll |

## 8. Abschlussbericht

Dieser Abschnitt wird nach der Umsetzung mit den tatsaechlichen Aenderungen, bewusst
zurueckgestellten Punkten und finalen Verifikationsergebnissen ergaenzt.
