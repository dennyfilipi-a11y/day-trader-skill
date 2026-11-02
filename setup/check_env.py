#!/usr/bin/env python3
"""Check this project's setup: Python, paper-only config, broker guard, data sources.

    python3 setup/check_env.py            # everything
    python3 setup/check_env.py --offline  # skip the network probes

Read only: it changes nothing and sends no order. Every probe is one small
GET to a free public endpoint the tools use.
"""
import json
import os
import shutil
import ssl
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "Mozilla/5.0 (compatible; day-trader-skill/2.0; setup check)"
SKILLS = ["trader-scanner", "trader-news", "trader-entry", "trader-exit", "trader-timemachine",
          "trader-risk", "trader-budget", "trader-broker", "trader-alerts", "trader-analyst",
          "trader-pelosi"]

# (what, url, who uses it, needs the SEC user agent)
SOURCES = [
    ("Yahoo charts (query2)", "https://query2.finance.yahoo.com/v8/finance/chart/SPY?range=1d&interval=1d",
     "scanner, entry, exit, timemachine, news, alerts", False),
    ("Yahoo charts (query1)", "https://query1.finance.yahoo.com/v8/finance/chart/SPY?range=1d&interval=1d",
     "fallback for the chart tools", False),
    ("Yahoo headlines RSS", "https://feeds.finance.yahoo.com/rss/2.0/headline?s=SPY&region=US&lang=en-US",
     "news", False),
    ("Stooq quotes", "https://stooq.com/q/l/?s=spy.us&f=sd2t2ohlcv&h&e=csv", "alerts (--source stooq)", False),
    ("Nasdaq Trader symbol list", "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
     "scanner universe", False),
    ("SEC tickers", "https://www.sec.gov/files/company_tickers.json", "news (8-K), analyst", True),
    ("SEC XBRL facts", "https://data.sec.gov/submissions/CIK0000320193.json", "analyst", True),
    ("House Clerk disclosures", "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2026FD.zip",
     "pelosi", False),
]


def sec_ua():
    ua = os.environ.get("SEC_USER_AGENT", "").strip()
    if not ua:
        try:
            with open(os.path.join(ROOT, "trader", "config.json"), encoding="utf-8") as fh:
                ua = str(json.load(fh).get("sec_user_agent") or "").strip()
        except (OSError, ValueError):
            ua = ""
    return ua if "@" in ua and "you@example.com" not in ua else ""


def probe(url, ua):
    req = urllib.request.Request(url, headers={"User-Agent": ua, "Range": "bytes=0-2047"})
    try:
        with urllib.request.urlopen(req, timeout=20, context=ssl.create_default_context()) as r:
            r.read(2048)
            return True, "HTTP %d" % r.status
    except urllib.error.HTTPError as e:
        return False, "HTTP %d" % e.code
    except Exception as e:  # noqa: BLE001 - report any failure as text
        reason = getattr(e, "reason", e)
        text = str(reason)
        if "403" in text or "Tunnel" in text or "tunnel" in text:
            text += " (blocked by this environment's network policy?)"
        return False, text


def line(ok, what, detail):
    print("  %-6s %-28s %s" % ("OK" if ok else "FAIL", what, detail))
    return ok


def main(argv):
    offline = "--offline" in argv
    ok_all = True
    print("Setup")
    ok_all &= line(sys.version_info >= (3, 8), "Python >= 3.8", sys.version.split()[0])
    pdf = shutil.which("pdftotext")
    line(True, "pdftotext (optional)", pdf or "missing: trader-pelosi then reads only the index, not PDF text")
    linked = [s for s in SKILLS if os.path.isfile(os.path.join(ROOT, ".claude", "skills", s, "SKILL.md"))]
    ok_all &= line(len(linked) == len(SKILLS), "project skills", "%d of %d in .claude/skills" % (len(linked), len(SKILLS)))
    try:
        with open(os.path.join(ROOT, "trader", "config.json"), encoding="utf-8") as fh:
            cfg = json.load(fh)
    except (OSError, ValueError) as e:
        cfg = {}
        ok_all &= line(False, "trader/config.json", str(e))
    if cfg:
        paper = cfg.get("paper") is True
        ok_all &= line(paper, "paper trading", "paper: true" if paper else "paper is NOT true: fix trader/config.json")
        risky = [k for k in ("allow_options", "allow_margin", "allow_short") if cfg.get(k)]
        ok_all &= line(not risky, "no options/margin/short", ", ".join(risky) or "all off")
    hook = os.path.isfile(os.path.join(ROOT, ".claude", "hooks", "block_orders.py"))
    ok_all &= line(hook, "broker/order guard", ".claude/hooks/block_orders.py" if hook else "missing")
    for k in ("ALPACA_API_KEY", "ALPACA_SECRET_KEY", "APCA_API_KEY_ID", "APCA_API_SECRET_KEY"):
        if os.environ.get(k):
            ok_all &= line(False, "no broker keys", "%s is set: remove it, this project is paper only" % k)
    ua = sec_ua()
    line(True, "SEC user agent", "set" if ua else "not set: SEC parts of news/analyst are skipped (set SEC_USER_AGENT)")

    if offline:
        print("\nData sources: skipped (--offline)")
    else:
        print("\nData sources (one small GET each)")
        for what, url, used, needs_sec in SOURCES:
            if needs_sec and not ua:
                line(False, what, "skipped: no SEC user agent")
                ok_all = False
                continue
            ok, detail = probe(url, ua if needs_sec else UA)
            ok_all &= line(ok, what, "%s  [%s]" % (detail, used))
    print("\n%s" % ("All checks passed." if ok_all else "Some checks failed: see ANLEITUNG.md, section Fehlerbehebung."))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
