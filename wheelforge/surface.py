"""
wheelforge/surface.py — the volatility-surface reads a PUT seller cares about.

Ported per GOAL.md Phase 4 (StrikeForge surface.py), kept to what changes a
cash-secured-put decision. The first read is PUT SKEW: how much richer the OTM put's
implied vol is than the at-the-money put's. When OTM puts are bid up relative to ATM,
the market is paying extra for downside protection at exactly the strike a CSP seller
collects on, so that fear is the seller's edge, not his enemy.

Pure functions, no network, fully testable. The chain read (pulling the ATM IV off the
puts frame) lives in build_site_data, mirroring how levels/structure stay network-free.

No third-party deps. No em dashes in user-facing strings (Michael's rule).
"""

from __future__ import annotations


def put_skew(otm_iv, atm_iv):
    """Relative put skew: (otm_iv - atm_iv) / atm_iv, comparing the OTM put we would SELL
    against the ATM put on the same chain. Positive = OTM puts richer than ATM = downside
    fear priced into the very strike the seller is paid on (good for him). Negative = the
    OTM put is CHEAPER than ATM (a call-skewed / melt-up tape), no downside premium to
    harvest. Returns a float (may be negative), or None when either IV is missing/non-positive
    so a degraded chain never manufactures a skew signal (fail-open)."""
    try:
        o = float(otm_iv)
        a = float(atm_iv)
    except (TypeError, ValueError):
        return None
    if o <= 0 or a <= 0:
        return None
    return (o - a) / a


def _selftest():
    # OTM put 18% richer than ATM -> +0.18 skew (the routine NVDA-weekly read).
    s = put_skew(0.59, 0.50)
    assert abs(s - 0.18) < 1e-9, f"18% richer OTM put should read +0.18 skew, got {s}"
    # Flat surface -> 0 skew (no edge to harvest, no penalty either).
    assert put_skew(0.40, 0.40) == 0.0, "a flat vol surface should read 0 skew"
    # Call-skewed tape: OTM put CHEAPER than ATM -> negative skew (no downside premium).
    assert put_skew(0.40, 0.50) < 0, "an OTM put cheaper than ATM should read negative skew"
    # Fail-open: any missing / non-positive IV yields None, never a fabricated number.
    assert put_skew(None, 0.50) is None, "missing OTM IV -> None"
    assert put_skew(0.59, None) is None, "missing ATM IV -> None"
    assert put_skew(0.59, 0.0) is None, "zero ATM IV -> None (no divide)"
    assert put_skew(-0.1, 0.5) is None, "negative OTM IV -> None"
    assert put_skew("x", 0.5) is None, "junk IV -> None"
    print("put_skew: OTM 59% vs ATM 50% ->", round(s, 3), "(downside fear priced rich)")
    print("\nOK: WheelForge surface self-test passed.")


if __name__ == "__main__":
    _selftest()
