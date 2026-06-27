"""
wheelforge/roll_advisor.py — the trade lifecycle AFTER the sell.

WheelForge finds the put to sell. Then it goes silent: the moment Michael hits
"sell," nothing tells him when to take the win or when the trade is in trouble.
That gap is the whole difference between a screener and an income machine. This
module closes it. Pure functions, no network, fully testable. The live `roll` CLI
subcommand (in __main__.py) prices the current mid and feeds it in.

Three states, driven by two numbers (captured premium, distance to strike):

  BTC_NOW    you have captured >= 50% of the entry premium with >= 50% of the
             DTE still on the clock. The standard 50/50 exit: the rest of the
             decay is slow and not worth the assignment risk. Buy to close, free
             the capital, re-sell a fresh week.
  ROLL_ALERT spot has fallen within ~1 sigma of your strike with < 7 days left.
             The short is getting tested into expiry. Roll down-and-out for a
             credit before gamma bites, or take assignment if you want the shares.
  HOLD       in between. The trade is working. Let theta do its job.

ROLL_ALERT (a live risk) outranks BTC_NOW (a nice-to-have) when both could fire.
No em dashes in user-facing strings (Michael's rule).
"""

from __future__ import annotations

import math

BTC_CAPTURE = 0.50      # take the win once half the premium is decayed away...
BTC_DTE_FRAC = 0.50     # ...and at least half the clock is still left (slow tail)
ROLL_DTE = 7            # "into expiry" = inside the last week
ROLL_SIGMA = 1.0        # "tested" = spot within 1 sigma of the strike
ROLL_OUT_DTE = 14       # rolling OUT buys ~two more weeks of fresh time on the clock
PROFIT_TAKE_PCT = 0.50  # the canonical wheel exit: close once you can buy it back
                        # for <= half what you sold it for (50% of max profit booked)


def profit_take_alert(entry_premium, current_mid, dte_remaining):
    """The WON-trade signal, decoupled from the clock. Fires CLOSE_50 the moment the
    short can be bought back for <= PROFIT_TAKE_PCT of the entry premium, i.e. you have
    locked half the max profit, no matter how many days are left.

    This is the half of position management the BTC_NOW state in `evaluate` deliberately
    gates behind >=50% DTE remaining. That gate is right for a monthly grinding out its
    last few days of slow decay (let it expire, keep it all). It is WRONG for a short
    weekly that hits 50% on day 3 or 4: there the last half of the premium is small and
    the days left are worth more as freed collateral than as residual theta. Annual yield
    = premium-per-trade x trades-per-year; BTC_NOW guards the first term, this guards the
    second. So it travels as an advisory ALONGSIDE the state, never overriding it.

    entry_premium  premium received per share when the put was sold
    current_mid    the option's current mid per share (cost to buy to close)
    dte_remaining  days left to expiry (unused by the trigger; kept for the caller's line)

    Returns "CLOSE_50" when the target is hit, else None. Fail-open on junk input.
    """
    try:
        entry = float(entry_premium)
        mid = max(0.0, float(current_mid))
    except (TypeError, ValueError):
        return None
    if entry <= 0:
        return None
    return "CLOSE_50" if mid <= entry * PROFIT_TAKE_PCT else None


def _sigma_move(spot, iv, dte_remaining):
    """One standard-deviation price move over the time left, in dollars.
    sigma = S * IV * sqrt(t). Returns 0.0 on junk input (fail-open)."""
    try:
        spot, iv = float(spot), float(iv)
        t = max(0.0, float(dte_remaining)) / 365.0
    except (TypeError, ValueError):
        return 0.0
    if spot <= 0 or iv <= 0 or t <= 0:
        return 0.0
    return spot * iv * math.sqrt(t)


