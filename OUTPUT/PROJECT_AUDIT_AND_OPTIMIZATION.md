# Projekt-Audit und Optimierungsbericht

> **AI-/Best-Effort-Hinweis:** Projekt und Audit wurden zu 100 % mit KI generiert. Keine
> Gewaehr; siehe [NOTICE.md](../NOTICE.md).

Stand der Bestandsaufnahme: 2026-07-10; Abschlussverifikation: 2026-07-11

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
| Persistenz | SQLite, heute paketierte SQL-Migrationen unter `src/cm_dashboard/migrations` | Fuer das Volumen ausreichend; einige Constraints wichen vor der Korrektur vom Fachmodell ab. |
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
- Beleg: damaliges `migrations/001_init.sql`, `shipment_import.py`, `article_import.py`. Aktuell gibt es
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

### 8.1 Projektverstaendnis nach der Umsetzung

Der fachliche Zweck und die lokale Einzelplatzarchitektur bleiben unveraendert. Die Anwendung
importiert private Cardmarket-Dateiexporte in einen reproduzierbaren SQLite-Arbeitsbestand,
verknuepft Artikel und Sendungen richtungssensitiv und stellt read-only Auswertungen bereit.
Die Originaldateien bleiben die kanonische Quelle; die DB kann jederzeit atomar neu aufgebaut
werden. Es wurden keine Cloud-, API-, Mock- oder Mehrbenutzerkomponenten eingefuehrt.

Der wichtigste fachliche Datenfluss ist jetzt durchgehend abgesichert:

1. 447 Dateien werden klassifiziert und mit Calamine bzw. CSV gelesen.
2. Header und Pflichtwerte werden vor dem Schreiben validiert.
3. Jede Datei schreibt Raw- und Faktdaten innerhalb eines Savepoints.
4. Decimal-Werte und Mehrfachvorkommen bilden stabile Artikel-Business-Keys.
5. Artikel werden ueber `direction + order_id` an Sendungen gebunden.
6. DB-basierte Validierung prueft Coverage, Reconciliation, Eventkonflikte und Gruppierung.
7. Reporting erzwingt eine sichtbare Datumsbasis und liefert paginierte, gefilterte Ansichten.

### 8.2 Durchgefuehrte Aenderungen

| Urspruengliches Problem | Umgesetzte Loesung | Betroffene Bereiche | Wirkung und Verifikation |
|---|---|---|---|
| Private Realwerte im aktuellen oeffentlichen Git-Stand | Konkrete Werte redigiert, Fixture-Assertions dynamisch bzw. synthetisch gemacht | `OUTPUT`, Tests | Aktueller Tree ohne bekannte Realwerte; Secret-/PII-Musterscan ohne Befund |
| Toleranz-/Unicode-Risiken mit XLS und fehlendes XLSX | Einheitlicher Calamine-Reader fuer XLS/XLSX, CSV unveraendert | `readers.py`, `pyproject.toml`, Tests | 442 XLS: 0 Lese-, Header- oder Zeilenzahlabweichungen; synthetischer XLSX-Test |
| Doppelte CSV/XLS-Zeilen und verlorene echte Mehrfachpositionen | Kanonische Decimal-Serialisierung plus Vorkommensindex | `deduplication.py`, Raw-/Artikelimport | 44 Spiegelzeilen nur einmal gezaehlt; echte identische Positionen bleiben erhalten |
| Teilcommits, verfruehter Status und Batchabbruch | Savepoint pro Datei, Rollback/Issue, Fehlerfortsetzung, Hash-Fast-Path und atomarer `rebuild` | `pipeline.py`, CLI | Rollback-, Continue-, Skip-, Konflikt- und Replace-Tests; Folgeimport 0/447/0 |
| Global eindeutige Order-ID | Migration auf `UNIQUE(direction, order_id)` und richtungssensitive Links/Details | Migration 003, Shipment-/Artikelimport, Reporting | Dual-Richtungstest, Alt-DB-Migration, 0 FK-Befunde |
| Doppelte Berichte ueber Kauf-/Zahlungssicht | `PAYMENTDATE` als sichtbarer Standard, validierte Umschaltung auf `PURCHASEDATE` | Reporting, Web, CSV | Default 5.298 statt 10.560 alter Zeilen; Cross-Basis-Regressionspruefung |
| Unvollstaendige und inkonsistente Validierung | Coverage und Summenabgleiche DB-basiert; abgeleitete Issues reproduzierbar persistiert | `validation.py`, Importseite | 18 Coverage-Warnungen, 2 Infos und 5 konkrete Eventdatum-Warnungen; keine Reconciliation-Fehler |
| Offene Connections und schwache lokale Webgrenze | Request-Connections geschlossen, Busy Timeout, Trusted Hosts, CSP/Frame/MIME/Referrer/Cache-Header | `db.py`, `web/app.py` | Handle-/Header-/Hosttests; unbekannter Host liefert 400 |
| Stille Listenlimits und fehlende PRD-Filter | Getrennte Pagination mit Gesamtzahlen; Betrag, Menge, Waehrung, Kommentar, Quelle, Status und Linkstatus | Reporting, Templates | Artikel 53, Sendungen 11 und Importe 5 Seiten im Vollbestand; Filter-/Seitentests |
| Mobile Ueberbreite und englische UI | Grid-/Flex-Minima korrigiert, Tabellen intern scrollbar, deutsche Labels, Skip-Link und Fokuszustand | Templates, CSS | 390px Viewport: 375px Dokumentbreite, 0 externer Overflow; Desktop ebenfalls 0 |
| Verwundete/veraltete Entwicklungsumgebung und fehlende Gates | pytest 9/httpx2, pip 26.1.2, mypy, Ruff, pip-audit, Build, CI und echtes Exitcode-Handling | `pyproject.toml`, Workflow, Skripte | 115 Tests, mypy/Ruff/pip check/Audit/Build bestanden |
| Wheel ohne Migrationen/Templates/Static | Ressourcen ins Paket verschoben, Package Data und Wheel-Inhaltspruefung | `src/cm_dashboard/migrations`, Build-Konfiguration | Frische Wheel-Installation erzeugt DB mit 3 Migrationen und findet Webressourcen |
| Veraltete Betriebsdokumentation | README, Monatsworkflow, Architektur und historischer Planstatus aktualisiert | `README.md`, `docs`, `OUTPUT` | Befehle im finalen Vollcheck ausgefuehrt |

