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
# the thesis is "sell DEAR and stay DISCIPLINED." YIELD is now a first-class factor
# of its own: Michael's book targets ~100% a year on capital, so the annualized
# return-on-capital has to count directly, not hide inside free_shares. Assignment
# is welcome, never feared, so we do NOT penalize it here; we reward the fat yield.
WEIGHTS = {
    "richness": 0.25,
    "safety": 0.18,
    "yield": 0.18,
    "free_shares": 0.12,
    "liquidity": 0.13,
    "structure": 0.14,
}

# A spread this wide makes the quoted mid a fiction: the real fill is far worse, so the
# annualized RoC is overstated before a single order is placed. Parallel to MIN_PREMIUM
# (the tradeable-dollar floor in build_site_data): beyond this the pick is ungradeable on
# liquidity, not merely penalized, no matter how deep the open interest looks.
MAX_SPREAD_PCT = 0.15


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


# A chronic gapper loses up to this fraction of its prob-OTM safety credit. Bounded so a
# gap read never zeroes a genuinely far-OTM strike; it just docks the name that the smooth
# lognormal prob_otm flatters. (gap_risk itself is computed in tail_risk.py off the OHLCV.)
GAP_HAIRCUT_MAX = 0.35


def gap_haircut(gap_risk):
    """Multiplier in [1 - GAP_HAIRCUT_MAX, 1.0] from a 0..1 gap-risk read. A name that gaps
    hard overnight can jump a far-OTM strike no matter how good its prob_otm looks, so it is
    genuinely LESS safe at the same distance. Junk / missing -> 1.0 (no haircut, fail-open)."""
    return 1.0 - GAP_HAIRCUT_MAX * clamp01(gap_risk)


def safety_score(prob_otm, gap_risk=0.0):
    """Disciplined sellers want a high chance the short stays OTM. ~0.70 prob is
    the floor of 'income not lottery'; 0.85+ is the sweet spot. The prob_otm is a
    THIN-tailed lognormal estimate, so a chronic overnight gapper gets a haircut: same
    distance, less safe (see tail_risk.gap_risk). gap_risk defaults to 0 = no haircut."""
    return clamp01(_ramp(prob_otm, 0.55, 0.88) * gap_haircut(gap_risk))


def liquidity_score(bid, ask, open_interest, volume):
    """Tight spread + real interest. An edge you cannot fill is not an edge."""
    bid = float(bid or 0); ask = float(ask or 0)
    mid = (bid + ask) / 2.0
    spread_pct = ((ask - bid) / mid) if mid > 0 else 1.0
    if spread_pct >= MAX_SPREAD_PCT:
        return 0.0                                # too wide to grade: the mid is a fiction
    tight = 1.0 - _ramp(spread_pct, 0.02, 0.20)   # <=2% tight, >=20% awful
    depth = _ramp((open_interest or 0), 100, 2000)
    flow = _ramp((volume or 0), 10, 500)
    return clamp01(0.5 * tight + 0.3 * depth + 0.2 * flow)


def yield_score(annualized_roc):
    """The income-machine factor. Michael runs a ~100%-a-year book and SCANS for the
    fattest weeklies, so the ceiling sits at 2x: a 200% weekly must out-score a 100%
    monthly on yield, not tie it. A 1.0-ceiling saturated at his baseline and went blind
    to the very edge he is hunting. Yield is the goal; assignment is welcome but never the
    point, so this factor knows nothing about assignment odds. RoC lives HERE now (it used
    to hide inside free_shares), counted directly."""
    return _ramp(annualized_roc, 0.08, 2.0)        # 8% floor, ~100%/yr = midfield, 2x maxes it


def free_shares_score(opt_type, want_to_own, basis_discount):
    """The OWNERSHIP fit (RoC moved to yield_score, so no double-count). For a
    cash-secured PUT: is this a name you'd be happy to be assigned and own free
    shares of over time? For a COVERED CALL: does selling it reduce basis without
    capping away a name you meant to keep?"""
    if str(opt_type).lower().startswith("p"):
        return 1.0 if want_to_own else 0.15        # assignment must be welcome
    # covered call: value the basis reduction (do not cap a keeper for nothing)
    return _ramp(basis_discount, 0.0, 0.05)        # 0-5% basis cut per cycle


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


