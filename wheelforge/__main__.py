"""
WheelForge CLI — run the scanner from a terminal, not just the website.

  python -m wheelforge scan AAPL MSFT NVDA      score a few names
  python -m wheelforge scan                     score the live screener universe
  python -m wheelforge scan --top 25 --min 55   bigger universe, only setups >= 55

  python -m wheelforge roll NVDA --strike 180 --exp 2026-07-03 --entry 2.00 --qty 2
                                                manage an OPEN put: BTC / HOLD / ROLL

  python -m wheelforge cc NVDA --basis 175 [--dte 30] [--shares 100]
                                                got assigned? sell a call to grind the basis

Scan prints a ranked table of the best cash-secured puts. Roll closes the OTHER half
of the trade: feed it a put you already sold and it prices the live mid, computes how
much premium you have captured and how close spot sits to your strike, and tells you to
take the win (BTC_NOW), sit tight (HOLD), or defend it (ROLL_ALERT). cc runs the wheel's
SECOND leg: feed it shares you hold and their cost basis and it finds the lowest OTM call
at or above that basis, prices it live, and tells you how much it grinds the basis down.
Same engine the site runs. No em dashes (Michael's rule).
"""

from __future__ import annotations

import sys
from datetime import date

from wheelforge.build_site_data import build_one, _sector_crowding
from wheelforge.roll_advisor import evaluate as roll_evaluate
from wheelforge.roll_advisor import roll_target, ROLL_OUT_DTE
from wheelforge.universe import screen_universe, seed_universe


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
    # A crowded pick is a fine setup that doubles up an already-represented sector: mark it
    # so he sizes (or skips) the correlated name on purpose, not by accident.
    crowd = " SECTOR" if p.get("sector_crowded") else ""
    # Trailing support tag (only when struck AT a real floor): the price and how many
    # times the market has TESTED it, so a level held 7x reads differently from a one-off
    # pivot. Same append-no-header style as the SECTOR flag above.
    supp = ""
    if p.get("at_support") and p.get("support"):
        tch = p.get("support_touches")
        supp = f"  sup ${p['support']:.0f}" + (f"x{tch}" if tch else "")
    return (f"{rank:>2}  {score:>5}  {t['ticker']:<6} "
            f"{('$'+format(p['strike'],'.2f')):>9} {p['dte']:>3}d "
            f"{_num(p.get('annualized_roc')):>6}% {_num(p.get('prob_otm')):>5}% "
            f"{p.get('source','?'):<6} wf {_num(fs.get('wheel_fit')):>5} {earn:>6}{crowd}{supp}")


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
        # Enrich the typed names with their REAL earnings date + sector (same path the
        # screener uses) so the earnings veto actually fires on `scan NVDA` the eve of a
        # print, instead of riding earnings_days=None -> 999 -> never blocked. seed_universe
        # screens by name; merge so every typed ticker still survives (never drop a name)
        # even if the screen omits one, falling open to None for any it could not resolve.
        seeded = {d["ticker"]: d for d in seed_universe(tickers)}
        plan = [seeded.get(t, {"ticker": t, "earnings_days": None, "sector": None})
                for t in tickers]
        print(f"scanning {len(plan)} names...")
    else:
        plan = screen_universe(limit=top)
        print(f"scanning the screener universe ({len(plan)} names)...")

    rows = []
    for r in plan:
        try:
            one = build_one(r["ticker"], r.get("earnings_days"), sector=r.get("sector"))
            if one:
                rows.append(one)
        except Exception as exc:
            print(f"  {r['ticker']}: skipped ({exc})")
    rows = [x for x in rows if x["pick"]["score"] >= minscore or x["pick"]["avoid"]]
    rows.sort(key=lambda x: (not x["pick"]["avoid"], x["pick"]["score"]), reverse=True)
    _sector_crowding(rows)   # flag correlated duplicates AFTER the rank (does not reorder)

    print("\n  SCORE  TICKER     STRIKE  DTE   YIELD  OTM%  SOURCE  WHEEL  EARN")
    print("  " + "-" * 68)
    for i, t in enumerate(rows, 1):
        print(_row(i, t))
    live = sum(1 for t in rows if t["pick"].get("source") == "live")
    print(f"\n{len(rows)} setups, {live} on live chains. Sell the put, collect the premium, "
          f"build toward free shares.")


