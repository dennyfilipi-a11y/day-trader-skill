#!/usr/bin/env bash
# Full paper test run of all 11 skills on real historical data (offline).
#
#   bash setup/backtest.sh            # the TSLA trade of Monday 2026-10-19, 10:15 AM New York
#   KEEP=1 bash setup/backtest.sh     # keep the scratch folder to look at the files
#
# The data are the fixtures in tests/fixtures: real Yahoo, SEC and House Clerk
# data saved on 2026-10-19/20. Every step runs in a scratch folder with its own
# trader/ directory, so your real trader/ files are not touched. The broker
# step only renders the ticket: nothing is sent anywhere, paper or live.
set -euo pipefail

R="$(cd "$(dirname "$0")/.." && pwd)"
F="$R/tests/fixtures"
W="$(mktemp -d)"
NOW="2026-10-19 10:15"
trap '[ "${KEEP:-0}" = 1 ] && echo "Files kept in $W" || rm -rf "$W"' EXIT
cd "$W"
mkdir -p trader
cp "$R/trader/config.json" trader/config.json 2>/dev/null || cp "$R/trader-budget/config.example.json" trader/config.json
python3 - <<'PY'
import json
c = json.load(open("trader/config.json"))
assert c.get("paper") is True, "trader/config.json must keep paper: true"
PY

step() { printf '\n==== %s ====\n' "$1"; }
py() { python3 "$@"; }

step "1/11 trader-scanner: opening-range breakouts at 10:15"
py "$R/trader-scanner/scan.py" orb --offline "$F/trader-scanner/wall5m-2026-10-19.json.gz" --now "$NOW" --at 10:15 --show 5
step "2/11 trader-news: TSLA headlines that morning"
py "$R/trader-news/news.py" --tickers TSLA --offline "$F/trader-news" --now 2026-10-19T14:15:00Z --no-sec --hours 12 --dry-run | head -12
step "3/11 trader-entry: TSLA bar by bar"
py "$R/trader-entry/entry.py" check TSLA --offline "$F/trader-entry/TSLA-2026-10-19-5m.json" --now "$NOW" --write
step "4/11 trader-exit: stop and target before the entry"
py "$R/trader-exit/exit.py" plan --stop or-mid --target 1R --now "$NOW" --write
step "5/11 trader-timemachine: 10,000 replays plus 59 real sessions"
py "$R/trader-timemachine/timemachine.py" run --offline "$F/trader-timemachine/TSLA-60d5m.json.gz" --now "$NOW" --write
step "6/11 trader-budget: size to the max loss"
py "$R/trader-budget/size.py" --now "$NOW" --write
step "7/11 trader-risk: PASS or BLOCK"
py "$R/trader-risk/check.py" --now "$NOW"
step "8/11 trader-broker: the ticket only (PAPER, nothing is sent)"
py "$R/trader-broker/ticket.py" show --now "$NOW" | head -12
step "9/11 trader-alerts: stop, target, flat by the close"
py "$R/trader-alerts/alerts.py" add --from-plan --date 2026-10-19
py "$R/trader-alerts/alerts.py" list
step "10/11 trader-analyst: Apple's quarters from SEC XBRL"
py "$R/trader-analyst/facts.py" AAPL --offline "$F/trader-analyst" --user-agent "Paper Test test@example.org" --quarters 4 --no-filings
step "11/11 trader-pelosi: 2026 PTR index from the House Clerk"
py "$R/trader-pelosi/ptr.py" index --year 2026 --member pelosi --offline "$F/trader-pelosi/2026FD.zip" --limit 5

printf '\nDone: all 11 skills ran on historical data. Paper only, no order was sent.\n'
