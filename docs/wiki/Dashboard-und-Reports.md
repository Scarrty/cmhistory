# Dashboard und Reports

## Seiten

| URL | Zweck |
|---|---|
| `/` | Kennzahlen, Filter und Monatsdiagramm |
| `/imports` | Importstatus und Datenqualitaetshinweise |
| `/shipments` | Sendungsexplorer und Sendungsdetails |
| `/articles` | Artikelexplorer und Produktdetails |
| `/reports/period.csv` | Gefilterter CSV-Zeitraumreport |

Basisadresse: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Datumsbasis

`PAYMENTDATE` ist die empfohlene Standardansicht, weil sie im aktuellen Bestand die breiteste
Abdeckung besitzt. `PURCHASEDATE` kann fuer fachliche Vergleiche ausgewaehlt werden.

Beide Sichten enthalten dieselben physischen Artikelpositionen unter unterschiedlichen
Ereigniszeitpunkten. Ergebnisse aus `PAYMENTDATE` und `PURCHASEDATE` nie addieren.

## Filter

Je nach Seite stehen unter anderem zur Verfuegung:

- Von- und Bis-Datum
- Kauf oder Verkauf
- Kauf- oder Zahlungsdatum
- Artikelname und Kommentar
- Produkt-ID und lokalisierter Produktname
- Set und Kategorie
- Bestellnummer
- Handelspartner und Land
- Waehrung
- Mindest- und Hoechstbetrag
- Menge
- Importdatei
- Verknuepfungsstatus zwischen Artikel und Sendung

Filter werden serverseitig auf die Datenbank angewendet. Listen sind paginiert und zeigen daher
nicht nur die ersten hundert Treffer als Gesamtbestand an.

## Kennzahlen

- Artikelpositionen und Mengen stammen aus `article_lines`.
- Sendungsanzahlen stammen aus den ueber Richtung und Bestellnummer deduplizierten Sendungen.
- Artikelwerte enthalten keine automatische Waehrungsumrechnung.
- Shipment-Gesamtwerte koennen Versand, Trustee-Service oder Kommission gemaess Quelle
  enthalten; die Einzelwerte bleiben getrennt gespeichert.

## CSV-Zeitraumreport

Der Report verwendet dieselben Kernfilter wie das Dashboard. Wichtige Spalten:

| Spalte | Bedeutung |
|---|---|
| `purchase_total` | Summe der gefilterten Kaufartikel |
| `sales_total` | Summe der gefilterten Verkaufsartikel |
| `total` | Bruttovolumen aus Kauf- plus Verkaufssummen |
| `net_total` | Verkaufssumme minus Kaufsumme |

`net_total` ist kein Gewinn. Gebuehren, Versand, Steuern, Lagerbestandsveraenderungen und FIFO-
Kosten sind nicht vollstaendig enthalten. Der Export ist kein Steuerreport und ersetzt keine
Buchhaltung oder Steuerberatung.

Beispiel fuer einen gefilterten Download:

```text
http://127.0.0.1:8000/reports/period.csv?date_basis=PAYMENTDATE&direction=SOLD
```

Am einfachsten werden die Filter im Dashboard gesetzt und anschliessend der dort angebotene
CSV-Report geoeffnet.

## Personendaten

Benutzernamen und Namen werden in normalen Ansichten maskiert. Adress- und VAT-Felder werden in
den Reporting-Abfragen nicht ausgegeben. Die lokale Datenbank enthaelt dennoch aus den
Originalexporten abgeleitete personenbezogene Daten und muss entsprechend geschuetzt werden.