def _live_quote(ticker, strike, exp):
    """Fetch (current_put_mid, spot, iv) for one open short put off the yfinance
    chain. Fail-open: returns (None, None, None) if anything is missing."""
    try:
        import yfinance as yf
        tk = yf.Ticker(ticker)
        hist = tk.history(period="5d", interval="1d", auto_adjust=False)
        spot = float(hist["Close"].iloc[-1]) if hist is not None and not hist.empty else None
        puts = tk.option_chain(exp).puts
        row = puts[puts["strike"] == float(strike)]
        if row is None or row.empty:
            return None, spot, None
        row = row.iloc[0]
        bid, ask = float(row.get("bid") or 0), float(row.get("ask") or 0)
        mid = (bid + ask) / 2.0 if (bid > 0 and ask > 0) else float(row.get("lastPrice") or 0)
        iv = float(row.get("impliedVolatility") or 0) or None
        return (mid or None), spot, iv
    except Exception:
        return None, None, None


def _roll_chain(ticker, min_dte):
    """Pick the nearest expiry at least min_dte out and return (exp, [(strike, mid)...])
    for its puts, so roll_target can price the down-and-out roll. Fail-open: ('', []) on
    any error or empty chain (the alert then stands without a specific prescription)."""
    try:
        import yfinance as yf
        tk = yf.Ticker(ticker)
        today = date.today()
        future = []
        for e in (tk.options or ()):
            try:
                d = (date.fromisoformat(e) - today).days
            except ValueError:
                continue
            if d >= min_dte:
                future.append((e, d))
        if not future:
            return "", []
        exp = min(future, key=lambda ed: ed[1])[0]
        out = []
        for _, row in tk.option_chain(exp).puts.iterrows():
            bid, ask = float(row.get("bid") or 0), float(row.get("ask") or 0)
            mid = (bid + ask) / 2.0 if (bid > 0 and ask > 0) else float(row.get("lastPrice") or 0)
            k = float(row.get("strike") or 0)
            if k > 0 and mid > 0:
                out.append((k, mid))
        return exp, out
    except Exception:
        return "", []


def _roll_parse(args):
    """Parse: roll TICKER --strike X --exp YYYY-MM-DD --entry P [--qty N]
    [--current C] [--spot S] [--iv V]. The last three are offline overrides."""
    o = {"ticker": None, "strike": None, "exp": None, "entry": None,
         "qty": 1, "current": None, "spot": None, "iv": None}
    i = 0
    while i < len(args):
        a = args[i].lower()
        if a == "roll":
            i += 1; continue
        if a.startswith("--") and i + 1 < len(args):
            key, val = a[2:], args[i + 1]
            if key in ("strike", "entry", "current", "spot", "iv"):
                o[key] = float(val)
            elif key == "qty":
                o["qty"] = int(val)
            elif key == "exp":
                o["exp"] = val
            i += 2; continue
        if o["ticker"] is None:
            o["ticker"] = args[i].upper()
        i += 1
    return o


