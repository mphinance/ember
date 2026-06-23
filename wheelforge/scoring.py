"""
wheelforge/scoring.py — the pure Premium Quality Score.

Built by ember toward GOAL.md: rank option-SELLING setups for a disciplined seller
whose endgame is free shares. This is the core: pure functions, no network, fully
testable. Data + CLI come in later cycles.

A setup scores high when the premium is genuinely rich, it's safe enough to be
disciplined, it's tradeable, it doesn't sell through earnings (hard avoid), it fits
the free-shares endgame, and structure agrees. See GOAL.md for the thesis.

No third-party deps. No em dashes in user-facing strings (Michael's rule).
"""

from __future__ import annotations


# Relative importance of each factor in the blend. Richness + safety lead because
# the thesis is "sell DEAR and stay DISCIPLINED." Tunable in later cycles.
WEIGHTS = {
    "richness": 0.28,
    "safety": 0.24,
    "free_shares": 0.20,
    "liquidity": 0.14,
    "structure": 0.14,
}


def clamp01(x):
    """Coerce to a float in [0, 1]; junk -> 0.0."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return 0.0
    if x != x:  # NaN
        return 0.0
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def _ramp(x, lo, hi):
    """Linear 0..1 as x goes lo..hi (saturating). lo<hi assumed."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return 0.0
    if hi == lo:
        return 0.0
    return clamp01((x - lo) / (hi - lo))


# ── per-factor scores (each 0..1) ────────────────────────────────────────────

def richness_score(iv, rv, iv_rank):
    """How rich is this premium? VRP (iv/rv above 1.0) plus IV Rank elevation.
    Selling cheap vol is off-thesis, so a sub-1.0 VRP scores near zero."""
    vrp = (float(iv) / float(rv)) if (iv and rv and float(rv) > 0) else 1.0
    vrp_s = _ramp(vrp, 1.0, 1.6)          # 1.0x = no edge, 1.6x = very rich
    rank_s = clamp01((iv_rank or 0) / 100.0)
    return clamp01(0.6 * vrp_s + 0.4 * rank_s)


def safety_score(prob_otm):
    """Disciplined sellers want a high chance the short stays OTM. ~0.70 prob is
    the floor of 'income not lottery'; 0.85+ is the sweet spot."""
    return _ramp(prob_otm, 0.55, 0.88)


def liquidity_score(bid, ask, open_interest, volume):
    """Tight spread + real interest. An edge you cannot fill is not an edge."""
    bid = float(bid or 0); ask = float(ask or 0)
    mid = (bid + ask) / 2.0
    spread_pct = ((ask - bid) / mid) if mid > 0 else 1.0
    tight = 1.0 - _ramp(spread_pct, 0.02, 0.20)   # <=2% tight, >=20% awful
    depth = _ramp((open_interest or 0), 100, 2000)
    flow = _ramp((volume or 0), 10, 500)
    return clamp01(0.5 * tight + 0.3 * depth + 0.2 * flow)


def free_shares_score(opt_type, annualized_roc, want_to_own, basis_discount):
    """The endgame. For a cash-secured PUT: strong annualized return on capital AND
    a name you'd be happy to be assigned (own free shares over time). For a COVERED
    CALL: reduce basis without capping away a name you meant to keep."""
    roc_s = _ramp(annualized_roc, 0.08, 0.35)     # 8% annualized floor, 35% great
    if str(opt_type).lower().startswith("p"):
        own_s = 1.0 if want_to_own else 0.15       # assignment must be welcome
        return clamp01(0.6 * roc_s + 0.4 * own_s)
    # covered call: value the basis reduction; mild own-bonus so we don't cap a keeper
    disc_s = _ramp(basis_discount, 0.0, 0.05)      # 0-5% basis cut per cycle
    return clamp01(0.6 * roc_s + 0.4 * disc_s)


def structure_score(trend_align):
    """Not selling puts into a falling knife or calls into a rip. Caller supplies a
    0..1 alignment (0.5 = neutral) until the data layer computes it."""
    return clamp01(trend_align if trend_align is not None else 0.5)


# ── earnings: a HARD avoid gate, not a soft factor ───────────────────────────

