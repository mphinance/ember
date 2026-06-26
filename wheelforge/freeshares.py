"""
wheelforge/freeshares.py — the endgame: turn a cash-secured put into free shares.

Michael's thesis is not "collect premium." It is "sell premium with discipline until
you own the stock for free." So for every CSP this module answers the questions a
wheeler actually asks:
  - If I get assigned, what is my effective cost basis, and how far below today's price
    is that? (premium reduces the basis: basis = strike - premium)
  - What annualized return am I earning on the cash I tie up while I wait?
  - How good is this as a WHEEL entry overall (cheap basis on a name worth owning, with
    real income, without being near-certain to be put the stock)?

Pure, no network, self-tested. The single read the frontend and scoring lean on is
free_shares_read(). No em dashes in user-facing strings.
"""

from __future__ import annotations


def clamp01(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return 0.0
    if x != x:
        return 0.0
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def _ramp(x, lo, hi):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if hi == lo else clamp01((x - lo) / (hi - lo))


def assignment_basis(strike, premium):
    """Effective cost per share if assigned: you buy at the strike but keep the
    premium, so your real basis is strike minus premium."""
    return max(0.0, float(strike) - float(premium))


def basis_discount(spot, basis):
    """How far below today's price you would own it (fraction). Negative means
    assignment costs you ABOVE the current price (a bad wheel entry)."""
    spot = float(spot)
    return (spot - float(basis)) / spot if spot > 0 else 0.0


def prob_assigned(prob_otm):
    """Rough chance of being put the shares = 1 - P(expires OTM)."""
    try:
        return clamp01(1.0 - float(prob_otm))
    except (TypeError, ValueError):
        return 0.0


def wheel_fit(spot, strike, premium, annualized_roc, prob_otm, want_to_own=True):
    """0..1: how good a WHEEL entry this is. Rewards a cheap effective basis vs spot
    and real income on a name worth owning; lightly penalizes a near-certain
    assignment (that is closer to just being long than a premium play)."""
    basis = assignment_basis(strike, premium)
    disc_s = _ramp(basis_discount(spot, basis), 0.0, 0.12)      # owning 12% under = great
    roc_s = _ramp(annualized_roc, 0.08, 2.0)                    # 8% floor, ~100%/yr midfield, 2x maxes (matches scoring.yield_score)
    own_s = 1.0 if want_to_own else 0.2
    fit = 0.45 * disc_s + 0.35 * roc_s + 0.20 * own_s
    if prob_assigned(prob_otm) > 0.75:
        fit *= 0.85
    return clamp01(fit)


def free_shares_read(spot, strike, premium, annualized_roc, prob_otm, want_to_own=True):
    """The full free-shares read for one CSP. Plain dict, all fields rounded for UI."""
    basis = assignment_basis(strike, premium)
    disc = basis_discount(spot, basis)
    pa = prob_assigned(prob_otm)
    fit = wheel_fit(spot, strike, premium, annualized_roc, prob_otm, want_to_own)
    return {
        "assignment_basis": round(basis, 2),
        "basis_discount_pct": round(disc * 100, 1),
        "prob_assigned_pct": round(pa * 100, 1),
        "wheel_fit": round(fit * 100, 1),
        "summary": _summary(basis, disc, annualized_roc),
    }


def _summary(basis, disc, roc):
    if disc <= 0:
        return ("Weak wheel entry. Assignment would cost you at or above today's price, "
                "so this is income only, not cheap shares.")
    return (f"If assigned you own at ${basis:,.2f}, {disc*100:.1f}% below today, "
            f"earning {roc*100:.1f}% annualized on the cash while you wait.")


def _selftest():
    # A clean wheel: sell the 95 put on a 100 stock for 3.00, ~30% prob assigned.
    r = free_shares_read(spot=100, strike=95, premium=3.0, annualized_roc=0.22,
                         prob_otm=0.72, want_to_own=True)
    print("good wheel:", r)
    assert r["assignment_basis"] == 92.0, "basis = strike - premium"
    assert 7.5 < r["basis_discount_pct"] < 8.5, "own ~8% below spot"
    assert 25 < r["prob_assigned_pct"] < 30
    assert r["wheel_fit"] >= 50, "a cheap basis + real income on a wanted name fits"

    # Discrimination: roc sub-factor used to saturate at 35%/yr, so every name in
    # Michael's 100-200%/yr book looked identical on yield. Ramped to 2.0 now (matching
    # scoring.yield_score), a fat weekly must out-score a thin one, all else equal.
    thin = wheel_fit(spot=100, strike=95, premium=3.0, annualized_roc=0.30,
                     prob_otm=0.72, want_to_own=True)
    fat = wheel_fit(spot=100, strike=95, premium=3.0, annualized_roc=1.20,
                    prob_otm=0.72, want_to_own=True)
    print(f"yield discrimination: thin(30%/yr)={thin:.3f}  fat(120%/yr)={fat:.3f}")
    assert fat > thin + 0.10, "a fat weekly must now beat a thin one on wheel-fit"

    # A bad wheel: strike ABOVE spot effective basis (assignment costs more than now).
    bad = free_shares_read(spot=100, strike=104, premium=1.0, annualized_roc=0.04,
                           prob_otm=0.55, want_to_own=True)
    print("bad wheel :", bad)
    assert bad["basis_discount_pct"] < 0, "basis above spot is a negative discount"
    assert bad["wheel_fit"] < r["wheel_fit"], "bad entry must score below the good one"
    print("\nOK: free-shares self-test passed.")


if __name__ == "__main__":
    _selftest()
