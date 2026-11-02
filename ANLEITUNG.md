# Anleitung: Day-Trader-Skills im Paper Trading

Diese Anleitung gilt für diesen Fork (`dennyfilipi-a11y/day-trader-skill`).
Er ist so eingerichtet, dass **nur Paper Trading** möglich ist: Es gibt keine
Broker-Verbindung, keine API-Schlüssel und keine Echtgeld-Orders. Die
Original-README auf Englisch steht weiter in `README.md`.

> Keine Anlageberatung. Die Skills lesen öffentliche Daten und rechnen. Die
> meisten Daytrader verlieren Geld. Die Time Machine ist eine Simulation, keine
> Vorhersage.

## Was eingerichtet ist

| Teil | Wo | Was es tut |
| --- | --- | --- |
| 11 Skills | `.claude/skills/` (Verknüpfungen auf die Ordner `trader-*`) | Claude kennt die Befehle `/trader-scanner` usw. in diesem Projekt |
| Regeln | `trader/config.json` | Budget 5.000 $, max. 50 $ Verlust pro Trade, 150 $ pro Tag, 3 Trades pro Tag, `"paper": true` |
| Order-Sperre | `.claude/hooks/block_orders.py` und `.claude/settings.json` | blockiert jedes Broker-Werkzeug (Alpaca, Interactive Brokers und alles, was nach Order klingt), auch wenn jemand einen Connector hinzufügt |
| Prüfskript | `setup/check_env.py` | prüft Python, Paper-Einstellung, Sperre und alle Datenquellen |
| Testlauf | `setup/backtest.sh` | spielt alle 11 Skills mit echten historischen Daten durch (Tesla, 19.10.2026) |

Python 3.8 oder neuer reicht. Es muss nichts installiert werden: Die Tools
nutzen nur die Standardbibliothek. Eine virtuelle Umgebung ist deshalb nicht
nötig.

## Einmalig: Internet für die Datenquellen freigeben

Die Standard-Cloud-Umgebung blockiert die Börsendaten. Einmal einrichten:

1. In Claude das Projekt **Trading** öffnen, dann **Projekteinstellungen**,
   Bereich **Cloud environment**, Menü öffnen, **Add cloud environment**.
2. **Network access** auf **Limited** stellen, „Allow package managers“
   angehakt lassen und unter **Allowed domains** eintragen:
   ```
   query1.finance.yahoo.com
   query2.finance.yahoo.com
   feeds.finance.yahoo.com
   stooq.com
   www.nasdaqtrader.com
   www.sec.gov
   data.sec.gov
   disclosures-clerk.house.gov
   ```
3. Unter **Environment variables** eintragen (die SEC verlangt Name und
   E-Mail im Abruf, das ist kein API-Schlüssel):
   ```
   SEC_USER_AGENT=Vorname Nachname deine@email.de
   ```
   Die E-Mail steht bewusst nicht in `trader/config.json`, weil der Fork
   öffentlich ist.
4. Speichern. Das gilt für **neue** Threads.

Prüfen in einem neuen Thread: „Führe `python3 setup/check_env.py` aus.“
Alle Zeilen sollten `OK` zeigen.

## Der Handelstag

Die US-Börse öffnet um 9:30 Uhr New Yorker Zeit. Das ist meist **15:30 Uhr
deutscher Zeit** (in den Wochen, in denen nur eine Seite die Uhr umgestellt
hat, 14:30 Uhr). Alle Zeiten in den Skills sind New Yorker Zeit.

Am besten einen Handelstag in **einem** Thread erledigen: Die Arbeitsdateien
in `trader/` (Watchlist, Plan, Orders, Tageslog) leben nur so lange wie die
Cloud-Sitzung.

### Vor der Eröffnung (bis ca. 15:30 Uhr)

Schreib Claude zum Beispiel:

- „`/trader-scanner` daily: Welche Setups gibt es heute vorbörslich?“
- „`/trader-news` für TSLA, NVDA, AAPL: Was gibt es Neues?“
- „`/trader-alerts`: Erinnere mich an die Eröffnung.“

### Nach der Eröffnung (ab ca. 15:45 Uhr, frühestens 9:45 New York)