### 8.3 Bewusst nicht umgesetzt

| Punkt | Grund | Verbleibendes Risiko | Empfohlener naechster Schritt |
|---|---|---|---|
| Git-Historie umschreiben | Force-Push ist eine separate irreversible Team-/Repository-Entscheidung | Redigierte Fragmente koennen in alten Commits weiter existieren | Klone/Branches koordinieren, Historie mit geeignetem Tool filtern, danach alle Tokens/Links pruefen |
| Authentifizierung, Rollen und Netzwerkhosting | Fachlich nicht fuer den lokalen MVP entschieden | App waere bei externer Bindung ungeschuetzt | Bis dahin nur `127.0.0.1`; fuer Hosting eigenes Security-/Betriebskonzept erstellen |
| Aktive DB automatisch aus OneDrive auslagern und Backup/Restore-UI | Zielpfad und Aufbewahrungsregeln sind Nutzer-/Betriebsentscheidungen | Sync-Konflikte oder Dateisperren bleiben moeglich | DB-Pfad konfigurierbar machen und versionierte Backup-/Restore-Prozedur festlegen |
| Kombinierte Datumsbasis `beide` | Sie wuerde dieselben Artikelpositionen fachlich doppelt zaehlen | Nutzer kann Kauf-/Zahlungssicht nicht in einer Tabelle vergleichen | Vergleichsansicht mit getrennten Serien definieren, nie als gemeinsame Summe |
| Multi-Currency-Umrechnung | Der aktuelle Bestand enthaelt nur EUR; Wechselkursquelle und Stichtag fehlen | Kuenftige gemischte Waehrungen duerfen nicht addiert werden | Pro-Waehrung-KPIs oder fachlich freigegebenes FX-Modell spezifizieren |
| Vollstaendige PRD-Reports und Explorer | Partneransicht, Sortierung, Spaltenwahl, gefilterter Listenexport, Produktzeitreihe und Kostenreports sind groesserer Produktscope | MVP deckt nicht jede PRD-Komfortfunktion ab | Nach Nutzungsprioritaet in getrennten Produktinkrementen umsetzen |
| Steuer-, FIFO-, Inventar- und garantierte Margenlogik | Quellen belegen keine eindeutige Zuordnung verkaufter zu gekauften Einzelartikeln | Gewinnangaben waeren fachlich nicht belastbar | Inventar-/Bewertungsregeln mit Fachentscheidung und neuen Daten definieren |
| Strukturierter Produktivlogger/Monitoring | Kein Hintergrundbetrieb und kein Hosting im MVP | Lokale Fehleranalyse bleibt CLI-/Log-basiert | Erst bei dauerhaftem Dienstbetrieb strukturierte Events und Rotation einfuehren |
| Lokale Python-3.14.0rc1-Umgebung ersetzen | Systeminstallation liegt ausserhalb des Repositories | Kompatibilitaets-Workaround bleibt lokal noetig | Virtuelle Umgebung mit finalem Python 3.12/3.13 oder finalem 3.14 neu erstellen |

Die direkte SQL-Nutzung auf der Import- und Produktseite sowie fehlende Migrationschecksummen
bleiben niedrige Wartbarkeitsrisiken. Eine Repository-/Service-Schicht waere fuer den aktuellen
Umfang YAGNI und wurde deshalb nicht eingefuehrt.

### 8.4 Finale Verifikation

