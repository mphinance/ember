"""
wheelforge/market_weather.py — a non-blocking MARKET REGIME read (roadmap item).

The score judges each NAME on its own six factors. But a premium seller also wants
one glance at the whole tape before he sells anything: is this a calm market where
selling premium at support is a steady grind, or a stressed one where the premium is
rich for a reason and he should demand a fatter cushion?

The cleanest, cheapest regime read is the VIX term structure: front-month VIX vs
three-month VIX3M.
  - VIX3M > VIX (contango, ratio < 1) is the NORMAL, calm state: near-term fear sits
    below three-month fear, the tape is orderly, sell premium.
  - VIX >= VIX3M (flat / backwardation, ratio >= 1) is stress: fear is front-loaded,
    a shock is being priced NOW. Premium is rich but the risk is real, so be picky.
  - A high absolute VIX is its own stress flag regardless of the curve.

This NEVER gates a per-name score (same discipline as the skew / crowding signals):
it is an informational banner Michael reads, not a silent edit to any pick. Pure, no
deps, fail-open to None so a missing VIX feed just hides the banner.
"""

from __future__ import annotations

# Curve: at/above this VIX/VIX3M ratio the term structure has flattened into stress.
BACKWARDATION_RATIO = 1.00
# Deep contango: comfortably below this the near-term tape is calm.
CONTANGO_RATIO = 0.95
# Absolute VIX bands.
VIX_CALM = 15.0
VIX_HIGH = 28.0


def market_regime(vix, vix3m):
    """Classify the tape from the VIX term structure. Returns a dict the frontend paints
    as a banner, or None if either input is missing/unusable (fail-open)."""
    try:
        v = float(vix)
        v3 = float(vix3m)
    except (TypeError, ValueError):
        return None
    if v <= 0 or v3 <= 0:
        return None

    ratio = v / v3

    # Stress: the curve has inverted (front-month fear >= three-month) OR the absolute
    # level is high. Either way the seller should demand a richer cushion.
    if ratio >= BACKWARDATION_RATIO or v >= VIX_HIGH:
        regime, label = "stressed", "STRESSED"
        if ratio >= BACKWARDATION_RATIO:
            note = ("VIX term structure inverted (near-term fear above 3-month). Premium "
                    "is rich for a reason. Be picky: demand real support and a fatter cushion.")
        else:
            note = ("VIX elevated. Premium is rich but so is the risk. Be picky: sell only "
                    "the safest setups and size down.")
    # Calm: low absolute VIX and a healthy contango. Steady backdrop, but cheap premium,
    # so the edge is in only selling names whose IV is genuinely rich.
    elif v <= VIX_CALM and ratio < CONTANGO_RATIO:
        regime, label = "calm", "CALM"
        note = ("Low VIX, healthy contango. A calm tape to sell premium at support, but "
                "premium is cheap, so be selective and only sell genuinely rich IV.")
    # Normal contango: the default, steady state for the income machine.
    else:
        regime, label = "normal", "NORMAL"
        note = "Normal contango. A steady backdrop to sell premium at support."

    return {
        "vix": round(v, 2),
        "vix3m": round(v3, 2),
        "ratio": round(ratio, 3),
        "regime": regime,
        "label": label,
        "note": note,
    }


def _selftest():
    # Calm: low VIX, steep contango.
    calm = market_regime(13.0, 16.0)
    assert calm and calm["regime"] == "calm", calm
    # Normal: mid VIX, mild contango (ratio between CONTANGO_RATIO and 1.0).
    norm = market_regime(18.0, 19.0)
    assert norm and norm["regime"] == "normal", norm
    # Normal too: low VIX but the curve is nearly flat (ratio >= CONTANGO_RATIO), so not calm.
    norm2 = market_regime(14.0, 14.5)
    assert norm2 and norm2["regime"] == "normal", norm2
    # Stressed by inversion: VIX above VIX3M even at a modest absolute level.
    inv = market_regime(19.0, 18.0)
    assert inv and inv["regime"] == "stressed", inv
    assert "inverted" in inv["note"], inv
    # Stressed by absolute level: high VIX even while the curve is still in contango.
    hi = market_regime(30.0, 33.0)
    assert hi and hi["regime"] == "stressed", hi
    assert hi["ratio"] < 1.0, hi
    # Fail-open on bad / missing inputs.
    assert market_regime(None, 16.0) is None
    assert market_regime(15.0, None) is None
    assert market_regime(0, 16.0) is None
    assert market_regime("x", "y") is None
    print("market_weather self-test passed.")


if __name__ == "__main__":
    _selftest()
