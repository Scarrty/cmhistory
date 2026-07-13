# FABLE.md — Repo-Analyse: Fehler, Probleme und Verbesserungsvorschläge

> **AI-/Best-Effort-Hinweis:** Dieses Projekt und dieses Review wurden zu 100 % mit KI
> generiert. Keine Gewaehr; siehe [NOTICE.md](NOTICE.md).

Vollständige Analyse des Repositories `Scarrty/cmhistory` (Cardmarket History Dashboard).
Diese Datei ist das Arbeitsdokument für die Umsetzung: Jeder Befund enthält Fundstelle,
Beleg/Reproduktion, konkreten Fix-Vorschlag und Akzeptanzkriterien, sodass ein Mensch oder
ein anderes System die Änderungen ohne erneute Analyse durchführen kann.

- **Stand:** 2026-07-12, Commit `eaf1d55` (main), Branch `claude/repo-analysis-fable-lpd3fj`
- **Analyseumfang:** alle 87 versionierten Dateien (Quellcode, Migrationen, Templates,
  Statics, Tests, Skripte, CI, Dokumentation)
- **Verifikation:** Toolchain wurde real ausgeführt (Python 3.12-venv):
  - `ruff check src tests scripts` → **bestanden, 0 Findings**
  - `mypy` → **bestanden, 0 Findings (23 Dateien)**
  - `pytest -q` → **4 failed, 78 passed, 34 skipped** (siehe P0-1)
  - `python -m build` + `scripts/verify_distribution.py` → **bestanden**
  - GitHub Actions Run #1 auf `main` (ID 29192088008) → **failure**, identische 4 Tests

## Schweregrade

| Stufe | Bedeutung |
|---|---|
| **P0** | Blockierend: CI rot / falsche Kernaussage der Doku |
| **P1** | Datenkorrektheit oder falsches Verhalten mit realem Nutzer-Impact |
| **P2** | Robustheit, Wartbarkeit, Betriebssicherheit |
| **P3** | Stil, Doku, Kleinigkeiten |

## Umsetzungsstand (2026-07-12)

Alle Befunde sind auf diesem Branch umgesetzt; die Detailabschnitte unten dokumentieren
weiterhin Analyse und Begründung. Die drei zunächst offenen Punkte wurden am 2026-07-12 per
Maintainer-Interview entschieden und anschließend umgesetzt:

- **P2-16** (Coverage-Warnungen): Entscheidung **Quittierungsdatei**. Bekannte Lücken werden
  über Fingerprints in `accepted_issues.json` neben der Datenbank quittiert; `validate` gibt
  die Fingerprints aus, quittierte Lücken werden zu einer Info-Zeile
  (`accepted_period_coverage_summary`) zusammengefasst. Die Datei überlebt einen `rebuild`.
- **P3-2** (CSV-Report): Entscheidung **`net_total` ergänzen** (kein Breaking Change).
  `total` bleibt Bruttovolumen; neue Spalte `net_total` = Verkäufe − Käufe (Periodenzeile)
  bzw. vorzeichenbehaftet je Richtung (Monatszeilen). Semantik in der README dokumentiert.
- **P3-5** (Lizenz): Entscheidung **MIT**. `LICENSE`-Datei plus `license`/`license-files`
  in `pyproject.toml` (Build-Backend auf `setuptools>=77` angehoben für SPDX-Metadaten).

Wichtig für den Betrieb: P1-1 und P2-4 ändern normalisierte Fakten —
`NORMALIZATION_VERSION` wurde auf 3 erhöht. Bestehende Datenbanken verlangen nach dem
Update einen einmaligen expliziten `rebuild` (CLI und Web zeigen das an).

## Übersicht aller Befunde

| ID | Stufe | Bereich | Kurzbeschreibung | Status |
|---|---|---|---|---|
| P0-1 | P0 | Tests/CI | 4 Tests erfordern private Quelldaten und schlagen ohne sie fehl → CI auf main ist rot | ✅ umgesetzt |
| P0-2 | P0 | Doku | README-Behauptung „CI läuft ohne private Exporte" ist aktuell falsch | ✅ umgesetzt |
| P1-1 | P1 | Import | CSV-Reader zerstört Zeilenumbrüche in quoted Feldern → Dedup CSV/XLS kann versagen | ✅ umgesetzt |
| P1-2 | P1 | Web/Import | Modulimport der Web-App erzeugt/migriert die Datenbank als Seiteneffekt | ✅ umgesetzt |
| P1-3 | P1 | Konfiguration | `PROJECT_ROOT` zeigt bei installiertem Wheel in die Python-Installation | ✅ umgesetzt |
| P1-4 | P1 | Reporting | Sendungen werden lexikografisch statt numerisch nach Order-ID sortiert | ✅ umgesetzt |
| P1-5 | P1 | Import | `_pad_row` schneidet überzählige Zellen stumm ab (stiller Datenverlust) | ✅ umgesetzt |
| P2-1 | P2 | CLI | `validate` liefert Exit-Code 0 auch bei error-Issues | ✅ umgesetzt |
| P2-2 | P2 | CLI | `rebuild` ohne Fehlerbehandlung → nackter Traceback | ✅ umgesetzt |
| P2-3 | P2 | DB | Migrationsausführung nicht atomar; Re-Run von 002 zerstört den Startvorgang | ✅ umgesetzt |
| P2-4 | P2 | Import | `normalize_bool` liefert `False` statt `None` bei leerem Wert | ✅ umgesetzt |
| P2-5 | P2 | Web | `typing._eval_type`-Monkey-Patch (Python-3.14-Workaround) ist fragil und dupliziert | ✅ umgesetzt (isoliert in `_compat.py`) |
| P2-6 | P2 | Web | DB-Pfad der Web-App ist nicht konfigurierbar (kein env var, kein Factory-Start) | ✅ umgesetzt |
| P2-7 | P2 | Import | Fortsetzungszeilen vor dem ersten Header werden still verworfen (kein Issue) | ✅ umgesetzt |
| P2-8 | P2 | CI | Doppelte CI-Läufe (push+pull_request), veraltete Action-Versionen (Node-20-Warnung) | ✅ umgesetzt |
| P2-9 | P2 | Tests | mypy prüft `tests/` nicht (`files = ["src", "scripts"]`) | ✅ umgesetzt |
| P2-10 | P2 | Betrieb | `.gitignore` deckt Rebuild-Tempdateien (`.cardmarket.db.*.rebuild`) nicht ab | ✅ umgesetzt |
| P2-11 | P2 | Skripte | `verify_mvp.ps1` leert `dist/` nicht → Verifier bricht nach Versionsbump | ✅ umgesetzt |
| P2-12 | P2 | DB | Kein Index auf `article_lines.shipment_id` | ✅ umgesetzt (Migration 004) |
| P2-13 | P2 | Web | `allowed_hosts` enthält `testserver` in der Produktionskonfiguration | ✅ umgesetzt |
| P2-14 | P2 | Web | `assert` im Request-Pfad (`shipment_detail`) entfällt unter `python -O` | ✅ umgesetzt |
| P2-15 | P2 | Import | `imported_at` wird beim Überschreiben mit Status `failed` nicht zurückgesetzt | ✅ umgesetzt |
| P2-16 | P2 | Validierung | `missing_period_coverage`-Warnungen sind nicht quittierbar → Dauerrauschen | ✅ umgesetzt (Quittierungsdatei) |
| P3-1 | P3 | Stil | Fehlerhafte Einrückung der schließenden Klammer in `store_raw_article_rows` | ✅ umgesetzt |
| P3-2 | P3 | Doku | Semantik von `combined_total` (Käufe+Verkäufe addiert) klären/umbenennen | ✅ umgesetzt (dokumentiert + `net_total`) |
| P3-3 | P3 | Doku | Dezimal-Heuristik `"1.234"` (Punkt als Tausendertrenner) dokumentieren | ✅ umgesetzt |
| P3-4 | P3 | Tests | `synthetic_sources` schreibt CSV-Inhalt unabhängig von der Dateiendung | ✅ umgesetzt |
| P3-5 | P3 | Repo | Keine LICENSE-Datei / kein `license`-Feld in `pyproject.toml` | ✅ umgesetzt (MIT) |
| P3-6 | P3 | Web | Kein `/favicon.ico` → 404 bei jedem Browseraufruf | ✅ umgesetzt |

