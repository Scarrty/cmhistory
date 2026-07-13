# Cardmarket-Exporte erstellen

Das Dashboard liest die Kauf- und Verkaufsstatistiken des eigenen Cardmarket-Kontos. Es liest
keinen Lagerbestandsexport und verwendet keine Cardmarket-API.

> Cardmarket kann Bezeichnungen und Positionen in der Benutzeroberflaeche aendern. Diese
> Anleitung beschreibt den im Juli 2026 bekannten Ablauf. Massgeblich sind die Reporttypen und
> Dateinamen, die im Abschnitt **Vollstaendiger Exportumfang** aufgefuehrt sind.

## Voraussetzungen

- Zugriff auf das eigene Cardmarket-Konto
- Abgeschlossene Kauf- oder Verkaufstransaktionen
- Ein Zeitraum, der spaetestens am Vortag endet
- Ein lokaler, nicht oeffentlich freigegebener Zielordner

Cardmarket erzeugt Statistikberichte asynchron. Nach dem Anfordern erscheint der Fortschritt
unter **Account -> Downloads**; nach Fertigstellung versendet Cardmarket zusaetzlich eine
E-Mail. Laut Cardmarket enthalten Berichte nur Daten bis einschliesslich zum Vortag. Ein
gleichartiger Bericht wird fuer 23 Stunden zwischengespeichert. Dieser Block gilt auch zwischen
Kaufdatum- und Zahlungsdatum-Varianten desselben Berichts.

## Bericht anfordern

1. Bei [Cardmarket](https://www.cardmarket.com/) anmelden.
2. **Account** oeffnen.
3. **Statistics** beziehungsweise **Statistiken** oeffnen.
4. Richtung auswaehlen:
   - **Purchased** / **Gekauft** fuer eigene Kaeufe
   - **Sold** / **Verkauft** fuer eigene Verkaeufe
5. Berichtsebene auswaehlen:
   - **Articles** fuer einzelne Artikelpositionen
   - **Shipments** fuer Bestellungen, Partner, Versand, Gebuehren und Summen
6. Datumsbasis auswaehlen:
   - **Purchase date** fuer das Kaufdatum
   - **Payment date** fuer das Zahlungsdatum
7. Start- und Enddatum festlegen. Fuer einen Monatsbericht immer den vollstaendigen Monat
   verwenden, beispielsweise `2026-06-01` bis `2026-06-30`.
8. Als Format **Excel** auswaehlen. Cardmarket kann dabei eine `.xls`- oder `.xlsx`-Datei
   liefern; beide werden unterstuetzt.
9. Berichtserzeugung starten.
10. **Account -> Downloads** oeffnen und warten, bis der Bericht bereitsteht.
11. Datei direkt in den lokalen Exportordner herunterladen.

Wenn die Oberflaeche nach dem ersten Bericht eine 23-Stunden-Sperre fuer die andere
Datumsbasis zeigt, den zweiten Bericht am Folgetag erzeugen. Bereits fertige Dateien nicht
erneut in Excel speichern, weil Tabellenprogramme Werte und Formate veraendern koennen.

## Vollstaendiger Exportumfang

Fuer eine lueckenlose Monatsabdeckung werden pro Zeitraum acht logische Berichte benoetigt:

| Richtung | Ebene | Datumsbasis | Erwarteter Dateianfang |
|---|---|---|---|
| Gekauft | Artikel | Zahlungsdatum | `PURCHASED ARTICLES-BYPAYMENTDATE-...` |
| Gekauft | Artikel | Kaufdatum | `PURCHASED ARTICLES-BYPURCHASEDATE-...` |
| Gekauft | Sendungen | Zahlungsdatum | `PURCHASED SHIPMENTS-BYPAYMENTDATE-...` |
| Gekauft | Sendungen | Kaufdatum | `PURCHASED SHIPMENTS-BYPURCHASEDATE-...` |
| Verkauft | Artikel | Zahlungsdatum | `SOLD ARTICLES-BYPAYMENTDATE-...` |
| Verkauft | Artikel | Kaufdatum | `SOLD ARTICLES-BYPURCHASEDATE-...` |
| Verkauft | Sendungen | Zahlungsdatum | `SOLD SHIPMENTS-BYPAYMENTDATE-...` |
| Verkauft | Sendungen | Kaufdatum | `SOLD SHIPMENTS-BYPURCHASEDATE-...` |

Das Dashboard funktioniert auch mit einem Teilbestand. Fehlende Gegenberichte oder
Datumsbasen werden dann als `missing_period_coverage` gemeldet. Fuer die normale Dashboard-
Sicht ist `PAYMENTDATE` die empfohlene Basis. Beide Datumsbasen bilden dieselben physischen
Artikel ab und duerfen nicht addiert werden.

## Dateinamen

Der Dateiname ist Teil des Importvertrags:

```text
<PURCHASED|SOLD> <ARTICLES|SHIPMENTS>-BY<PURCHASEDATE|PAYMENTDATE>-YYYY-MM-DD_YYYY-MM-DD.<XLS|XLSX|CSV>
```

Beispiele:

```text
SOLD ARTICLES-BYPAYMENTDATE-2026-06-01_2026-06-30.XLSX
PURCHASED SHIPMENTS-BYPURCHASEDATE-2026-06-01_2026-06-30.XLS
```

- Den von Cardmarket gelieferten Namen beibehalten.
- Browser-Zusaetze wie `(1)` nicht importieren. Die doppelte Datei entfernen und das Original
  behalten.
- Pro logischem Bericht nur ein Format ablegen. Parallele CSV- und Excel-Versionen werden zwar
  dedupliziert, erzeugen aber einen Informationshinweis.
- Historische Dateien nach erfolgreichem Import nicht umbenennen oder ersetzen.

## Kontrolle vor dem Import

Fuer jeden Monat pruefen:

- Zeitraum im Dateinamen stimmt mit der Auswahl in Cardmarket ueberein.
- Datei ist groesser als null Byte und laesst sich lokal oeffnen.
- Keine Kopien mit `(1)`, `(2)` oder aehnlichen Zusaetzen vorhanden.
- Erwartete Richtung, Ebene und Datumsbasis sind vorhanden.
- Der Zeitraum endet nicht am aktuellen Tag.

## Datenschutz

Shipment-Exporte koennen Benutzernamen, Namen, Adressen, Professional-Status und VAT-Angaben
enthalten. Die Dateien nur lokal speichern und wie Geschaefts- beziehungsweise Personendaten
schuetzen. Weitere Hinweise stehen unter [Datenschutz und Backups](Datenschutz-und-Backups).

## Offizielle Cardmarket-Hinweise

- [Asynchrone Reports, Download-Bereich, Vortagsgrenze und 23-Stunden-Cache](https://news.cardmarket.com/en/Magic/Cloudflare-Optimizations-And-Changes-To-Sales-Reports-On-Cardmarket)
- [Felder der exportierbaren Kauf- und Verkaufsstatistiken](https://news.cardmarket.com/en/Magic/Changes-To-Exportable-Buying-And-Selling-Statistics)
