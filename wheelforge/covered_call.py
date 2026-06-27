"""
wheelforge/covered_call.py — the wheel's SECOND leg: sell a call against shares you hold.

The CSP scanner is the intake. When Michael gets assigned (the welcome outcome ~15-20%
of the time), the work does not stop, it FLIPS: now he owns 100 shares at a known basis
and the income machine keeps running by selling a covered call to grind that basis down.
GOAL.md names this leg ("reduce basis without capping away a name you meant to keep"),
but until now the engine only ever priced puts. This module prices the other half.

The decision is small and disciplined: sell the LOWEST out-of-the-money call at or above
your cost basis. OTM keeps the shares working with room to run; >= basis means that if the
shares get called away you sell at or above what you paid, so the trade is pure basis
reduction plus any gain up to the strike, never a forced loss to harvest premium.

Pure, no network, self-tested. Mirrors build_site_data's put math (same BS, same median
prob_otm, same RoC shape) so the two legs are graded on one ruler. The network (the live
call chain) lives in the CLI, exactly like roll_advisor. No em dashes (Michael's rule).
"""

from __future__ import annotations

import math

from wheelforge.scoring import score_contract

R = 0.045  # risk-free, matches build_site_data._iv_from_put


def _norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _bs_call(S, K, t, r, sigma):
    """Black-Scholes European call value (mirror of build_site_data._bs_put)."""
    if S <= 0 or K <= 0 or t <= 0 or sigma <= 0:
        return 0.0
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)
    return S * _norm_cdf(d1) - K * math.exp(-r * t) * _norm_cdf(d2)


def _iv_from_call(premium, S, K, t, r):
    """Back implied vol out of a REAL call premium by bisection. Same reason as the put
    side: yfinance's quoted impliedVolatility is stale junk on many strikes, and a wrong
    IV poisons prob_otm and the VRP. The premium is real, so solve for the vol that
    reproduces it. Returns None if it cannot."""
    if not (premium and premium > 0 and S > 0 and K > 0 and t > 0):
        return None
    lo, hi = 0.01, 5.0
    if _bs_call(S, K, t, r, hi) < premium:   # richer than even 500% vol -> bail
        return None
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if _bs_call(S, K, t, r, mid) > premium:
            hi = mid
        else:
            lo = mid
    iv = (lo + hi) / 2.0
    return iv if 0.01 < iv < 5.0 else None


def call_prob_otm(spot, strike, iv, t):
    """P(a sold call expires OTM) = P(S_T < K) = you KEEP the shares and the premium.
    Median measure (drift 0), the exact complement of build_site_data's put prob_otm, so a
    call and a put are scored on the same safety ruler. A high number means the shares are
    unlikely to be called away this cycle."""
    if not (spot > 0 and strike > 0 and iv > 0 and t > 0):
        return 0.0
    z = (math.log(spot / strike) + (0.0 - 0.5 * iv * iv) * t) / (iv * math.sqrt(t))
    return _norm_cdf(-z)   # call-OTM is the complement of the put-OTM N(z)


def annualized_roc(premium, basis, dte):
    """Annualized return the call earns on the capital it works against. For a covered
    call the capital is the cost basis of the shares you already hold (not a strike of
    cash), so RoC = premium / basis, annualized. Same shape as the CSP _annualized_roc,
    anchored on what THIS leg actually ties up."""
    return (premium / basis) * (365.0 / dte) if (basis > 0 and dte > 0) else 0.0


def pick_call(spot, basis, candidates):
    """Choose the call to sell: the LOWEST out-of-the-money strike at or above the cost
    basis. OTM (strike > spot) keeps upside room; strike >= basis means a call-away sells
    at or above what you paid, so the trade is basis reduction plus gain-to-strike, never a
    forced loss. Returns the chosen candidate dict, or None if nothing qualifies (e.g. the
    shares are so far underwater no OTM strike reaches the basis)."""
    elig = [c for c in candidates
            if (c.get("strike") or 0) > spot
            and (c.get("strike") or 0) >= basis
            and (c.get("premium") or 0) > 0]
    return min(elig, key=lambda c: c["strike"]) if elig else None


def covered_call_read(spot, basis, dte, candidates, exp=None, rv=None, iv_rank=None,
                      days_to_earnings=None, want_to_own=True, trend_align=None):
    """The full covered-call read for one held position. Picks the strike, prices it,
    scores it through the SAME score_contract path the CSP scanner uses (direction CC), and
    returns a plain dict with the basis-reduction read a wheeler actually asks for. Returns
    None when no OTM strike reaches the basis. trend_align defaults neutral until a caller
    feeds a real structure read (a known simplification, noted in GOAL)."""
    spot = float(spot); basis = float(basis); dte = int(dte)
    pick = pick_call(spot, basis, candidates)
    if not pick:
        return None
    strike = float(pick["strike"]); premium = float(pick["premium"])
    bid = pick.get("bid"); ask = pick.get("ask")
    oi = pick.get("open_interest"); vol = pick.get("volume")
    t = dte / 365.0

    # Trust the real premium over the quoted IV: solve IV from the mid, fall back to the
    # quoted IV, then to realized vol (the same ladder the put path uses).
    solved = _iv_from_call(premium, spot, strike, t, R)
    qiv = pick.get("iv")
    if solved:
        iv = solved
    elif qiv and rv and 0.33 * rv <= qiv <= 4 * rv:
        iv = qiv
    else:
        iv = rv or 0.25

    prob_otm = call_prob_otm(spot, strike, iv, t)
    roc = annualized_roc(premium, basis, dte)
    # basis_discount here is the per-cycle basis CUT (free_shares_score CC path ramps 0..5%):
    # how much of the basis this one call knocks off, the covered-call analog of the put's
    # assignment-basis discount.
    basis_cut = premium / basis if basis > 0 else 0.0

    contract = {
        "opt_type": "call", "iv": iv, "rv": rv, "iv_rank": iv_rank,
        "prob_otm": prob_otm, "bid": bid, "ask": ask,
        "open_interest": oi, "volume": vol,
        "annualized_roc": roc, "basis_discount": basis_cut,
        "dte": dte, "days_to_earnings": days_to_earnings,
        "want_to_own": want_to_own,
        "trend_align": 0.5 if trend_align is None else trend_align,
    }
    scored = score_contract(contract)

    new_basis = max(0.0, basis - premium)
    called_gain = (strike - basis) / basis if basis > 0 else 0.0
    return {
        **scored,                                  # score, grade, direction, avoid, factors, why
        "strike": round(strike, 2),
        "premium": round(premium, 2),
        "dte": dte,
        "exp": exp,
        "prob_otm": round(prob_otm * 100, 1),
        "basis_reduction_pct": round(basis_cut * 100, 2),
        "new_basis": round(new_basis, 2),
        "annualized_roc": round(roc * 100, 1),
        "called_away_gain_pct": round(called_gain * 100, 1),
        "summary": _summary(strike, premium, basis, new_basis, basis_cut, roc, called_gain),
    }


