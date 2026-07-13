# Datenschutz und Backups

## Welche Daten sind sensibel?

Cardmarket-Exporte koennen enthalten:

- Benutzernamen und Klarnamen
- Anschriften und Laender
- Bestellnummern und Zeitpunkte
- Artikel, Mengen und Preise
- Professional-Status und VAT-Angaben
- Kommentare zu Artikeln oder Bestellungen

Die SQLite-Datenbank enthaelt Rohzeilen und normalisierte Fakten aus diesen Dateien. Auch wenn
die Weboberflaeche viele Personendaten maskiert oder nicht abfragt, bleibt die Datenbank selbst
schutzbeduerftig.

## Schutzmassnahmen

- Exporte, Datenbank und Backups nur im eigenen Benutzerkonto speichern.
- Keine Dateien in das oeffentliche GitHub-Repository committen.
- Keine Quelldateien an Issues, Chats oder Support-Tickets anhaengen.
- Dashboard nur an `127.0.0.1` starten.
- Datentraeger- oder Betriebssystemverschluesselung verwenden, wenn das Geraet mobil ist.
- Backups ebenfalls verschluesseln und Zugriffsrechte begrenzen.
- Vor der Weitergabe von Screenshots Namen, Bestellnummern und Filterparameter pruefen.

## Was muss gesichert werden?

Prioritaet 1:

1. Originale Cardmarket-Exporte im Ordner `exports`
2. `accepted_issues.json`, falls bekannte Abdeckungsluecken quittiert wurden

Prioritaet 2:

3. `data\cardmarket.db` fuer eine schnelle Wiederherstellung
4. Notizen zu bewusst fehlenden Berichten

Die Datenbank ist aus den Originalexporten reproduzierbar. Ohne Originalexporte koennen
historische Rohdaten nach einem Verlust nicht erneut von der Anwendung erzeugt werden.

## Manuelles Backup unter Windows

Server vorher stoppen:

```powershell
$root = "C:\CardmarketDashboard"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backup = "D:\Backups\CardmarketDashboard-$stamp"
New-Item -ItemType Directory -Path $backup -Force
Copy-Item "$root\exports" "$backup\exports" -Recurse
Copy-Item "$root\data\cardmarket.db" "$backup\cardmarket.db"
if (Test-Path "$root\data\accepted_issues.json") {
  Copy-Item "$root\data\accepted_issues.json" "$backup\accepted_issues.json"
}
```

## Wiederherstellung

Bevorzugte Variante:

1. Software installieren.
2. Originalexporte nach `exports` zurueckspielen.
3. `accepted_issues.json` nach `data` zurueckspielen.
4. Datenbank mit `rebuild` neu erzeugen.
5. `validate` ausfuehren.

Eine gesicherte SQLite-Datei kann bei exakt gleicher Anwendungsversion direkt zurueckkopiert
werden. Danach trotzdem `validate` ausfuehren.

## Aufbewahrung und Loeschung

Die notwendige Aufbewahrungsdauer haengt vom eigenen rechtlichen und steuerlichen Kontext ab.
Dieses Projekt legt keine Fristen fest. Professionelle Nutzer sollten Anforderungen mit ihrer
Buchhaltung oder Steuerberatung klaeren. Das Dashboard selbst ist kein Archivierungs- oder
Steuersystem.