def roll(args):
    o = _roll_parse(args)
    if not (o["ticker"] and o["strike"] and o["exp"] and o["entry"] is not None):
        print("usage: python -m wheelforge roll TICKER --strike X --exp YYYY-MM-DD "
              "--entry PREMIUM [--qty N]")
        return 1
    try:
        dte_remaining = (date.fromisoformat(o["exp"]) - date.today()).days
    except ValueError:
        print(f"bad --exp date: {o['exp']} (use YYYY-MM-DD)")
        return 1

    current, spot, iv = o["current"], o["spot"], o["iv"]
    if current is None or spot is None or iv is None:
        q_cur, q_spot, q_iv = _live_quote(o["ticker"], o["strike"], o["exp"])
        current = current if current is not None else q_cur
        spot = spot if spot is not None else q_spot
        iv = iv if iv is not None else q_iv
    if current is None or spot is None:
        print(f"could not price {o['ticker']} {o['strike']}p {o['exp']} live; pass "
              f"--current and --spot to run it offline.")
        return 1

    # DTE-total is unknown from the args alone (we only know expiry); approximate the
    # original tenor from the captured-decay rule's perspective by assuming a weekly
    # sell unless the remaining clock already exceeds it. The two exit rules only need
    # the FRACTION of time left, and for a short-dated weekly the seller's total tenor
    # is ~7-14 days, so anchor on max(remaining, the weekly DTE) as the denominator.
    from wheelforge.build_site_data import DTE as _WEEKLY
    dte_total = max(dte_remaining, _WEEKLY)
    r = roll_evaluate(entry=o["entry"], current=current, dte_total=dte_total,
                      dte_remaining=dte_remaining, spot=spot, strike=o["strike"],
                      iv=iv, qty=o["qty"], opt_type="put")
    badge = {"BTC_NOW": ">> BTC NOW", "ROLL_ALERT": "!! ROLL ALERT", "HOLD": "-- HOLD"}
    print(f"\n  {o['ticker']} ${o['strike']:.2f} put  exp {o['exp']}  ({dte_remaining}d left)")
    print(f"  sold @ ${o['entry']:.2f}  now @ ${current:.2f}  spot ${spot:.2f}"
          f"{'  (modeled iv)' if iv is None else ''}")
    print(f"\n  {badge.get(r['state'], r['state'])}   "
          f"captured {r['captured_pct']}%  (${r['captured_dollars']:.0f})  "
          f"sigma-to-strike {r['sigma_dist']}")
    print(f"\n  {r['action']}")
    # The diagnostic above says "roll down-and-out for a credit"; this is the PRESCRIPTION.
    # On a live ROLL_ALERT, fetch the roll-out chain (~two weeks past the current expiry)
    # and name the specific strike, expiry and net credit, so Michael reads a trade he can
    # place, not generic advice. Needs a live IV to size the 1 sigma target; if the chain or
    # IV is unavailable the alert simply stands without the line (fail-open, never throws).
    if r["state"] == "ROLL_ALERT":
        new_exp, cands = _roll_chain(o["ticker"], dte_remaining + ROLL_OUT_DTE)
        new_dte = (date.fromisoformat(new_exp) - date.today()).days if new_exp else None
        tgt = (roll_target(current_mid=current, spot=spot, iv=iv, new_dte=new_dte,
                           candidates=cands, qty=o["qty"], opt_type="put")
               if (cands and new_dte) else None)
        if tgt:
            kind = "credit" if tgt["net_credit"] >= 0 else "DEBIT"
            print(f"\n  -> ROLL TO  ${tgt['picked_strike']:.2f} put  exp {new_exp}  "
                  f"({new_dte}d)  @ ${tgt['new_premium']:.2f}")
            print(f"     net {kind} ${abs(tgt['net_credit']):.2f}/share  "
                  f"(${abs(tgt['net_credit_dollars']):.0f} on {o['qty']}x)   "
                  f"target ~1 sigma below spot = ${tgt['target_strike']:.2f}")
        else:
            print("\n  -> ROLL TO  no live roll-out chain (or IV) available to size the "
                  "specific strike; the alert stands.")
    # The won-trade advisory rides alongside the state: it can fire while state is HOLD
    # (a short weekly past the BTC DTE gate but already at 50% of max profit). Only worth
    # printing when it adds something the state did not already say (state == HOLD).
    if r.get("profit_take") == "CLOSE_50" and r["state"] == "HOLD":
        print(f"\n  $$ PROFIT TARGET (50%)   you can buy it back for <= half what you sold "
              f"it for. On a short weekly, closing now frees the collateral to re-sell a "
              f"fresh week instead of holding the slow tail to expiry.")
    print()
    return 0


