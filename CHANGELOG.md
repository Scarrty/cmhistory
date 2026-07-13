# Changelog

> **AI-/Best-Effort-Hinweis:** Dieses Projekt und seine Dokumentation wurden zu 100 % mit KI
> generiert. Keine Gewaehr; Details stehen in [NOTICE.md](NOTICE.md).

Alle wesentlichen Aenderungen dieses Projekts werden in dieser Datei dokumentiert.

## [1.0.0] - 2026-07-13

Erste stabile Version des lokalen Cardmarket History Dashboards.

### Enthalten

- Wiederholbarer Import von Cardmarket-Exporten in `.xls`, `.xlsx` und `.csv`
- Atomarer Datenbank-Neuaufbau und idempotenter Monatsimport
- Verknuepfung von Artikeln und Sendungen ueber Richtung und Bestellnummer
- Dashboard, Artikel- und Sendungsexplorer mit serverseitigen Filtern
- Monatsdiagramme und CSV-Zeitraumreport mit Brutto- und Nettosicht
- Datenqualitaetspruefungen, Quellenabdeckung und quittierbare bekannte Luecken
- Lokaler, read-only FastAPI/Jinja-Betrieb mit maskierten Personendaten
- Vollstaendige Installations-, Export-, Import- und Betriebsdokumentation im GitHub-Wiki
- Sichtbarer 100-%-AI-generated- und Best-Effort-Hinweis in Repository, Wiki und Anwendung
- MIT-Lizenz

### Upgrade-Hinweis

Version 1.0.0 verwendet Normalisierungsversion 3. Bestehende Datenbanken aus einer
Vorabversion muessen mit dem dokumentierten `rebuild`-Befehl aus den Originalexporten neu
aufgebaut werden. Die Quelldateien bleiben dabei unveraendert.

[1.0.0]: https://github.com/Scarrty/cmhistory/releases/tag/v1.0.0
