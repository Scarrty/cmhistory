# Cardmarket History Dashboard Wiki

> **100 % AI-generated / Best Effort:** Alle Projektartefakte wurden mit KI-Systemen generiert.
> Trotz Tests kann die Software Fehler enthalten. Ergebnisse pruefen und Backups behalten.
> [Vollstaendiger Hinweis](https://github.com/Scarrty/cmhistory/blob/main/NOTICE.md).

Dieses Wiki beschreibt Version **1.0.0** des Cardmarket History Dashboards. Die Anwendung
importiert historische und neue Cardmarket-Statistikexporte, verknuepft Artikel mit Sendungen
und stellt Kauf- und Verkaufsdaten lokal in einem filterbaren Dashboard dar.

## Schnellstart

1. [Cardmarket-Exporte erstellen](Cardmarket-Exporte)
2. [Software installieren](Installation)
3. [Ersten Datenbankaufbau ausfuehren](Erster-Datenbankaufbau)
4. [Dashboard starten und verwenden](Dashboard-und-Reports)
5. [Neue Monate importieren](Monatlicher-Import)

## Dokumentation

| Thema | Inhalt |
|---|---|
| [Cardmarket-Exporte](Cardmarket-Exporte) | Berichte erzeugen, Dateitypen, Datumsbasis und Vollstaendigkeit |
| [Installation](Installation) | Windows-Installation aus dem Release und Installation aus Git |
| [Erster Datenbankaufbau](Erster-Datenbankaufbau) | Quellen pruefen, Datenbank bauen und validieren |
| [Monatlicher Import](Monatlicher-Import) | Wiederkehrender Import neuer Berichte |
| [Dashboard und Reports](Dashboard-und-Reports) | Seiten, Filter und Reporting-Semantik |
| [Betrieb und Konfiguration](Betrieb-und-Konfiguration) | Pfade, Start, Stopp, Upgrade und lokaler Betrieb |
| [Datenschutz und Backups](Datenschutz-und-Backups) | Schutz der Exporte und Wiederherstellung |
| [Fehlerbehebung](Fehlerbehebung) | Typische Meldungen und konkrete Loesungen |
| [Release 1.0.0](Release-v1.0.0) | Funktionsumfang und Upgrade-Hinweise |

## Unterstuetzte Quellen

- Excel 97-2003 (`.xls`)
- Excel Open XML (`.xlsx`)
- Semikolongetrennte CSV-Dateien (`.csv`)
- Gekaufte und verkaufte Artikel
- Gekaufte und verkaufte Sendungen
- Kaufdatum (`PURCHASEDATE`) und Zahlungsdatum (`PAYMENTDATE`)

Die Quelldateien bleiben unveraendert. SQLite ist ein reproduzierbarer Arbeitsbestand und kann
jederzeit aus den Originalexporten neu aufgebaut werden.

## Sicherheitsgrenze

Die Anwendung ist eine lokale Einzelplatzanwendung ohne Anmeldung. Sie darf nur an
`127.0.0.1` gebunden und nicht direkt im Internet oder lokalen Netzwerk freigegeben werden.
Cardmarket-Exporte koennen Namen, Anschriften, Benutzernamen und steuerbezogene Angaben
enthalten. Sie gehoeren nicht in Git, Cloud-Freigaben oder Support-Tickets.

Projekt: [Scarrty/cmhistory](https://github.com/Scarrty/cmhistory)  
Lizenz: [MIT](https://github.com/Scarrty/cmhistory/blob/main/LICENSE)