def _call_chain(ticker, min_dte):
    """Fetch (exp, spot, rv, [candidate calls]) for the nearest expiry at least min_dte out,
    so covered_call_read can pick and price the call to sell. Each candidate carries the
    strike, mid premium, bid/ask, OI and volume. rv is a quick realized-vol read off recent
    closes (the VRP denominator). Fail-open: returns (None, None, None, []) on any error."""
    try:
        import yfinance as yf
        from wheelforge.build_site_data import _realized_vol
        tk = yf.Ticker(ticker)
        hist = tk.history(period="1y", interval="1d", auto_adjust=False)
        if hist is None or hist.empty:
            return None, None, None, []
        closes = [float(c) for c in hist["Close"].tolist() if c == c]
        spot = closes[-1]
        rv = _realized_vol(closes[-63:]) or None
        today = date.today()
        future = []
        for e in (tk.options or ()):
            try:
                d = (date.fromisoformat(e) - today).days
            except ValueError:
                continue
            if d >= min_dte:
                future.append((e, d))
        if not future:
            return None, spot, rv, []
        exp = min(future, key=lambda ed: ed[1])[0]
        cands = []
        for _, row in tk.option_chain(exp).calls.iterrows():
            bid, ask = float(row.get("bid") or 0), float(row.get("ask") or 0)
            mid = (bid + ask) / 2.0 if (bid > 0 and ask > 0) else float(row.get("lastPrice") or 0)
            k = float(row.get("strike") or 0)
            if k > 0 and mid > 0:
                cands.append({
                    "strike": k, "premium": mid, "bid": bid, "ask": ask,
                    "open_interest": float(row.get("openInterest") or 0),
                    "volume": float(row.get("volume") or 0),
                    "iv": float(row.get("impliedVolatility") or 0) or None,
                })
        return exp, spot, rv, cands
    except Exception:
        return None, None, None, []


def _cc_parse(args):
    """Parse: cc TICKER --basis B [--dte N] [--shares N] [--spot S] [--earnings D]."""
    o = {"ticker": None, "basis": None, "dte": 30, "shares": 100,
         "spot": None, "earnings": None}
    i = 0
    while i < len(args):
        a = args[i].lower()
        if a == "cc":
            i += 1; continue
        if a.startswith("--") and i + 1 < len(args):
            key, val = a[2:], args[i + 1]
            if key in ("basis", "spot"):
                o[key] = float(val)
            elif key in ("dte", "shares"):
                o[key] = int(val)
            elif key == "earnings":
                o["earnings"] = float(val)
            i += 2; continue
        if o["ticker"] is None:
            o["ticker"] = args[i].upper()
        i += 1
    return o


def cc(args):
    from wheelforge.covered_call import covered_call_read
    o = _cc_parse(args)
    if not (o["ticker"] and o["basis"] is not None):
        print("usage: python -m wheelforge cc TICKER --basis COST [--dte N] [--shares N]")
        return 1

    exp, spot, rv, cands = _call_chain(o["ticker"], o["dte"])
    if o["spot"] is not None:
        spot = o["spot"]
    if spot is None or not cands:
        print(f"could not load a live call chain for {o['ticker']}; try a different "
              f"--dte, or check the ticker.")
        return 1
    dte = (date.fromisoformat(exp) - date.today()).days if exp else o["dte"]

    read = covered_call_read(spot=spot, basis=o["basis"], dte=dte, candidates=cands,
                             exp=exp, rv=rv, days_to_earnings=o["earnings"],
                             want_to_own=True)
    if read is None:
        print(f"\n  {o['ticker']}: no out-of-the-money call reaches your ${o['basis']:.2f} "
              f"basis at {dte}d (spot ${spot:.2f}). The shares are too far underwater to "
              f"sell a clean covered call here; hold, or roll the basis down another way.")
        return 0

    grade = read.get("grade", "?")
    score = "AVOID" if read.get("avoid") else f"{read['score']}"
    print(f"\n  {o['ticker']}  covered call  exp {exp}  ({dte}d)   spot ${spot:.2f}  "
          f"basis ${o['basis']:.2f}  x{o['shares']//100 or 1}")
    print(f"\n  [{grade}] score {score}   sell ${read['strike']:.2f} call @ ${read['premium']:.2f}"
          f"   keeps-shares {read['prob_otm']}%")
    print(f"  basis ${o['basis']:.2f} -> ${read['new_basis']:.2f}  "
          f"({read['basis_reduction_pct']}% this cycle, {read['annualized_roc']}% annualized)"
          f"  called-away gain {read['called_away_gain_pct']}%")
    print(f"\n  {read['summary']}")
    print(f"\n  {read['why']}\n")
    return 0


def main(argv):
    args = argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if args[0].lower() == "roll":
        return roll(args)
    if args[0].lower() == "cc":
        return cc(args)
    if args[0].lower() == "scan" or args[0].upper().isalpha():
        scan(args)
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