def _summary(strike, premium, basis, new_basis, basis_cut, roc, called_gain):
    if called_gain >= 0:
        return (f"Sell the ${strike:,.2f} call for ${premium:.2f}: grinds your basis from "
                f"${basis:,.2f} to ${new_basis:,.2f} ({basis_cut*100:.1f}% this cycle, "
                f"{roc*100:.0f}% annualized). If called away you still sell "
                f"{called_gain*100:.1f}% above basis, so it is a win either way.")
    return (f"Sell the ${strike:,.2f} call for ${premium:.2f}: ${basis_cut*100:.1f}% basis "
            f"reduction this cycle, but the strike sits below your ${basis:,.2f} basis, so a "
            f"call-away locks a loss. Income only, not a clean basis grind.")


# ── self-test (keep WheelForge runnable every cycle) ─────────────────────────

def _selftest():
    # You hold 100 shares of a $100 name bought at $95 (a put got assigned, now in profit).
    # Candidate calls around spot; the lowest OTM strike at/above basis is the $105.
    spot, basis, dte = 100.0, 95.0, 30
    cands = [
        {"strike": 90, "premium": 11.0, "bid": 10.9, "ask": 11.1, "open_interest": 800, "volume": 50},
        {"strike": 100, "premium": 3.0, "bid": 2.95, "ask": 3.05, "open_interest": 2500, "volume": 400},  # ATM, not OTM
        {"strike": 105, "premium": 1.8, "bid": 1.75, "ask": 1.85, "open_interest": 3000, "volume": 600},
        {"strike": 110, "premium": 0.9, "bid": 0.85, "ask": 0.95, "open_interest": 1500, "volume": 200},
    ]
    chosen = pick_call(spot, basis, cands)
    assert chosen["strike"] == 105, "lowest OTM strike at/above basis is the 105, not the ITM 90 or ATM 100"

    r = covered_call_read(spot, basis, dte, cands, exp="2026-07-31", rv=0.30, iv_rank=55,
                          want_to_own=True)
    print("covered call:", r["strike"], "premium", r["premium"], "score", r["score"],
          r["grade"], "|", r["summary"])
    assert r["direction"] == "covered call", "a call must read as a covered call"
    assert r["strike"] == 105.0
    assert r["new_basis"] == round(basis - 1.8, 2), "premium reduces the basis"
    assert r["called_away_gain_pct"] > 0, "called away at 105 from a 95 basis is a gain"
    assert 0 < r["prob_otm"] < 100, "prob the call stays OTM is a real probability"
    assert r["annualized_roc"] > 0, "the call earns a positive annualized RoC on the basis"

    # Underwater shares: bought at $108, OTM strikes that reach the basis are far away and
    # thin. The 110 is the lowest OTM strike >= 108; the read must flag the slim gain.
    under = covered_call_read(spot=100.0, basis=108.0, dte=30, candidates=cands,
                              rv=0.30, want_to_own=True)
    print("underwater  :", under["strike"], "|", under["summary"])
    assert under["strike"] == 110.0, "must reach above the 108 basis, so the 110, not the 105"

    # Deeply underwater: no OTM strike reaches a $200 basis -> no clean covered call exists.
    none = covered_call_read(spot=100.0, basis=200.0, dte=30, candidates=cands, rv=0.30)
    assert none is None, "no OTM strike at/above a far basis means no covered call to sell"

    # prob_otm is the complement of a put at the same strike (same median measure): a call
    # struck above spot is MORE likely to expire OTM than a put struck there, and both sit
    # in (0,1). Sanity-check the math directly.
    p = call_prob_otm(spot=100, strike=110, iv=0.30, t=30 / 365.0)
    assert 0.5 < p < 1.0, "an OTM call (strike well above spot) should usually expire OTM"

    # Earnings veto rides through the shared scoring path: a print before expiry hard-avoids.
    veto = covered_call_read(spot, basis, dte, cands, rv=0.30, days_to_earnings=10)
    assert veto["avoid"] and veto["score"] == 0.0, "earnings before expiry must veto the CC too"
    assert veto["grade"] == "F", "a vetoed covered call grades F honestly"

    print("\nOK: covered-call self-test passed.")


if __name__ == "__main__":
    _selftest()