| Pruefung | Ergebnis |
|---|---|
| Installation | Editable Dev-Installation erfolgreich; altes `httpx` und `xlrd` entfernt |
| Frische Distribution | Wheel in temporaerer Umgebung installiert; Laufzeitdeps konsistent; DB/Webressourcen nutzbar |
| Ruff | Bestanden fuer `src`, `tests`, `scripts` |
| mypy | 0 Befunde in 23 Python-Quelldateien/-skripten |
| pytest | 115 bestanden, 1 bewusst uebersprungen (separater privater Vollquellentest) |
| Vollquellencheck | `verify_mvp.ps1` bestanden; 447 Dateien, 442 XLS + 5 CSV, 0 unbekannt |
| Vollstaendiger Neuaufbau | 447/447 Dateien, 0 fehlgeschlagen; anschliessende CLI-Validierung bestanden |
| SQLite | `integrity_check=ok`, 0 Foreign-Key-Befunde, 3 Migrationen |
| Importstatus | 447 `imported`, 0 andere Statuswerte, 0 fehlende `imported_at` |
| Fakten | 10.576 Raw-Artikelzeilen, 10.596 Raw-Shipmentzeilen, 1.082 Sendungen, 4.065 Produkte |
| Standardreport | 5.298 Artikelpositionen, 1.082 Sendungen, 17.158,50 EUR Kaufwert, 3.803,78 EUR Verkaufswert |
| Weitere Sichten | Gekauft/Kaufdatum: 3.593 Zeilen und 16.176,95 EUR; Verkauft je Basis: 1.641 Zeilen und 3.803,78 EUR |
| Persistierte Validierung | 25 Hinweise: 18 Coverage, 5 fehlende Eventdaten, 2 Informationen; 0 Errors |
| Idempotenter Folgeimport | 0 importiert, 447 uebersprungen, 0 fehlgeschlagen |
| Dependency-Konsistenz | `pip check` ohne Befund |
| Dependency-Sicherheit | `pip-audit`: keine bekannten Schwachstellen; lokales Projekt selbst nicht auf PyPI auditierbar |
| Paketbuild | sdist und Wheel erfolgreich; Migrationen, Templates, CSS und JS im Wheel verifiziert |
| HTTP-Smoke | Dashboard, Importe, Sendungen, Artikel und CSV jeweils 200; unbekannter Host 400 |
| Browser Desktop | 1.265px Client-/Dokumentbreite, 0 externer Overflow, 0 Console-Warnungen/-Fehler |
| Browser Mobil | 390px Viewport, 375px Client-/Dokumentbreite, Panels 343px, Tabellen intern scrollbar, 0 externer Overflow |
| Performance (50 warme Laeufe) | KPIs 6,90 ms; Monat 7,52 ms; Artikelseite Count+100 Rows 16,20 ms; Sendungsseite 2,19 ms |
| Secrets/private Artefakte | Keine getrackten XLS/XLSX/CSV/DB/Logs und kein Credential-Muster im aktuellen Tree |
| Aktive DB | Gepruefter Neuaufbau installiert; alte DB lokal als `data/cardmarket.pre-optimization-20260711.db` gesichert |
| Git | 14 logisch getrennte lokale Commits; nicht gepusht; GitHub-CI daher noch nicht remote ausgefuehrt |

### 8.5 Abschliessende Bewertung

| Dimension | Bewertung nach der Ueberarbeitung |
|---|---|
| Funktionsfaehigkeit | Hoch fuer den lokalen MVP. Import, Verknuepfung, Explorer, Details, Diagramm und CSV arbeiten auf dem Vollbestand. |
| Sicherheit | Angemessen fuer localhost-only: read-only Web, Hostschutz, Header und Maskierung. Nicht fuer Netzwerk-/Internetbetrieb freigegeben. |
| Wartbarkeit | Deutlich verbessert durch kleine Module, atomare Grenzen, Typpruefung, CI, paketierte Ressourcen und aktuelle Dokumentation. |
| Erweiterbarkeit | Gut innerhalb des lokalen Reportingmodells; Hosting, Inventar und FX benoetigen bewusste neue Architektur-/Fachentscheidungen. |
| Performance | Sehr gut fuer 21.172 Raw-Zeilen und 5.298 Standard-Fakten; kein Cache oder DB-Wechsel erforderlich. |
| Testbarkeit | Hoch fuer kritische Import-/Datenlogik und Webpfade; privater Vollbestand wird zusaetzlich separat end-to-end geprueft. |
| Produktionsreife | Einsatzbereit als lokaler Einzelplatz-MVP. Nicht produktionsreif als gehostetes Mehrbenutzer- oder Buchhaltungssystem. |

**Gesamturteil:** Der lokale MVP ist nach den Korrekturen praktisch einsetzbar und
implementierungsseitig belastbar. Die verbleibenden Punkte sind dokumentierte Produkt- oder
Betriebsentscheidungen, keine verdeckten defekten Kernfunktionen.