1. **`/trader-scanner` orb**: Welche Aktien brechen aus ihrer 15-Minuten-Spanne aus?
2. **`/trader-news` TICKER**: Gibt es eine Meldung, die den Kurs treibt (Earnings, Übernahme)?
3. **`/trader-entry` TICKER**: Wartet Kerze für Kerze und sagt „triggered“, wenn der Einstieg kommt.
4. **`/trader-exit`**: Legt Stop und Ziel fest, **bevor** du einsteigst.
5. **`/trader-timemachine`**: 10.000 Simulationen plus alle vergangenen Tage mit demselben Setup. Zeigt die ehrlichen Chancen.
6. **`/trader-budget`**: Wie viele Aktien passen zu deinem maximalen Verlust?
7. **`/trader-risk`**: PASS oder BLOCK gegen deine Regeln.
8. **`/trader-broker`**: Zeigt das Ticket. **Hier endet es in diesem Fork.** Es wird nichts gesendet.

### Paper-Trade festhalten

Statt einer echten Order trägst du den simulierten Kauf ins Paper-Depot ein:

- „Trag den Paper-Kauf ein: 8 TSLA zu 364,18.“
  Claude führt dann `ticket.py fill --symbol TSLA --side buy --qty 8 --price 364.18` aus.
- `/trader-alerts` mit `add --from-plan` legt Stop, Ziel und „flat by 15:55“ an.
  Danach regelmäßig „Prüf die Alerts“ (`alerts.py check`).
- Wenn Stop oder Ziel erreicht ist, oder spätestens um 15:55 New York (21:55 bei uns):
  „Trag den Paper-Verkauf ein: 8 TSLA zu 370,04.“

### Regelmäßig (unabhängig vom Trade)

- **`/trader-analyst` TICKER**: Was hat sich in den letzten Quartalszahlen geändert?
- **`/trader-pelosi`**: Neue Aktiengeschäfte von Kongressmitgliedern (öffentliche Pflichtmeldungen).

## Regeln anpassen

In `trader/config.json` oder einfach Claude sagen, zum Beispiel: „Setz mein
Budget auf 2.000 $ und den maximalen Verlust pro Trade auf 20 $.“ Die
Bedeutung jeder Zeile steht in `trader-budget/SKILL.md`, Schritt 1.

`"paper"` bleibt `true`. Optionen, Margin und Leerverkäufe bleiben aus.

## Testlauf mit historischen Daten

```bash
bash setup/backtest.sh
```

Spielt alle 11 Skills mit dem echten Handelstag Tesla, Montag 19.10.2026,
durch. Ergebnis zum Vergleich: Ausbruch um 10:15 bei 364,18, Stop 358,32,
Ziel 370,04, 8 Aktien, maximaler Verlust 46,88 $, Time Machine: Ziel zuerst
29,4 %, Stop zuerst 25,5 %, keines von beiden 45,1 %, also etwa ein
Münzwurf. Der Lauf braucht kein Internet und ändert nichts an deinen Dateien.

Alle automatischen Tests:

```bash
python3 -m unittest discover -s tests
```

## Was in diesem Fork nie passiert

- Keine Order an einen Broker, weder Paper noch echt. Die Sperre blockiert jedes Order-Werkzeug.
- Keine API-Schlüssel. Wenn dich jemand nach Alpaca- oder IBKR-Schlüsseln fragt: nicht eingeben.
- Keine Änderung am Original-Repository von Jake Schincariol.

## Fehlerbehebung

| Meldung | Ursache | Lösung |
| --- | --- | --- |
| `Tunnel connection failed: 403` oder `could not reach` | Netzwerk der Cloud-Umgebung blockiert die Domain | Abschnitt „Internet freigeben“ oben, dann neuer Thread |
| `SEC filings skipped` | `SEC_USER_AGENT` fehlt | Umgebungsvariable wie oben setzen |
| `Blocked by .claude/hooks/block_orders.py` | Ein Broker-Werkzeug sollte laufen | So gewollt: Paper only |
| Yahoo antwortet `HTTP 429` | zu viele Abrufe | ein paar Minuten warten; die Tools machen schon Pausen |
| `plan for another day is refused` | Plan ist von gestern | `/trader-exit` neu ausführen |