---

## P0 — Blockierend

### P0-1: CI auf main ist rot — 4 Tests setzen private Quelldaten voraus

**Problem:** Vier Tests arbeiten direkt auf `source_root()` (Projektwurzel bzw.
`CM_DASHBOARD_SOURCE_ROOT`) und asserten das private Inventar von 447 Exportdateien.
Ohne die privaten Dateien (CI, frischer Clone) schlagen sie hart fehl, statt zu skippen:

| Test | Fundstelle | Assert |
|---|---|---|
| `test_scan_current_source_folder_matches_review_inventory` | `tests/test_source_scan.py:48` | `len(report.files) == 447` |
| `test_validate_source_folder_reports_known_missing_coverage_examples` | `tests/test_import_validation.py:15` | konkrete Coverage-Lücken im Privatbestand |
| `test_persist_validation_issues_stores_issues` | `tests/test_import_validation.py:51` | `stored_count == 3` (braucht ≥3 echte Issues) |
| `test_shipment_group_counts_match_review_evidence` | `tests/test_shipment_grouping.py:41` | Zeilen-/Header-Zählungen des Privatbestands |

**Beleg:** GitHub Actions Run 29192088008 (`main`, 2026-07-12): `4 failed, 78 passed,
34 skipped`, Job „verify" endet mit Exit-Code 1 im Schritt „Test". Lokal ohne
Quelldaten identisch reproduziert. Die nachfolgenden CI-Schritte (Build,
Distribution-Check) laufen dadurch nie; lokal manuell verifiziert, dass sie bestehen
würden.

**Hinweis:** Das Repo kennt das Muster bereits: `tests/test_full_source_smoke.py:11`
nutzt `@pytest.mark.skipif(os.environ.get("CM_DASHBOARD_RUN_FULL_SOURCE_TESTS") != "1", ...)`
und die Fixture-Tests skippen über `require_fixture_path()` (`tests/fixtures.py:86`).
Nur die vier obigen Tests haben keinen Guard.

**Fix-Vorschlag:**
1. Gemeinsamen Guard einführen, z. B. in `tests/fixtures.py`:
   ```python
   requires_full_source = pytest.mark.skipif(
       os.environ.get("CM_DASHBOARD_RUN_FULL_SOURCE_TESTS") != "1",
       reason="Set CM_DASHBOARD_RUN_FULL_SOURCE_TESTS=1 to run tests against the private full source folder.",
   )
   ```
   und auf die drei Inventar-Tests anwenden (`test_source_scan.py:48`,
   `test_import_validation.py:15`, `test_shipment_grouping.py:41`).
   Alternativ ein dynamischer Skip, wenn `scan_source_files(source_root()).files` leer ist —
   der env-Gate ist aber deterministischer und konsistent mit dem Smoke-Test.
2. `test_persist_validation_issues_stores_issues` (`tests/test_import_validation.py:51`)
   von den Privatdaten entkoppeln: statt `validate_source_folder(source_root(), ...)`
   drei synthetische `ValidationIssue`-Objekte direkt konstruieren (oder eine
   synthetische Quelle über `tests/synthetic_sources.py` bauen). Der Test prüft nur
   `persist_validation_issues`, dafür sind keine echten Quelldateien nötig.

**Akzeptanzkriterien:**
- `pytest -q` besteht in einer Umgebung ohne private Exporte (0 failed; die vier Tests
  erscheinen als skipped bzw. laufen synthetisch).
- Mit `CM_DASHBOARD_RUN_FULL_SOURCE_TESTS=1` und vorhandenem Privatbestand laufen die
  Inventar-Tests weiterhin unverändert.
- GitHub Actions auf main wird grün (inkl. der bisher nie erreichten Schritte Build +
  `verify_distribution.py`).

**Aufwand:** S (unter 1 Stunde)

