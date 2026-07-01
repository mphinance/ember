"""
wheelforge/patterns.py — the few price-action patterns a PUT SELLER actually trades on.

Michael's structure read (definition-of-best #6) is not the textbook chart-pattern zoo.
For a cash-secured-put seller only a handful of OHLCV shapes change the sell decision:
  - SUPPORT HOLD (bounce): price sits low in its Keltner channel but has RECOVERED off a
    recent low. Buyers are defending the floor you want to sell under. The A+ put-sell setup.
  - BREAKDOWN: price is at/under the lower Keltner band and still falling. The floor gave
    way, this is a falling knife, do not sell puts into it.
  - DOWNTREND: sustained lower closes, price low in the channel, no bounce yet. Wait.
  - COILING: a tight range mid-channel, volatility compressed. Premium is fair both sides.
Anything else -> no strong read (tag "none").

This is a per-name TAG only. Like every other WheelForge signal it is a VISIBLE flag he
reads, not a silent rescore of the structure factor (structure_with_floor already owns
that). Pure, no network, fail-open to a neutral no-read. No em dashes in user strings.
"""

from __future__ import annotations

from wheelforge.structure import keltner_bands, keltner_position

_NEUTRAL = {"tag": "none", "bias": "neutral", "read": ""}


def _series(candles):
    """Coerce candle dicts to (closes, highs, lows) float lists, or None on bad data."""
    closes, highs, lows = [], [], []
    for c in candles:
        try:
            closes.append(float(c["close"]))
            highs.append(float(c["high"]))
            lows.append(float(c["low"]))
        except (KeyError, TypeError, ValueError):
            return None
    return closes, highs, lows


def read_pattern(candles, lookback=10):
    """Classify the one price-action pattern that changes a put-sell decision.

    Returns {tag, bias, read}: tag in {support_hold, breakdown, downtrend, coiling, none},
    bias in {good, avoid, neutral}, read = one plain-English line (empty for 'none').
    Fails open to the neutral no-read on short/bad history so the caller can ignore it."""
    if not candles or len(candles) < 21:
        return dict(_NEUTRAL)
    parts = _series(candles)
    bands = keltner_bands(candles)
    kp = keltner_position(candles)
    if parts is None or bands is None or kp is None:
        return dict(_NEUTRAL)
    closes, highs, lows = parts
    spot = closes[-1]
    if spot <= 0:
        return dict(_NEUTRAL)

    n = min(lookback, len(closes) - 1)
    win_highs, win_lows = highs[-n:], lows[-n:]
    ret = spot / closes[-n] - 1.0                       # trend over the window
    k3 = min(3, n)
    ret3 = spot / closes[-k3] - 1.0                     # trend over the last few bars
    rng = (max(win_highs) - min(win_lows)) / spot       # range tightness (fraction of spot)
    lo = min(win_lows)
    dipped = lo > 0 and lo <= spot * 0.96              # a real dip happened (>= 4% low)
    recovered = lo > 0 and spot >= lo * 1.02           # then bounced >= 2% off that low

    # 1) BREAKDOWN: at/under the lower band with the drop CONCENTRATED in the last few
    # bars, a fresh violent break of a floor that had been holding. (A steady grind lower
    # falls through to DOWNTREND below: same 'wait' verdict, but an honestly different shape.)
    if kp <= 0.15 and ret3 <= -0.05:
        return {"tag": "breakdown", "bias": "avoid",
                "read": ("Slicing below the Keltner floor and still falling. The support "
                         "gave way, a falling knife. Do not sell puts into it.")}
    # 2) SUPPORT HOLD (bounce): low in the channel, dipped to a recent low and recovered off
    # it, not still falling. Buyers defended the floor you sell under.
    if 0.10 < kp <= 0.50 and dipped and recovered and ret > -0.02:
        return {"tag": "support_hold", "bias": "good",
                "read": ("Holding low in its channel and bouncing off a recent low. Buyers "
                         "are defending the floor you sell under.")}
    # 3) DOWNTREND: sustained lower closes, low in the channel, no bounce yet.
    if ret <= -0.06 and kp < 0.40:
        return {"tag": "downtrend", "bias": "avoid",
                "read": ("Lower highs and lower closes with no bounce yet. Wait for it to "
                         "stop falling before selling puts.")}
    # 4) COILING: a tight range mid-channel, volatility compressed.
    if rng <= 0.06 and 0.30 <= kp <= 0.75:
        return {"tag": "coiling", "bias": "neutral",
                "read": "Coiling in a tight range. Premium is fair on both sides."}
    return dict(_NEUTRAL)


def _selftest():
    def series(step, base=100.0, band=0.01, bars=60):
        out, p = [], base
        for _ in range(bars):
            p *= (1.0 + step)
            out.append({"high": p * (1 + band), "low": p * (1 - band), "close": p})
        return out

    # short history -> fail open, never guess
    assert read_pattern([])["tag"] == "none"
    assert read_pattern(series(0.004, bars=10))["tag"] == "none", "too few bars -> no read"

    # DOWNTREND: a steady grind lower, price low in the channel, no bounce.
    dn = read_pattern(series(-0.010))
    print("downtrend:", dn)
    assert dn["tag"] == "downtrend" and dn["bias"] == "avoid"

    # BREAKDOWN: a base, then an accelerating slide that closes at/under the lower band.
    base = series(0.0, bars=30)                     # flat base builds a tight channel
    p = base[-1]["close"]
    for _ in range(8):                              # then fall hard, closing at the lows
        p *= 0.97
        base.append({"high": p * 1.005, "low": p * 0.99, "close": p * 0.992})
    bd = read_pattern(base)
    print("breakdown:", bd)
    assert bd["tag"] == "breakdown" and bd["bias"] == "avoid"

    # SUPPORT HOLD: a base, a dip toward the floor, then a recovery close off the low.
    hold = series(0.0, bars=30)
    p = hold[-1]["close"]
    for f in (0.97, 0.95, 0.94):                    # dip down toward support
        q = p * f
        hold.append({"high": p * 1.002, "low": q * 0.998, "close": q})
    low = hold[-1]["close"]
    for f in (1.015, 1.03):                         # bounce back up off the low
        low *= f
        hold.append({"high": low * 1.005, "low": low * 0.99, "close": low})
    sh = read_pattern(hold)
    print("support_hold:", sh)
    assert sh["tag"] == "support_hold" and sh["bias"] == "good"

    # COILING: a tight flat range mid-channel.
    coil = read_pattern(series(0.0, band=0.004))
    print("coiling:", coil)
    assert coil["tag"] == "coiling" and coil["bias"] == "neutral"

    # A calm uptrend sits high in the channel: none of the above should fire.
    up = read_pattern(series(0.004, band=0.02))
    print("uptrend:", up)
    assert up["tag"] in ("none", "coiling"), "a healthy uptrend is not a warning pattern"

    print("\nOK: patterns self-test passed.")


if __name__ == "__main__":
    _selftest()
