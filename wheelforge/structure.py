"""
wheelforge/structure.py — a REAL structure read (ported from VoPR's Keltner position).

The code review caught it: WheelForge's `trend_align` was a hardcoded 0.6, so the
"structure agrees" pillar of the score meant nothing. This ports VoPR's
`scanner/technicals.py::calculate_price_position`: where does price sit in its Keltner
Channel (SMA20 +/- 3 * ATR14, Wilder)? Score 0..1, where 0 = at/below the lower band
(falling, a knife you should not sell puts into) and 1 = at/above the upper band
(holding up). For a cash-secured-put seller, higher is safer, so the score IS the
structure factor: it drops when a name is breaking down.

Pure Python (WheelForge carries candle lists, not pandas). Fail-open to None so the
caller can default to neutral. No third-party deps.
"""

from __future__ import annotations


def _bar(c):
    """Coerce a candle (dict from build_site_data) to (high, low, close)."""
    try:
        return float(c["high"]), float(c["low"]), float(c["close"])
    except (KeyError, TypeError, ValueError):
        return None


def wilder_atr(candles, period=14):
    """Wilder's ATR over candle dicts. None if too short."""
    if not candles or len(candles) < period + 1:
        return None
    trs = []
    for i in range(1, len(candles)):
        cur, prev = _bar(candles[i]), _bar(candles[i - 1])
        if not cur or not prev:
            return None
        h, l, _ = cur
        pc = prev[2]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    if len(trs) < period:
        return None
    atr = sum(trs[:period]) / period            # seed = SMA of first `period` TRs
    for tr in trs[period:]:
        atr = (atr * (period - 1) + tr) / period  # Wilder smoothing
    return atr


def keltner_position(candles, sma_period=20, atr_period=14, mult=3.0):
    """Where spot sits in its Keltner Channel, 0..1 (VoPR's price-position score).
    0 = at/below the lower band (bearish), 0.5 = at the SMA, 1 = at/above the upper.
    Returns None if there is not enough history (caller defaults to neutral 0.5)."""
    need = max(sma_period, atr_period) + 1
    if not candles or len(candles) < need:
        return None
    closes = []
    for c in candles:
        b = _bar(c)
        if not b:
            return None
        closes.append(b[2])
    spot = closes[-1]
    sma = sum(closes[-sma_period:]) / sma_period
    atr = wilder_atr(candles, atr_period)
    if atr is None or atr <= 0:
        return None
    upper, lower = sma + mult * atr, sma - mult * atr
    width = upper - lower
    if width <= 0:
        return 0.5
    return max(0.0, min(1.0, (spot - lower) / width))


def keltner_bands(candles, sma_period=20, atr_period=14, mult=3.0):
    """The raw Keltner levels for drawing on the chart: {upper, sma, lower}.
    None if not enough history."""
    need = max(sma_period, atr_period) + 1
    if not candles or len(candles) < need:
        return None
    closes = []
    for c in candles:
        b = _bar(c)
        if not b:
            return None
        closes.append(b[2])
    sma = sum(closes[-sma_period:]) / sma_period
    atr = wilder_atr(candles, atr_period)
    if atr is None or atr <= 0:
        return None
    return {"upper": round(sma + mult * atr, 2), "sma": round(sma, 2),
            "lower": round(sma - mult * atr, 2)}


def support_floor_score(strike, support, spot):
    """How good is the structural FLOOR under this put strike? Michael's method is to
    sell the put AT major support and trust it, so the A+ setup is a strike sitting just
    ABOVE a real price-action support level: genuine demand sits BELOW where you sold.
    The worst setup is a strike at or below support, selling THROUGH the floor into the
    void where nothing holds price up.

    Returns 0..1 (1 = strike on/just above the floor, 0 = no useful floor below), or
    None when there is no detected support so the caller can stay on the trend read.
    We do NOT penalize a missing level as if it were 'nothing below': our pivot detector
    can simply fail to find a tested level. Only the clear bad case (selling through a
    known floor) is penalized."""
    try:
        strike = float(strike); spot = float(spot)
    except (TypeError, ValueError):
        return None
    if not support or strike <= 0 or spot <= 0:
        return None
    support = float(support)
    if support > strike:
        # strike BELOW support: selling THROUGH the floor, into the void below it. No
        # structural protection, the worst case for a put seller. (strike == support is
        # the at-support ideal and falls through to gap == 0 -> 1.0 below.)
        return 0.15
    # support at/below the strike: how close is the floor, as a fraction of spot? A
    # floor right under the strike (small gap) is ideal; far below means a long way to
    # fall before demand shows up. 0% gap = 1.0, >=12% below = no useful floor (0).
    gap = (strike - support) / spot
    s = 1.0 - gap / 0.12
    return max(0.0, min(1.0, s))


def structure_with_floor(keltner, floor, k_w=0.6):
    """Blend the broad trend read (Keltner position: is the NAME holding up) with the
    per-strike support floor (is there real demand just under THIS strike) into the
    single 0..1 structure factor. When there is no detected floor, the trend read stands
    alone. keltner defaults to neutral 0.5 if missing."""
    k = 0.5 if keltner is None else max(0.0, min(1.0, float(keltner)))
    if floor is None:
        return k
    f = max(0.0, min(1.0, float(floor)))
    return max(0.0, min(1.0, k_w * k + (1.0 - k_w) * f))


def _selftest():
    def series(step):
        # build candles with a tight high/low around a trending close
        out, p = [], 100.0
        for i in range(60):
            p *= (1.0 + step)
            out.append({"high": p * 1.01, "low": p * 0.99, "close": p})
        return out

    up = keltner_position(series(0.004))
    flat = keltner_position(series(0.0))
    down = keltner_position(series(-0.004))
    print(f"up={up}  flat={flat}  down={down}")
    assert up is not None and up >= 0.6, "an uptrend should sit high in the channel"
    assert down is not None and down <= 0.4, "a downtrend should sit low (do not sell into it)"
    assert up > down, "uptrend must score above downtrend"
    assert keltner_position([], ) is None, "no data -> None (caller defaults neutral)"

    # support-floor factor: spot 100, support 90.
    on_floor = support_floor_score(strike=90, support=90, spot=100)   # struck AT support
    just_above = support_floor_score(strike=92, support=90, spot=100) # floor 2% under
    far_above = support_floor_score(strike=99, support=90, spot=100)  # floor 9% under
    thru_floor = support_floor_score(strike=88, support=90, spot=100) # sold BELOW support
    no_floor = support_floor_score(strike=95, support=None, spot=100)
    print(f"floor: on={on_floor} near={just_above} far={far_above} "
          f"through={thru_floor} none={no_floor}")
    assert on_floor == 1.0, "a strike on the floor should max the support score"
    assert just_above > far_above, "a closer floor must score above a distant one"
    assert thru_floor <= 0.2, "selling through the floor must score near zero"
    assert no_floor is None, "no detected support -> None (caller keeps the trend read)"

    # blend: a strong floor should LIFT a neutral trend; through-the-floor should DRAG it.
    lifted = structure_with_floor(keltner=0.5, floor=1.0)
    dragged = structure_with_floor(keltner=0.5, floor=0.15)
    bare = structure_with_floor(keltner=0.7, floor=None)
    assert lifted > 0.5 > dragged, "the floor must move the structure factor both ways"
    assert bare == 0.7, "no floor -> the Keltner read stands alone"
    print("OK: structure self-test passed.")


if __name__ == "__main__":
    _selftest()