def roll_target(current_mid, spot, iv, new_dte, candidates,
                qty=1, opt_type="put", sigma_mult=ROLL_SIGMA):
    """Turn a ROLL_ALERT into a SPECIFIC trade: which strike to roll INTO, at the
    roll-out expiry, for what net credit. The diagnostic (`evaluate` says "roll
    down-and-out for a credit") is only half the job; this is the prescription.

    Pure, like everything else in this module: the live `roll` CLI fetches the chain
    at the roll-out expiry and feeds the (strike, premium) `candidates` in, exactly
    the way `evaluate` is fed the current mid. No network here.

    The roll-into strike sits ~1 sigma below current spot for a put (down-and-out):
    far enough that the new short is freshly OTM over the new tenor, close enough to
    still pay real premium. Among the candidates we take the strike nearest that
    target. net_credit = new_premium - current_mid: positive means rolling still PAYS
    you to do it (the whole point of rolling for a credit), negative means the roll
    costs money to buy more time, which the caller surfaces so Michael takes that on
    purpose rather than by accident.

    current_mid   cost per share to buy back the current short
    spot, iv      current underlying price and implied vol
    new_dte       days to the roll-out expiry (sets the 1 sigma target distance)
    candidates    list of (strike, premium) pairs from the roll-out chain
    qty           contracts (for the dollar figure)
    opt_type      "put" (default) or "call"; the roll direction flips side

    Returns {target_strike, picked_strike, new_premium, net_credit,
             net_credit_dollars, sigma} or None on junk / no candidates (fail-open).
    """
    try:
        cur = max(0.0, float(current_mid))
        s = float(spot)
        v = float(iv)
        t = max(0.0, float(new_dte)) / 365.0
        q = int(qty or 1)
    except (TypeError, ValueError):
        return None
    if s <= 0 or v <= 0 or t <= 0:
        return None
    is_put = str(opt_type).lower().startswith("p")
    sigma = s * v * math.sqrt(t)
    # down-and-out for a put (target below spot), up-and-out for a call (above)
    target = (s - sigma_mult * sigma) if is_put else (s + sigma_mult * sigma)

    best = None  # (distance_to_target, strike, premium)
    for c in candidates or ():
        try:
            k = float(c[0])
            prem = float(c[1])
        except (TypeError, ValueError, IndexError):
            continue
        if k <= 0 or prem < 0:
            continue
        d = abs(k - target)
        if best is None or d < best[0]:
            best = (d, k, prem)
    if best is None:
        return None

    _, picked, new_prem = best
    net_credit = round(new_prem - cur, 2)
    return {
        "target_strike": round(target, 2),
        "picked_strike": round(picked, 2),
        "new_premium": round(new_prem, 2),
        "net_credit": net_credit,                       # per share, can be negative
        "net_credit_dollars": round(net_credit * 100.0 * q, 2),
        "sigma": round(sigma, 2),
    }


def evaluate(entry, current, dte_total, dte_remaining, spot, strike,
             iv=None, qty=1, opt_type="put"):
    """Score one open short option against the two exit rules. Pure.

    entry         premium received per share when the put was sold
    current       the option's current mid per share (what it costs to BTC now)
    dte_total     calendar days from sell to expiry
    dte_remaining days left until expiry
    spot, strike  current underlying price and the short strike
    iv            current implied vol (for the 1 sigma test); falls back to a
                  realized estimate via dte if absent. Optional.
    qty           number of contracts (for the dollar figures)
    opt_type      "put" (default) or "call"; the distance test flips side.

    Returns {state, captured, dte_frac, sigma_dist, ... , action} where state is
    one of BTC_NOW / ROLL_ALERT / HOLD and action is a plain-English line.
    """
    entry = float(entry or 0.0)
    current = max(0.0, float(current or 0.0))
    dte_total = float(dte_total or 0.0)
    dte_remaining = max(0.0, float(dte_remaining or 0.0))
    qty = int(qty or 1)
    is_put = str(opt_type).lower().startswith("p")

    # Number one: how much of the premium has decayed into your pocket. Selling
    # at $2.00 and buying back at $0.80 is 60% captured. Can go negative if the
    # option moved against you (current > entry), which is itself a warning.
    captured = ((entry - current) / entry) if entry > 0 else 0.0
    dte_frac = (dte_remaining / dte_total) if dte_total > 0 else 0.0

    # Number two: how close is spot to the strike, measured in sigmas of the move
    # still possible before expiry. For a put the danger is spot falling TO the
    # strike (distance = spot - strike); for a call it is spot rising to it.
    sigma = _sigma_move(spot, iv, dte_remaining)
    raw_dist = (float(spot) - float(strike)) if is_put else (float(strike) - float(spot))
    sigma_dist = (raw_dist / sigma) if sigma > 0 else None
    breached = raw_dist <= 0                       # already ITM (in the money)

    # ── pick the state. Risk (ROLL_ALERT) beats opportunity (BTC_NOW). ──
    near_strike = breached or (sigma_dist is not None and sigma_dist <= ROLL_SIGMA)
    if dte_remaining < ROLL_DTE and near_strike:
        state = "ROLL_ALERT"
    elif captured >= BTC_CAPTURE and dte_frac >= BTC_DTE_FRAC:
        state = "BTC_NOW"
    else:
        state = "HOLD"

    captured_dollars = round((entry - current) * 100.0 * qty, 2)
    action = _action(state, captured, dte_remaining, sigma_dist, breached, is_put)
    # The won-trade advisory, computed independently of the state machine. On a short
    # weekly this fires while state is still HOLD (the BTC_NOW DTE gate has not opened),
    # which is exactly the early-close opportunity that frees collateral for more cycles.
    profit_take = profit_take_alert(entry, current, dte_remaining)
    return {
        "state": state,
        "captured": round(captured, 3),          # fraction of premium decayed
        "captured_pct": round(captured * 100.0, 1),
        "captured_dollars": captured_dollars,    # locked if you BTC right now
        "dte_remaining": int(dte_remaining),
        "dte_frac": round(dte_frac, 3),
        "sigma_dist": (round(sigma_dist, 2) if sigma_dist is not None else None),
        "breached": breached,
        "profit_take": profit_take,              # "CLOSE_50" or None (advisory, not state)
        "action": action,
    }


