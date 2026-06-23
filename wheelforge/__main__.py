"""
WheelForge CLI — run the scanner from a terminal, not just the website.

  python -m wheelforge scan AAPL MSFT NVDA      score a few names
  python -m wheelforge scan                     score the live screener universe
  python -m wheelforge scan --top 25 --min 55   bigger universe, only setups >= 55

Prints a ranked table of the best cash-secured puts: score, the strike to sell, yield,
odds it stays OTM, whether the premium is live or modeled, the wheel-fit, and days to
earnings (AVOID if a print lands before expiry). Reuses the same engine the site runs.
"""

from __future__ import annotations

import sys

from wheelforge.build_site_data import build_one
from wheelforge.universe import screen_universe


def _num(x, d="-"):
    return d if x is None else x


def _row(rank, t):
    p = t["pick"]
    fs = p.get("free_shares") or {}
    avoid = p.get("avoid")
    score = "AVOID" if avoid else f"{p['score']:>5}"
    earn = "" if p.get("earnings_days") is None else f"{p['earnings_days']}d"
    if avoid:
        earn += " !"
    return (f"{rank:>2}  {score:>5}  {t['ticker']:<6} "
            f"{('$'+format(p['strike'],'.2f')):>9} {p['dte']:>3}d "
            f"{_num(p.get('annualized_roc')):>6}% {_num(p.get('prob_otm')):>5}% "
            f"{p.get('source','?'):<6} wf {_num(fs.get('wheel_fit')):>5} {earn:>6}")


def _parse(args):
    tickers, top, minscore = [], 15, 0.0
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--top" and i + 1 < len(args):
            top = int(args[i + 1]); i += 2; continue
        if a == "--min" and i + 1 < len(args):
            minscore = float(args[i + 1]); i += 2; continue
        if a.lower() == "scan":
            i += 1; continue
        tickers.append(a.upper()); i += 1
    return tickers, top, minscore


def scan(args):
    tickers, top, minscore = _parse(args)
    if tickers:
        plan = [{"ticker": t, "earnings_days": None} for t in tickers]
        print(f"scanning {len(plan)} names...")
    else:
        plan = screen_universe(limit=top)
        print(f"scanning the screener universe ({len(plan)} names)...")

    rows = []
    for r in plan:
        try:
            one = build_one(r["ticker"], r.get("earnings_days"))
            if one:
                rows.append(one)
        except Exception as exc:
            print(f"  {r['ticker']}: skipped ({exc})")
    rows = [x for x in rows if x["pick"]["score"] >= minscore or x["pick"]["avoid"]]
    rows.sort(key=lambda x: (not x["pick"]["avoid"], x["pick"]["score"]), reverse=True)

    print("\n  SCORE  TICKER     STRIKE  DTE   YIELD  OTM%  SOURCE  WHEEL  EARN")
    print("  " + "-" * 68)
    for i, t in enumerate(rows, 1):
        print(_row(i, t))
    live = sum(1 for t in rows if t["pick"].get("source") == "live")
    print(f"\n{len(rows)} setups, {live} on live chains. Sell the put, collect the premium, "
          f"build toward free shares.")


def main(argv):
    args = argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if args[0].lower() == "scan" or args[0].upper().isalpha():
        scan(args)
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
