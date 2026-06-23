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
    print("OK: structure self-test passed.")


if __name__ == "__main__":
    _selftest()