# ── the letter grade (reads instantly; "63.5" does not) ──────────────────────

# Map the 0-100 Premium Quality Score to a letter so the board reads at a glance.
# Bands are TraderDaddy's EdgeScore cuts (csp-intelligence.md): A>=80, B>=65, C>=50,
# D>=35, F below. An earnings-vetoed pick scores 0, so it lands F honestly: a setup
# you must skip IS a failing setup, and the dimmed AVOID card already says why.
GRADE_BANDS = (("A", 80.0), ("B", 65.0), ("C", 50.0), ("D", 35.0))


def letter_grade(score):
    """A>=80, B>=65, C>=50, D>=35, else F. Pure; junk -> 'F'."""
    try:
        s = float(score)
    except (TypeError, ValueError):
        return "F"
    if s != s:  # NaN
        return "F"
    for letter, floor in GRADE_BANDS:
        if s >= floor:
            return letter
    return "F"


# ── the composite ────────────────────────────────────────────────────────────

def score_contract(c):
    """Score one candidate option-sell contract (a dict). Returns
    {score, direction, avoid, factors, why}. Pure; fail-open on missing fields."""
    opt_type = str(c.get("opt_type", "put"))
    is_put = opt_type.lower().startswith("p")

    factors = {
        "richness": richness_score(c.get("iv"), c.get("rv"), c.get("iv_rank")),
        "safety": safety_score(c.get("prob_otm"), c.get("gap_risk")),
        "yield": yield_score(c.get("annualized_roc")),
        "liquidity": liquidity_score(c.get("bid"), c.get("ask"),
                                     c.get("open_interest"), c.get("volume")),
        "free_shares": free_shares_score(opt_type, c.get("want_to_own"),
                                         c.get("basis_discount")),
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
        "grade": letter_grade(score),
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
    if f.get("yield", 0) >= 0.55:
        bits.append("fat annualized yield")
    if f["liquidity"] < 0.4:
        bits.append("but illiquid, hard to fill")
    if is_put and f["free_shares"] >= 0.6:
        bits.append("good free-shares fit if assigned")
    if clamp01(c.get("gap_risk")) >= 0.5:
        bits.append("watch overnight gap risk")
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

    # Two aggressive CSPs, same rich/safe/liquid setup: one at ~100%/yr (Michael's
    # baseline) and one at ~200%/yr (a fat weekly he scans FOR). With the 2x ceiling the
    # baseline lands midfield and the 2x maxes, so the fatter weekly must out-score the
    # 1x on the yield factor, not tie it. That is the whole point of raising the ceiling.
    one_x = dict(great_csp); one_x["annualized_roc"] = 1.05
    fat_yield = dict(great_csp); fat_yield["annualized_roc"] = 2.10

    # Two picks with deep OI/volume, identical but for the SPREAD: a 1.6% spread (real,
    # fillable) vs a 16% spread (the mid is a fiction). Before the MAX_SPREAD_PCT floor the
    # wide one still scored ~0.61 liquidity on its OI alone, clearing the 0.4 illiquid line
    # and inflating its RoC; now it is ungradeable (0.0) while the tight one stays strong.
    tight_fill = liquidity_score(bid=1.99, ask=2.02, open_interest=3000, volume=600)
    wide_fill = liquidity_score(bid=0.46, ask=0.54, open_interest=3000, volume=600)
    # The MODELED path carries a tight (4%) synthetic spread but NO real interest (oi=vol=0),
    # so it must collapse to the spread-only term and never reach a real liquid pick's range.
    modeled_fill = liquidity_score(bid=1.96, ask=2.04, open_interest=0, volume=0)

    g = score_contract(great_csp)
    e = score_contract(earnings_trap)
    c = score_contract(cheap_illiquid)
    o = score_contract(one_x)
    y = score_contract(fat_yield)
    print("great CSP   :", g["score"], g["direction"], "|", g["why"])
    print("earnings trap:", e["score"], e["direction"], "|", e["why"])
    print("cheap/illiq :", c["score"], c["direction"], "|", c["why"])
    print("1x yield    :", o["score"], "| yield factor", o["factors"]["yield"])
    print("2x yield    :", y["score"], y["direction"], "|", y["why"])

    assert g["score"] >= 70, "a genuinely rich, safe, liquid CSP should score high"
    assert e["avoid"] and e["score"] == 0.0, "earnings before expiry must hard-avoid"
    assert c["score"] < g["score"], "cheap + illiquid must rank below the great setup"
    assert g["direction"] == "cash-secured put"
    assert 0.45 <= o["factors"]["yield"] <= 0.60, "a ~100%/yr setup should sit midfield now"
    assert y["factors"]["yield"] >= 0.9, "a ~200% annualized weekly should max the yield factor"
    assert y["factors"]["yield"] > o["factors"]["yield"], "a 2x weekly must out-yield a 1x"
    assert y["score"] > g["score"], "fat yield must out-score the same setup at thin yield"
    assert "fat annualized yield" in y["why"], "a fat-yield pick should say so plainly"

    # GAP-RISK haircut: the same far-OTM CSP is LESS safe on a chronic overnight gapper.
    gappy = dict(great_csp); gappy["gap_risk"] = 1.0
    gp = score_contract(gappy)
    print("gappy CSP   :", gp["score"], "| safety", gp["factors"]["safety"],
          "vs calm", g["factors"]["safety"], "|", gp["why"])
    assert gp["factors"]["safety"] < g["factors"]["safety"], "a hard gapper must score less safe"
    assert gp["score"] < g["score"], "the gap haircut must drag the composite, same distance"
    assert "watch overnight gap risk" in gp["why"], "a serious gapper should say so plainly"
    # fail-open: a missing gap_risk leaves safety untouched (no silent penalty).
    assert safety_score(0.84) == safety_score(0.84, None), "missing gap_risk -> no haircut"
    assert 0.0 <= gap_haircut(0.5) <= 1.0 and gap_haircut(1.0) < gap_haircut(0.0), \
        "the haircut is a bounded multiplier that bites harder with more gap risk"

    # The letter grade reads the score at a glance (and an avoid is an honest F).
    print("grades      :", "great", g["grade"], "| 2x", y["grade"], "| cheap",
          c["grade"], "| avoid", e["grade"])
    assert g["grade"] in ("A", "B"), "a 70+ setup should grade A or B"
    assert e["grade"] == "F", "an earnings-vetoed (score 0) pick must grade F"
    assert letter_grade(80) == "A" and letter_grade(79.9) == "B", "A band starts at 80"
    assert letter_grade(50) == "C" and letter_grade(34.9) == "F", "C floor 50, F below 35"
    assert letter_grade(None) == "F" and letter_grade("x") == "F", "junk grades F, fail-open"
    assert y["grade"] >= g["grade"] or y["score"] > g["score"], "fatter yield never grades worse"
    print("tight spread:", round(tight_fill, 3), "| wide spread:", round(wide_fill, 3),
          "| modeled (no OI):", round(modeled_fill, 3))
    assert wide_fill == 0.0, "a spread past MAX_SPREAD_PCT must be ungradeable, not OI-rescued"
    assert tight_fill >= 0.6, "a tight, deep pick should still grade liquid"
    assert tight_fill > wide_fill, "the fillable quote must out-liquidity the fictional one"
    assert modeled_fill <= 0.5, "a modeled pick (no real OI/vol) must not pass for a liquid one"
    assert modeled_fill < tight_fill, "a real liquid put must out-liquidity a modeled one"
    print("\nOK: WheelForge scoring self-test passed.")


if __name__ == "__main__":
    _selftest()