### P0-2: README-Behauptung zur CI ist aktuell falsch

**Problem:** `README.md:132-133` behauptet: „GitHub Actions führt für Python 3.12
Linting, Typprüfung, Tests, Dependency-Audit und Distributionsprüfung ohne Zugriff auf
private Exporte aus." Tatsächlich ist der einzige CI-Lauf rot (siehe P0-1) und
Build/Distribution wurden in CI noch nie ausgeführt.

**Fix-Vorschlag:** Ergibt sich aus P0-1. Nach dem Fix Satz beibehalten; optional
ergänzen, dass Vollbestands-Tests nur mit `CM_DASHBOARD_RUN_FULL_SOURCE_TESTS=1` laufen
(analog `docs/architecture.md:110` „optionalen privaten Vollbestandsfixtures").

**Akzeptanzkriterien:** README-Aussage stimmt mit einem grünen CI-Lauf überein.

**Aufwand:** S (Teil von P0-1)

---

## P1 — Datenkorrektheit / falsches Verhalten

### P1-1: CSV-Reader zerstört Zeilenumbrüche in quoted Feldern

**Problem:** `src/cm_dashboard/importing/readers.py:63` parst CSV über
`csv.reader(text.splitlines(), ...)`. `splitlines()` entfernt die Newline-Zeichen,
bevor `csv.reader` mehrzeilige quoted Felder wieder zusammensetzen kann. Ein Feld
`"line1\nline2"` wird dadurch still zu `line1line2` (reproduziert und verifiziert).

**Impact:**
1. Stiller Datenverlust in Freitextfeldern (v. a. `Comments`).
2. Kritischer Folgefehler: Der Artikel-Business-Key
   (`importing/deduplication.py:87`, Feld `comments`) unterscheidet sich dann zwischen
   der CSV- und der XLS-Version derselben Geschäftszeile (XLS behält den Umbruch, CSV
   verliert ihn). Die CSV/XLS-Deduplizierung — ein Kernfeature laut README und
   `docs/architecture.md:53-55` — versagt für solche Zeilen, und dieselbe physische
   Position wird **doppelt gezählt**.

**Reproduktion:**
```python
from cm_dashboard.importing.readers import _read_csv
p.write_text('A;B\n"line1\nline2";x\n', encoding="utf-8")
_read_csv(p).rows  # → (('line1line2', 'x'),)  — Umbruch verloren
```

**Fix-Vorschlag:** In `_read_csv` (`readers.py:59`) das Parsen auf einen
newline-erhaltenden Iterator umstellen, z. B.:
```python
reader = csv.reader(io.StringIO(text), delimiter=delimiter)
```
(`io.StringIO` liefert Zeilen inklusive `\n`, `csv.reader` setzt quoted Mehrzeiler
dann korrekt zusammen.) `_read_csv_text` kann unverändert bleiben; alternativ die Datei
mit `open(path, newline="", encoding=...)` direkt an `csv.reader` geben (dann Encoding-
Fallback-Logik beibehalten). `_detect_csv_delimiter`-Aufruf bleibt gleich.

**Test:** Neuen Regressionstest in `tests/test_readers.py` ergänzen: quoted Feld mit
eingebettetem `\n` (und `\r\n`) bleibt inhaltlich erhalten; Zeilenzahl stimmt.
Zusätzlich einen Dedup-Test: CSV-Zeile mit mehrzeiligem Kommentar erzeugt denselben
Business-Key wie die entsprechende Dict-Row mit echtem Umbruch.

**Achtung Folgewirkung:** Die Fix-Änderung verändert normalisierte Fakten für
Bestandsdaten mit mehrzeiligen Kommentaren → `NORMALIZATION_VERSION`
(`importing/version.py:3`) auf `3` erhöhen, damit bestehende Datenbanken einen
expliziten `rebuild` verlangen (der Mechanismus dafür existiert bereits in
`pipeline.py:245-262`).

**Akzeptanzkriterien:** Neue Tests grün; bestehende Dedup-Tests
(`tests/test_deduplication.py`) unverändert grün; `NORMALIZATION_VERSION` erhöht.

**Aufwand:** S–M

### P1-2: Modulimport der Web-App erzeugt/migriert die Datenbank als Seiteneffekt

**Problem:** `src/cm_dashboard/web/app.py:397` führt auf Modulebene `app = create_app()`
aus; `create_app` ruft `create_database(...)` (`web/app.py:140`) und legt damit beim
bloßen Import des Moduls `data/cardmarket.db` am Default-Pfad an (inkl. Migrationen).
Verstärkt wird das durch `tests/conftest.py:3`, das `cm_dashboard.web.app` nur für den
typing-Patch importiert.

**Beleg:** Ein `pytest`-Lauf in diesem Audit hat ohne jede DB-bezogene Aktion eine
168-KB-Datei `data/cardmarket.db` im Repository-Root erzeugt (gitignored, aber
unerwünscht: Tests schreiben in den echten Projektordner; jedes Tool, das das Modul
importiert, legt eine Datenbank an).

**Fix-Vorschlag:**
1. Modulebenen-Instanz entfernen oder lazy machen. Empfohlen: Factory-Start
   dokumentieren — `uvicorn --factory cm_dashboard.web.app:create_app` — und die Zeile
   `app = create_app()` streichen (README:71, `docs/monthly_import.md:109` anpassen).
   Falls Kompatibilität zum bisherigen Startbefehl gewünscht ist: DB-Erzeugung aus
   `create_app` in einen FastAPI-Lifespan-Handler verschieben, sodass der Import keine
   Dateien anlegt.
2. `_patch_python314_typing_for_pydantic` in ein eigenes Modul (z. B.
   `cm_dashboard/_compat.py`) verschieben, damit `tests/conftest.py` nicht die ganze
   Web-App importieren muss (siehe auch P2-5).

**Akzeptanzkriterien:** `python -c "import cm_dashboard.web.app"` und ein kompletter
`pytest`-Lauf erzeugen keine Datei außerhalb von `tmp_path`; Webserver-Start laut
README funktioniert weiterhin.

**Aufwand:** M

### P1-3: `PROJECT_ROOT` zeigt bei installiertem Wheel in die Python-Installation

**Problem:** `src/cm_dashboard/config.py:6` bestimmt
`PROJECT_ROOT = Path(__file__).resolve().parents[2]`. Das funktioniert nur im
src-Layout (editierbare Installation). Bei einer regulären Wheel-Installation ist
`parents[2]` das `lib/python3.12`-Verzeichnis; `DEFAULT_DATABASE_PATH` und
`DEFAULT_SOURCE_PATH` zeigen dann in die Python-Installation. Das Projekt baut und
verifiziert Wheels (CI-Schritt, `verify_distribution.py`) — der Widerspruch ist real.

**Fix-Vorschlag:** Defaults vom Installationsort entkoppeln:
- `DEFAULT_SOURCE_PATH = Path.cwd()` und `DEFAULT_DATABASE_PATH = Path.cwd() / "data" / "cardmarket.db"`,
  jeweils überschreibbar per Umgebungsvariablen (`CM_DASHBOARD_SOURCE`,
  `CM_DASHBOARD_DB`) in `load_settings` (`config.py:28`).
- `tests/fixtures.py:70` (`source_root()`) nutzt `PROJECT_ROOT` als Fallback — dort auf
  `Path.cwd()` oder explizit auf den Repo-Root via `Path(__file__).parents[1]` der
  Testdatei umstellen, damit das Testverhalten unverändert bleibt.

**Achtung:** Wechsel auf `Path.cwd()` ändert das Verhalten der dokumentierten
PowerShell-Befehle nicht (die werden laut README/Docs immer aus dem Projektordner
aufgerufen), muss aber in README („Erster Datenbankaufbau") kurz erwähnt werden.

**Akzeptanzkriterien:** In einem frischen venv `pip install dist/*.whl` +
`python -m cm_dashboard.cli validate --db <pfad>` funktioniert; kein Pfad zeigt in
site-packages; bestehende Tests grün.

**Aufwand:** M

### P1-4: Sendungen werden lexikografisch statt numerisch sortiert

**Problem:** `src/cm_dashboard/reporting/queries.py:140`
(`ORDER BY shipments.order_id DESC, ...`) sortiert die TEXT-Spalte `order_id`
lexikografisch: `"999999" > "10000000"`. Über 10 Jahre Datenhistorie wachsen
Cardmarket-Order-IDs über Stellengrenzen — der Sendungsexplorer zeigt „neueste zuerst"
damit falsch.

**Fix-Vorschlag (eine der Varianten):**
- `ORDER BY CAST(shipments.order_id AS INTEGER) DESC, shipments.order_id DESC,
  shipments.shipment_id DESC` (CAST liefert 0 für nicht-numerische IDs, der
  Text-Tiebreaker hält die Ordnung stabil), oder
- fachlich sauberer: nach neuestem Eventdatum sortieren
  (`MAX(shipment_events.event_datetime)` via Subquery/`GROUP BY`), was auch Sendungen
  ohne numerische ID korrekt einordnet.

**Test:** In `tests/test_shipments_page.py` bzw. `tests/test_reporting_queries.py`
Fixture mit Order-IDs `999`, `1000`, `10000` → erwartete Reihenfolge `10000, 1000, 999`.

**Akzeptanzkriterien:** Neue Sortier-Tests grün; Pagination weiterhin stabil
(deterministischer Tiebreaker vorhanden).

**Aufwand:** S

### P1-5: `_pad_row` schneidet überzählige Zellen stumm ab

**Problem:** `src/cm_dashboard/importing/readers.py:103-106` kürzt Zeilen, die mehr
Zellen als der Header haben, kommentarlos auf Headerlänge (`values[:expected_length]`).
Eine fehlerhafte Quelldatei (z. B. unquoted Semikolon in einem Textfeld) verliert damit
still Daten, statt als Fehler/Warnung sichtbar zu werden — im Widerspruch zur
Projektphilosophie „Vollständige Rohzeilen-Nachvollziehbarkeit" (`docs/architecture.md:14`).

**Fix-Vorschlag:** In `_read_csv`/`_read_excel` überlange Zeilen erkennen und
`ValueError` mit Zeilennummer werfen (der Datei-Import wird dann regulär als `failed`
mit `import_failed`-Issue gespeichert, Mechanismus existiert in `pipeline.py:153-165`).
Alternativ weicher: Issue `row_width_mismatch` als Warnung aufnehmen und Daten in
`raw_values_json` unter einem Sammelschlüssel erhalten. Empfehlung: harter Fehler —
die Headervalidierung (`schemas.py:101`) ist ohnehin strikt.

**Akzeptanzkriterien:** Test: CSV-Zeile mit einer Zelle zu viel führt zu `failed`-Import
mit aussagekräftiger Meldung statt stillem Import; bestehende Tests grün.

**Aufwand:** S

---

## P2 — Robustheit / Wartbarkeit / Betrieb

### P2-1: `validate` liefert Exit-Code 0 auch bei Fehlern

**Problem:** `src/cm_dashboard/cli.py:86-96` gibt Issues aus, returned aber immer 0.
`scripts/verify_mvp.ps1:59-61` prüft `$LASTEXITCODE` — error-Issues (z. B.
`import_failed`, `source_file_changed`) werden von der Automatisierung übersehen.
`docs/monthly_import.md:84-90` listet explizit „Nicht akzeptieren"-Codes.

**Fix-Vorschlag:** `return 1 if any(issue.severity == "error" for issue in issues) else 0`.
Optional `--strict`-Flag, das auch Warnungen fehlschlagen lässt.

**Akzeptanzkriterien:** CLI-Test in `tests/test_cli.py`: DB mit error-Issue → Exit 1;
ohne → Exit 0. `verify_mvp.ps1` schlägt bei error-Issues fehl.

**Aufwand:** S

### P2-2: `rebuild` ohne Fehlerbehandlung

**Problem:** `src/cm_dashboard/cli.py:79-84`: `ImportBatchError` (fehlgeschlagene
Dateien oder Integritätsfehler, `pipeline.py:225-233`) erreicht den Nutzer als
Traceback. Zudem gehen die Detailinformationen (welche Dateien scheiterten, welche
Fehlermeldungen) verloren, weil die Exception nur die Anzahl enthält.

**Fix-Vorschlag:** In `cli.py` analog zum `import`-Zweig `try/except ImportPipelineError`
mit `print(f"error: {exc}")` und Exit-Code 2. Zusätzlich in
`rebuild_database` (`pipeline.py:225-229`) die fehlgeschlagenen `ImportResult`s in die
Exception aufnehmen (z. B. Attribut `failed_results`) und im CLI je Datei
`error: <datei>: <meldung>` ausgeben — dieselbe UX wie beim `import`-Befehl
(`cli.py:74-76`).

**Akzeptanzkriterien:** CLI-Test: rebuild mit defekter Quelldatei → Exit ≠ 0, lesbare
Fehlermeldung(en) pro Datei, kein Traceback, Alt-DB unverändert.

**Aufwand:** S

### P2-3: Migrationsausführung nicht atomar; Re-Run von 002 bricht den Start

**Problem:** `src/cm_dashboard/db.py:52-57` führt jede Migration via
`connection.executescript(...)` innerhalb `with connection:` aus. `executescript`
committet jedoch implizit jede offene Transaktion, bevor es läuft — der Kontextmanager
schützt also nicht. Crasht der Prozess zwischen Skriptende und dem
`INSERT INTO schema_migrations`, gilt die Migration als nicht angewendet und läuft beim
nächsten Start erneut. Für `002_import_normalization_version.sql` (ALTER TABLE ADD
COLUMN) bedeutet ein Re-Run `duplicate column name` → die Datenbank ist ohne manuellen
Eingriff nicht mehr startbar. (003 bringt eigenes BEGIN/COMMIT mit und wäre zufällig
re-run-fähig; 001 ist durch `IF NOT EXISTS` idempotent.)

**Fix-Vorschlag (Varianten, eine reicht):**
1. Migrationen defensiv idempotent machen: In `apply_migrations` vor dem Ausführen die
   Ziel-Änderung prüfen ist unpraktisch — besser: Migrationsdateien so schreiben, dass
   sie ihren eigenen `INSERT INTO schema_migrations (migration_id) VALUES ('...');`
   als letztes Statement im selben Skript (und für neue Migrationen innerhalb
   `BEGIN IMMEDIATE`/`COMMIT`) enthalten; `apply_migrations` führt dann nur noch aus.
2. Oder: `executescript` ersetzen — Skript an `;`-Statements splitten und über
   `connection.execute` einzeln innerhalb einer echten Transaktion ausführen (Vorsicht
   bei `BEGIN/COMMIT` in 003: für Bestands-DBs Sonderfall behandeln).
3. Minimalvariante: 002 in `ALTER TABLE ... ADD COLUMN` mit vorheriger Prüfung via
   `PRAGMA table_info(import_files)` in Python kapseln.

Empfehlung: Variante 1 für neue Migrationen als Konvention dokumentieren
(`docs/architecture.md`), plus Variante 3 als Absicherung für 002.

**Akzeptanzkriterien:** Test: `apply_migrations` zweimal hintereinander auf einer DB,
bei der `schema_migrations`-Einträge künstlich entfernt wurden, wirft keinen Fehler
bzw. erkennt den Zustand sauber. Frische DB + Bestands-DB (Version 1→3) migrieren
weiter korrekt (bestehender Test `tests/test_schema.py` bleibt grün).

**Aufwand:** M

### P2-4: `normalize_bool` liefert `False` statt `None` bei leerem Wert

**Problem:** `src/cm_dashboard/importing/normalize.py:109-111`: Signatur ist
`bool | None`, aber `is_empty(value)` → `return False`. Damit ist „Feld leer /
unbekannt" nicht von „explizit nein" unterscheidbar; `shipments.is_professional`
(`shipment_import.py:89`) speichert für leere Quellwerte `0` statt `NULL`, obwohl
Schema und `_bool_to_int` (`shipment_import.py:162`) NULL vorsehen.

**Fix-Vorschlag:** `return None` bei leer. Aufrufer prüfen: einziger Nutzer ist
`shipment_import.py:89`; `_bool_to_int(None) → None` funktioniert bereits. Test in
`tests/test_normalize.py` anpassen/ergänzen (aktuell wird dort vermutlich `False`
erwartet — bewusst umstellen).

**Achtung:** ändert normalisierte Fakten → wie bei P1-1 `NORMALIZATION_VERSION`
erhöhen (kann mit P1-1 in einem Versionssprung gebündelt werden).

**Akzeptanzkriterien:** leerer Wert → `NULL` in `shipments.is_professional`; `"x"`,
`"yes"`, `"no"` etc. unverändert; Version erhöht.

**Aufwand:** S

### P2-5: `typing._eval_type`-Monkey-Patch ist fragil und dupliziert

**Problem:** `src/cm_dashboard/web/app.py:20-35` patcht das stdlib-Modul `typing`
prozessweit, um eine pydantic-Inkompatibilität mit einer lokalen Python-3.14-Vorabversion
zu umgehen (Kontext: `OUTPUT/PROJECT_AUDIT_AND_OPTIMIZATION.md`, Zeile „lokale
Vorabversion benoetigt einen Kompatibilitaets-Workaround"). Der Patch liegt in der
Web-App und wird von `tests/conftest.py:3-5` erneut aufgerufen; `pyproject.toml`
verlangt nur `>=3.12`. Mit aktuellen Versionen (pydantic 2.13.x, fastapi 0.139) ist er
voraussichtlich obsolet.

**Fix-Vorschlag:**
1. Prüfen, ob der Patch mit den aktuell aufgelösten Versionen noch nötig ist
   (Python 3.14 final + pydantic ≥ 2.13): Web-Tests ohne Patch auf 3.12/3.13/3.14 laufen
   lassen.
2. Wenn nötig: in eigenes Modul `cm_dashboard/_compat.py` mit klarer
   Versionsbedingung (`sys.version_info`) verschieben; `web/app.py` und `conftest.py`
   importieren von dort (löst auch den Import-Seiteneffekt aus P1-2).
3. Wenn unnötig: Patch und conftest-Aufruf ersatzlos entfernen.

**Akzeptanzkriterien:** Web-Tests grün auf unterstützten Python-Versionen; kein
stdlib-Patch mehr in `web/app.py` bzw. sauber isoliert.

**Aufwand:** S–M

### P2-6: DB-Pfad der Web-App nicht konfigurierbar

**Problem:** Der dokumentierte Start (`uvicorn cm_dashboard.web.app:app`, README:71)
nutzt zwangsweise `DEFAULT_DATABASE_PATH`. `create_app(database_path=...)` existiert
(`web/app.py:132`), ist aber über die Kommandozeile nicht erreichbar. Zusammen mit
P1-3 heißt das: installierte Nutzung ist faktisch nicht konfigurierbar.

**Fix-Vorschlag:** `load_settings` (`config.py:28`) liest `CM_DASHBOARD_DB` /
`CM_DASHBOARD_SOURCE` aus `os.environ` als Fallback vor den Defaults. README/Docs um
ein Beispiel ergänzen. (Deckt sich mit P1-3; zusammen umsetzen.)

**Akzeptanzkriterien:** `CM_DASHBOARD_DB=/pfad/zur.db uvicorn ...` bedient die genannte
DB; Test über `load_settings` mit monkeypatched env.

**Aufwand:** S

### P2-7: Fortsetzungszeilen vor dem ersten Header werden still verworfen

**Problem:** `src/cm_dashboard/importing/shipment_grouping.py:24-53`: Beginnt ein
Shipment-Sheet mit einer Zeile ohne `OrderID` (Fortsetzung ohne vorausgehenden Header),
wird `resolved_order_id=None` gesetzt; `import_shipment_sheet`
(`shipment_import.py:32-34`) überspringt solche Zeilen kommentarlos. Die Rohzeile bleibt
zwar erhalten, aber es gibt kein `import_issue` — stiller Faktenverlust bei defekten
Exporten.

**Fix-Vorschlag:** In `import_shipment_sheet` nach dem Durchlauf Zeilen mit
`resolved_order_id IS NULL` zählen (bzw. in `resolve_shipment_groups` markieren) und
als Warnung `orphan_shipment_row` mit `source_row_number` in `import_issues` schreiben.

**Akzeptanzkriterien:** Test: synthetisches Shipment-CSV, erste Datenzeile ohne OrderID
→ Import erfolgreich, Warnung mit Zeilennummer vorhanden.

**Aufwand:** S

### P2-8: CI-Konfiguration: Doppelläufe und veraltete Actions

**Problem:** `.github/workflows/ci.yml:3-5` triggert auf `push` **und** `pull_request`
ohne Branch-Filter → jeder PR-Branch läuft doppelt. Die Run-Logs warnen zudem:
„actions/checkout@v4, actions/setup-python@v5 … target Node.js 20 … deprecated".

**Fix-Vorschlag:**
```yaml
on:
  push:
    branches: [main]
  pull_request:
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
```
und Actions auf die aktuellen Major-Versionen heben (`actions/checkout@v5`,
`actions/setup-python@v6`; beim Umsetzen die dann aktuellen Versionen verwenden).

**Akzeptanzkriterien:** Ein Lauf pro Ereignis; keine Node-Deprecation-Warnung im Log.

**Aufwand:** S

### P2-9: mypy prüft `tests/` nicht

**Problem:** `pyproject.toml:52` — `files = ["src", "scripts"]`. Typfehler in Tests
bleiben unentdeckt, z. B. `tests/test_deduplication.py:107`
(`WorksheetData(path="synthetic.csv", ...)` — `str` statt `Path`).

**Fix-Vorschlag:** `files = ["src", "scripts", "tests"]`; gefundene Testtypfehler
beheben (erwartbar wenige; der genannte: `Path("synthetic.csv")`).

**Akzeptanzkriterien:** `mypy` grün über alle drei Verzeichnisse; CI unverändert grün.

**Aufwand:** S

### P2-10: `.gitignore` deckt Rebuild-Tempdateien nicht ab

**Problem:** `pipeline.py:220` erzeugt `data/.cardmarket.db.<hex>.rebuild`. Bei einem
harten Prozessabbruch (kill, Stromausfall) bleibt die Datei liegen; `.gitignore:6-9`
matcht sie nicht (`data/*.db`, `data/*.db-*` greifen nicht wegen des `.rebuild`-Suffix).

**Fix-Vorschlag:** `.gitignore` um `data/.*.rebuild` (oder `data/*.rebuild`) ergänzen.
Optional: `rebuild_database` räumt beim Start verwaiste `*.rebuild`-Dateien im
Zielordner auf.

**Akzeptanzkriterien:** Tempdatei-Muster wird von `git status` ignoriert.

**Aufwand:** S

### P2-11: `verify_mvp.ps1` bricht nach Versionsbump am Distribution-Check

**Problem:** `scripts/verify_distribution.py:22-25` verlangt **genau ein** Wheel in
`dist/`; `scripts/verify_mvp.ps1:45-46` baut ohne `dist/` vorher zu leeren. Nach einer
Versionserhöhung liegen zwei Wheels vor → RuntimeError, obwohl alles in Ordnung ist.

**Fix-Vorschlag:** In `verify_mvp.ps1` vor dem Build `Remove-Item dist -Recurse -Force
-ErrorAction SilentlyContinue` (bzw. in frisches Temp-Outdir bauen). Alternativ nimmt
`verify_distribution.py` das neueste Wheel (`max(..., key=mtime)`) statt Exakt-1.

**Akzeptanzkriterien:** Zwei Wheels in `dist/` brechen den Skriptlauf nicht mehr bzw.
werden vorher entfernt.

**Aufwand:** S

### P2-12: Kein Index auf `article_lines.shipment_id`

**Problem:** `migrations/001_init.sql` / `003_...sql` definieren Indizes für Filter-
und Order-Spalten, aber keinen auf `article_lines.shipment_id`. Genutzt wird die Spalte
von `fetch_shipment_articles` (`reporting/queries.py:233`), den
`link_status`-EXISTS-Filtern (`queries.py:391-400`) und dem Link-Update
(`article_import.py:65-82`). Bei ~10–20k Zeilen unkritisch, aber jeder
Sendungsdetail-Aufruf macht einen Full Scan.

**Fix-Vorschlag:** Neue Migration `004_article_lines_shipment_index.sql`:
`CREATE INDEX IF NOT EXISTS idx_article_lines_shipment_id ON article_lines(shipment_id);`

**Akzeptanzkriterien:** Migration läuft auf frischer und bestehender DB;
`tests/test_schema.py` um Indexprüfung ergänzt.

**Aufwand:** S

### P2-13: `allowed_hosts` enthält `testserver` in Produktion

**Problem:** `web/app.py:142-145` — die TrustedHost-Liste enthält `testserver`
(Starlette-TestClient-Host) auch im Normalbetrieb. Risiko ist bei einer
localhost-only-App gering, aber die Produktionskonfiguration sollte keine
Test-Artefakte enthalten.

**Fix-Vorschlag:** `create_app(..., testing: bool = False)`-Parameter oder Host-Liste
als Argument; Tests übergeben `testserver` explizit. Minimalvariante: Kommentar +
bewusste Entscheidung dokumentieren.

**Akzeptanzkriterien:** Normalstart akzeptiert nur `127.0.0.1`, `localhost`, `[::1]`;
Web-Tests weiter grün.

**Aufwand:** S

### P2-14: `assert` im Request-Pfad

**Problem:** `web/app.py:365` — `assert validated_date_basis is not None`. Unter
`python -O` werden asserts entfernt; die Invariante hängt dann nur an
`_validated_choice`-Interna.

**Fix-Vorschlag:** Assert ersetzen: `_validated_choice` in einer Variante nutzen, die
`str` (nicht `str | None`) zurückgibt, wenn `default` gesetzt ist — z. B. kleine
Hilfsfunktion `_validated_choice_with_default(...) -> str`. Kein Laufzeit-Assert nötig.

**Akzeptanzkriterien:** mypy weiterhin grün ohne assert; Verhalten unverändert.

**Aufwand:** S

### P2-15: `imported_at` bleibt beim Statuswechsel auf `failed` stehen

**Problem:** `raw_store.upsert_import_file` (`raw_store.py:50-62`) aktualisiert beim
ON CONFLICT alle Felder außer `imported_at`. Wechselt eine Datei von `imported` zu
`failed` (Fehlversuch nach vorherigem Erfolg ist über den geänderten-Inhalt-Pfad zwar
abgefangen, aber `failed`→`failed`-Retries und künftige Pfade bleiben), zeigt die
Import-Seite einen veralteten Zeitstempel zu einem fehlgeschlagenen Status.

**Fix-Vorschlag:** Im UPDATE-Zweig `imported_at = CASE WHEN excluded.import_status =
'imported' THEN import_files.imported_at ELSE NULL END` — oder schlicht `imported_at`
nur im Erfolgs-UPDATE (`pipeline.py:142-150`) pflegen und beim Upsert auf `NULL`
setzen, wenn Status ≠ imported.

**Akzeptanzkriterien:** Nach fehlgeschlagenem Import ist `imported_at` NULL; nach
erfolgreichem Skip/Import bleibt der Erfolgszeitpunkt korrekt.

**Aufwand:** S

### P2-16: Dauerhafte `missing_period_coverage`-Warnungen nicht quittierbar

**Problem:** `validation._coverage_issues` (`validation.py:173-210`) erwartet für jede
(direction, entity)-Periode beide Datumsbasen. Der Privatbestand hat laut
`Datenmodell.md` historisch echte Lücken (z. B. 59 vs. 56 Dateien) — diese erzeugen bei
jedem `validate`-Lauf und auf `/imports` dieselben Warnungen, die man nie „erledigen"
kann. Dauerrauschen senkt die Aufmerksamkeit für neue, echte Lücken.

**Fix-Vorschlag (fachliche Entscheidung nötig):** Quittierungsmechanismus, z. B.
Tabelle `accepted_issues (code, fingerprint, accepted_at, note)`; `validate` und
`/imports` blenden quittierte Fingerprints aus bzw. zeigen sie eingeklappt. Fingerprint
für Coverage: `direction|entity|date_basis|period_start|period_end`. CLI:
`cm-dashboard accept-issue <fingerprint>`.

**Akzeptanzkriterien:** Quittierte Lücken erscheinen nicht mehr als offene Warnungen;
neue Lücken erscheinen weiterhin; Quittierungen überleben `validate`-Refreshes (nicht
aber `rebuild`, das ist zu dokumentieren oder die Tabelle wird beim Rebuild kopiert).

**Aufwand:** M–L (Scope-Entscheidung beim Maintainer)

---

## P3 — Kleinigkeiten

### P3-1: Einrückungsfehler der schließenden Klammer

`src/cm_dashboard/importing/raw_store.py:105-106`: Die schließende Klammer des
`rows.append(`-Aufrufs steht auf Spalte 4 statt 8 (syntaktisch gültig, optisch wie ein
Block-Ende der for-Schleife). Fix: Klammer korrekt einrücken. Aufwand: S.

### P3-2: Semantik von `combined_total` klären

`reporting/queries.py:257` summiert Käufe **plus** Verkäufe zu `combined_total`; im
CSV-Report (`web/app.py:69-79`, Spalte `total`) steht dieser Wert kommentarlos neben
`purchase_total`/`sales_total`. Kauf+Verkauf zu addieren ist fachlich fragwürdig
(Geldabfluss + Geldzufluss). Entweder in `netto` (sales − purchases) ändern, in
`gross_volume` umbenennen oder in README („Reporting-Semantik") explizit definieren.
Aufwand: S (Doku) bzw. M (Umbenennung inkl. Tests/Feldliste).

### P3-3: Dezimal-Heuristik dokumentieren

`normalize.py:68-77`: `"1.234"` wird als 1,234 interpretiert (Punkt = Dezimaltrenner),
`"1.234,56"` korrekt als 1234,56. Für Cardmarket-Exporte (Punkt-Dezimal) korrekt, aber
die Annahme sollte als Kommentar/Docstring an `normalize_decimal` und in
`Datenmodell.md` stehen, damit künftige Quellformate bewusst geprüft werden. Aufwand: S.

### P3-4: `synthetic_sources` schreibt CSV unabhängig von der Endung

`tests/synthetic_sources.py:81-96` schreibt immer CSV-Inhalt, auch wenn der übergebene
Pfad `.XLS`/`.XLSX` heißt — ein Test, der versehentlich eine XLS-Endung nutzt, erhält
einen verwirrenden Calamine-Fehler. Guard ergänzen:
`if path.suffix.lower() != ".csv": raise ValueError(...)`. Aufwand: S.

### P3-5: Lizenz fehlt

Keine `LICENSE`-Datei, kein `license`-Feld in `pyproject.toml:5-16`. Das Repo ist
öffentlich — ohne Lizenz gilt „alle Rechte vorbehalten", was ggf. unbeabsichtigt ist.
Entscheidung des Maintainers; danach `LICENSE` + `project.license` ergänzen. Aufwand: S.

### P3-6: Kein Favicon-Handler

Browser fordern `/favicon.ico` an → 404 pro Seitenaufruf. Kleines Inline-SVG-Icon als
Route oder `<link rel="icon">` auf eine statische Datei in `base.html` ergänzen.
Aufwand: S.

---

## Geprüft und bewusst NICHT beanstandet

Damit ein umsetzendes System nichts „repariert", was keiner Korrektur bedarf:

- **SQL-Injection:** Alle Abfragen parametrisiert; die f-String-WHERE-Klauseln in
  `reporting/queries.py` setzen nur intern konstruierte Klauseln ein, Werte laufen
  ausnahmslos über Parameter. `_get_or_create_named_row` (`article_import.py:190`)
  interpoliert Tabellennamen, wird aber nur mit den Literalen `"expansions"` /
  `"categories"` aufgerufen — kein Injektionspfad.
- **XSS:** Jinja2-Autoescaping aktiv (`Jinja2Templates`); Templates geben keine
  `|safe`-Werte aus. CSP/`X-Frame-Options`/`nosniff`-Header vorhanden (`web/app.py:148-164`).
- **httpx2 als Dev-Dependency** (`pyproject.toml:21`): korrekt — Starlette 1.3 verlangt
  für den TestClient das Paket `httpx2`; Tests laufen damit nachweislich.
- **Wheel-Glob `cm_dashboard-*.whl`** in `verify_distribution.py:21`: korrekt, da
  Wheel-Namen normalisiert werden (`cm-dashboard` → `cm_dashboard`). Verifiziert durch
  realen Build.
- **Excel-Serial-Datumskonvertierung** (`normalize.py:93`): Für den relevanten
  Wertebereich empirisch geprüft — keine Mikrosekunden-Artefakte durch Float-Rundung.
- **Savepoint-Transaktionslogik** (`pipeline.py:103-165`): pro Datei atomar; Verhalten
  von Python-sqlite3 (implizites BEGIN nur außerhalb aktiver Transaktion) korrekt genutzt.
- **Dedup-Design** (Business-Key mit `occurrence_index`): schlüssig; identische
  Mehrfachpositionen innerhalb einer Datei bleiben erhalten, CSV/XLS-Spiegel werden
  dedupliziert (Ausnahme: P1-1).
- **`os.replace`-Rebuild** (`pipeline.py:236`): atomar auf gleicher Partition; das
  `finally` räumt die Temp-DB nach Erfolg nicht doppelt (Datei existiert nicht mehr).
- **Maskierung** (`_mask_text`): zeigt erstes+letztes Zeichen — bewusster,
  dokumentierter Trade-off einer lokalen Einzelplatz-App; keine Änderung empfohlen.
- **`event_filter_requested`-Logik** in `_shipment_where` (`queries.py:346-351`):
  bewusstes Design, damit ungefilterte Sendungslisten auch Sendungen ohne Events zeigen.

## Empfohlene Umsetzungsreihenfolge

1. **P0-1 + P0-2** — CI grün machen (kleiner, isolierter Test-Fix; sofort umsetzbar).
2. **P1-1 + P2-4 gebündelt** — beide ändern normalisierte Fakten; zusammen ein einziger
   Sprung von `NORMALIZATION_VERSION` auf 3 und ein dokumentierter `rebuild`.
3. **P1-2 + P2-5 + P2-6 + P1-3 gebündelt** — Konfigurations-/Startup-Refactoring der
   Web-App und Pfad-Defaults (hängen zusammen; README/Docs in einem Zug anpassen).
4. **P1-4, P1-5, P2-1, P2-2** — kleine, unabhängige Korrektheits-/UX-Fixes.
5. **P2-3, P2-12** — DB-/Migrationshärtung (eine neue Migration, Konvention dokumentieren).
6. **P2-8 bis P2-11, P2-13 bis P2-15, P3-x** — beliebig einstreubar.
7. **P2-16, P3-2, P3-5** — erfordern eine fachliche Entscheidung des Maintainers, vor
   Umsetzung klären.

## Verifikation nach Umsetzung

Für jede Änderungsrunde lokal (bzw. in CI) ausführen:

```
python -m ruff check src tests scripts
python -m mypy
python -m pytest -q                      # muss ohne private Quelldaten grün sein
python -m build && python scripts/verify_distribution.py --dist dist
```

Mit Privatbestand zusätzlich: `CM_DASHBOARD_RUN_FULL_SOURCE_TESTS=1 python -m pytest -q`
und `scripts/verify_mvp.ps1` (Windows). Nach Fakten-relevanten Fixes (P1-1, P2-4):
`cm_dashboard.cli rebuild` + `validate` gegen den echten Bestand, Kennzahlenvergleich
Dashboard vor/nach (Artikelzahl darf sich nur durch bisher fehlgeschlagene Dedups ändern).