def earnings_blocks(days_to_earnings, dte):
    """True if an earnings print lands on or before expiry. Selling premium through
    a print is the classic blowup, so this is a veto, not a deduction."""
    try:
        d = float(days_to_earnings)
    except (TypeError, ValueError):
        return False
    if d < 0:
        return False
    return d <= float(dte or 0)


# ── the composite ────────────────────────────────────────────────────────────

def score_contract(c):
    """Score one candidate option-sell contract (a dict). Returns
    {score, direction, avoid, factors, why}. Pure; fail-open on missing fields."""
    opt_type = str(c.get("opt_type", "put"))
    is_put = opt_type.lower().startswith("p")

    factors = {
        "richness": richness_score(c.get("iv"), c.get("rv"), c.get("iv_rank")),
        "safety": safety_score(c.get("prob_otm")),
        "liquidity": liquidity_score(c.get("bid"), c.get("ask"),
                                     c.get("open_interest"), c.get("volume")),
        "free_shares": free_shares_score(opt_type, c.get("annualized_roc"),
                                         c.get("want_to_own"), c.get("basis_discount")),
        "structure": structure_score(c.get("trend_align")),
    }

    avoid = earnings_blocks(c.get("days_to_earnings"), c.get("dte"))
    raw = sum(WEIGHTS[k] * factors[k] for k in WEIGHTS)
    score = 0.0 if avoid else round(100.0 * clamp01(raw), 1)

    if avoid:
        direction = "avoid"
    elif is_put:
        direction = "cash-secured put"
    else:
        direction = "covered call"

    factors = {k: round(v, 3) for k, v in factors.items()}
    return {
        "score": score,
        "direction": direction,
        "avoid": avoid,
        "factors": factors,
        "why": _rationale(c, factors, avoid, is_put),
    }


def _rationale(c, f, avoid, is_put):
    """One plain-English line. No em dashes."""
    if avoid:
        return ("Skip. Earnings print lands before expiry, do not sell premium "
                "through it.")
    bits = []
    bits.append("rich premium" if f["richness"] >= 0.6 else
                "thin premium" if f["richness"] < 0.35 else "fair premium")
    bits.append("safe distance" if f["safety"] >= 0.6 else
                "tight to the strike" if f["safety"] < 0.4 else "ok distance")
    if f["liquidity"] < 0.4:
        bits.append("but illiquid, hard to fill")
    if is_put and f["free_shares"] >= 0.6:
        bits.append("good free-shares fit if assigned")
    return ", ".join(bits) + "."


# ── self-test (keep WheelForge runnable every cycle) ─────────────────────────

def _selftest():
    great_csp = {
        "opt_type": "put", "iv": 0.45, "rv": 0.30, "iv_rank": 72, "prob_otm": 0.84,
        "bid": 1.95, "ask": 2.00, "open_interest": 4200, "volume": 800,
        "annualized_roc": 0.28, "want_to_own": True, "dte": 35, "days_to_earnings": 60,
        "trend_align": 0.7,
    }
    earnings_trap = dict(great_csp)
    earnings_trap["days_to_earnings"] = 10  # print before the 35 DTE expiry
    cheap_illiquid = {
        "opt_type": "put", "iv": 0.22, "rv": 0.24, "iv_rank": 15, "prob_otm": 0.62,
        "bid": 0.10, "ask": 0.35, "open_interest": 40, "volume": 3,
        "annualized_roc": 0.05, "want_to_own": False, "dte": 30, "days_to_earnings": 90,
        "trend_align": 0.5,
    }

    g = score_contract(great_csp)
    e = score_contract(earnings_trap)
    c = score_contract(cheap_illiquid)
    print("great CSP   :", g["score"], g["direction"], "|", g["why"])
    print("earnings trap:", e["score"], e["direction"], "|", e["why"])
    print("cheap/illiq :", c["score"], c["direction"], "|", c["why"])

    assert g["score"] >= 70, "a genuinely rich, safe, liquid CSP should score high"
    assert e["avoid"] and e["score"] == 0.0, "earnings before expiry must hard-avoid"
    assert c["score"] < g["score"], "cheap + illiquid must rank below the great setup"
    assert g["direction"] == "cash-secured put"
    print("\nOK: WheelForge scoring self-test passed.")


if __name__ == "__main__":
    _selftest()