def _action(state, captured, dte_remaining, sigma_dist, breached, is_put):
    """One plain-English line per state. No em dashes."""
    if state == "BTC_NOW":
        return (f"Buy to close. You have captured {captured * 100:.0f}% of the premium "
                f"with {int(dte_remaining)} days still on the clock. Take the win, free "
                f"the capital, re-sell a fresh week.")
    if state == "ROLL_ALERT":
        side = "below" if is_put else "above"
        where = ("the strike is already breached" if breached
                 else f"spot is within {sigma_dist:.2f} sigma of the strike")
        roll = "down-and-out" if is_put else "up-and-out"
        return (f"Roll or take assignment. With {int(dte_remaining)} days left {where}, the "
                f"short is being tested. Roll {roll} for a credit before gamma bites, or "
                f"let it assign if you want the shares ({side} here is fine if you do).")
    held = "" if captured < 0 else f" You are up {captured * 100:.0f}% so far."
    return (f"Hold. The trade is working and theta is on your side.{held} No action until "
            f"you hit the 50% take-profit or spot tests the strike inside the last week.")


# ── self-test (keep WheelForge runnable every cycle) ─────────────────────────

def _selftest():
    # A: sold a $2.00 put, now worth $0.80 (60% captured), 20 of 30 DTE left, spot
    # comfortably above the strike. The textbook 50/50 take-profit.
    a = evaluate(entry=2.00, current=0.80, dte_total=30, dte_remaining=20,
                 spot=195, strike=180, iv=0.40, qty=2)
    # B: 5 DTE left, spot has fallen to 182 against a 180 strike with high IV, so
    # spot sits inside 1 sigma of the strike. The trade is being tested into expiry.
    b = evaluate(entry=2.00, current=2.60, dte_total=14, dte_remaining=5,
                 spot=182, strike=180, iv=0.55, qty=1)
    # C: working trade, early, only 20% captured. Hold.
    c = evaluate(entry=2.00, current=1.60, dte_total=30, dte_remaining=25,
                 spot=195, strike=180, iv=0.40, qty=1)
    # D: deep ITM near expiry (spot below strike). Breach must force ROLL_ALERT even
    # though "captured" looks positive on a stale mid.
    d = evaluate(entry=2.00, current=4.00, dte_total=14, dte_remaining=3,
                 spot=176, strike=180, iv=0.50, qty=1)
    # E: 60% captured but only 3 DTE left (clock mostly gone): the BTC 50/50 rule
    # needs >=50% DTE remaining, so this is NOT a fresh BTC_NOW. Spot is far from the
    # strike so it is not a roll either. Hold and let it expire worthless.
    e = evaluate(entry=2.00, current=0.80, dte_total=30, dte_remaining=3,
                 spot=200, strike=180, iv=0.35, qty=1)

    # F: a 7-DTE weekly bought back at 50% of entry on day 4 (3 DTE left). The BTC_NOW
    # state will NOT fire (only 3/7 = 43% of the clock left, under the 50% gate), but the
    # profit-take target IS hit. This is the early-close-on-a-weekly case the advisory
    # exists for: state HOLD, profit_take CLOSE_50.
    f = evaluate(entry=2.00, current=1.00, dte_total=7, dte_remaining=3,
                 spot=195, strike=180, iv=0.40, qty=1)

    for name, r in [("A take-profit", a), ("B tested", b), ("C working", c),
                    ("D breached", d), ("E late-decay", e), ("F weekly-50", f)]:
        print(f"{name:14} {r['state']:11} cap={r['captured_pct']:>5}% "
              f"dte={r['dte_remaining']:>2} sig={r['sigma_dist']} "
              f"take={r['profit_take'] or '-':>8} | {r['action']}")

    assert a["state"] == "BTC_NOW", "50%+ captured with 50%+ DTE left is the take-profit"
    assert a["captured_dollars"] == 240.0, "2 contracts, $1.20 decay = $240 locked"
    assert b["state"] == "ROLL_ALERT", "spot inside 1 sigma of strike with <7 DTE must alert"
    assert b["captured"] < 0, "a tested put that moved against you shows negative capture"
    assert c["state"] == "HOLD", "an early, working trade holds"
    assert d["state"] == "ROLL_ALERT" and d["breached"], "a breached strike near expiry alerts"
    assert e["state"] == "HOLD", "captured but <50% DTE left and far from strike is a hold"
    assert f["state"] == "HOLD", "a 7-DTE weekly at day 4 is past the BTC_NOW DTE gate"
    assert f["profit_take"] == "CLOSE_50", "but it HAS hit the 50% profit target (advisory)"

    # the pure function, in isolation: trigger is purely current_mid <= entry * 0.50.
    assert profit_take_alert(2.00, 1.00, 3) == "CLOSE_50", "exactly 50% of entry is hit"
    assert profit_take_alert(2.00, 0.90, 9) == "CLOSE_50", "below 50% is hit"
    assert profit_take_alert(2.00, 1.20, 5) is None, "60% of entry still left is not a take"
    assert profit_take_alert(0.0, 0.0, 5) is None, "no entry premium = no signal (fail-open)"
    assert profit_take_alert(None, 1.0, 5) is None, "junk input fails open to None"

    # G: the PRESCRIPTION for B's ROLL_ALERT. B is the 180 put tested at spot 182, IV 0.55,
    # 5 DTE, current mid 2.60. Roll out ~14 days (new_dte 19). 1 sigma over 19 days is
    # ~182*0.55*sqrt(19/365) ~= 22.8, so the down-and-out target is ~159.2; among the
    # candidate strikes the nearest is 160. Rolling 180->160 for $3.00 against the $2.60
    # buyback is a $0.40 (= $40 on 1x) NET CREDIT: a real down-and-out-for-a-credit trade.
    cands = [(175, 1.20), (170, 1.60), (165, 2.20), (160, 3.00), (155, 2.60)]
    g = roll_target(current_mid=2.60, spot=182, iv=0.55, new_dte=19,
                    candidates=cands, qty=1, opt_type="put")
    print(f"\nG roll_target -> strike {g['picked_strike']} @ {g['new_premium']} "
          f"(target {g['target_strike']}, sigma {g['sigma']}), net credit "
          f"${g['net_credit']}/sh (${g['net_credit_dollars']})")
    assert g["picked_strike"] == 160.0, "nearest candidate to the ~159 target is the 160 strike"
    assert g["net_credit"] == 0.40, "rolling into 3.00 against a 2.60 buyback is a 0.40 credit"
    assert g["net_credit_dollars"] == 40.0, "0.40/share x 100 x 1 contract = $40 credit"
    assert g["sigma"] > 0, "a live IV and DTE produce a real sigma move"
    # fail-open: no candidates, or junk vol/spot, returns None rather than throwing.
    assert roll_target(2.60, 182, 0.55, 19, []) is None, "no candidates = no prescription"
    assert roll_target(2.60, 182, None, 19, cands) is None, "junk iv fails open to None"
    assert roll_target(2.60, 0, 0.55, 19, cands) is None, "non-positive spot fails open"
    print("\nOK: WheelForge roll-advisor self-test passed.")


if __name__ == "__main__":
    _selftest()
