"""
wheelforge/vol_models.py — composite realized vol (ported from VoPR).

The review flagged that WheelForge judged premium richness (IV vs realized vol) using
only a single close-to-close RV, which throws away all the intraday range information.
This ports VoPR's `scanner/volatility_models.py`: four classical estimators blended.
A better RV denominator makes the VRP (and the whole richness factor) honest.

  - Close-to-Close: stdev of log returns. Baseline, ignores intraday.
  - Parkinson:      uses High/Low range, ~5x more efficient.
  - Garman-Klass:   uses all four OHLC, most efficient with no drift.
  - Rogers-Satchell: unbiased even when the name is TRENDING (key for selling premium
                     on names that are moving). Weighted heaviest.

Pure Python over WheelForge's candle dicts (open/high/low/close). All annualized.
Fail-open to 0.0 per estimator; the composite renormalizes over the ones that worked.
"""

from __future__ import annotations

import math
import statistics

TD = 252.0  # trading days per year
LN2 = math.log(2.0)

# Adapted from VoPR's default blend: lean on the range estimators, and on
# Rogers-Satchell most (it stays honest when the stock is trending).
WEIGHTS = (0.15, 0.25, 0.30, 0.30)  # CC, Parkinson, Garman-Klass, Rogers-Satchell


def _ohlc(c):
    try:
        o, h, l, cl = float(c["open"]), float(c["high"]), float(c["low"]), float(c["close"])
        if o > 0 and h > 0 and l > 0 and cl > 0 and h >= l:
            return o, h, l, cl
    except (KeyError, TypeError, ValueError):
        pass
    return None


def close_to_close_vol(candles, period=20):
    closes = [float(c["close"]) for c in candles[-(period + 1):] if c.get("close")]
    if len(closes) < 3:
        return 0.0
    rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes)) if closes[i - 1] > 0]
    if len(rets) < 2:
        return 0.0
    return statistics.stdev(rets) * math.sqrt(TD)


def parkinson_vol(candles, period=20):
    rows = [r for r in (_ohlc(c) for c in candles[-period:]) if r]
    if len(rows) < 2:
        return 0.0
    s = sum(math.log(h / l) ** 2 for _, h, l, _ in rows)
    n = len(rows)
    var = (1.0 / (4.0 * n * LN2)) * s
    return math.sqrt(var * TD) if var > 0 else 0.0


def garman_klass_vol(candles, period=20):
    rows = [r for r in (_ohlc(c) for c in candles[-period:]) if r]
    if len(rows) < 2:
        return 0.0
    n = len(rows)
    var = (1.0 / n) * sum(
        0.5 * math.log(h / l) ** 2 - (2.0 * LN2 - 1.0) * math.log(cl / o) ** 2
        for o, h, l, cl in rows
    )
    return math.sqrt(var * TD) if var > 0 else 0.0


def rogers_satchell_vol(candles, period=20):
    rows = [r for r in (_ohlc(c) for c in candles[-period:]) if r]
    if len(rows) < 2:
        return 0.0
    n = len(rows)
    var = (1.0 / n) * sum(
        math.log(h / cl) * math.log(h / o) + math.log(l / cl) * math.log(l / o)
        for o, h, l, cl in rows
    )
    return math.sqrt(var * TD) if var > 0 else 0.0


def composite_realized_vol(candles, period=20, weights=WEIGHTS):
    """Weighted blend of the four estimators, renormalized over the ones that
    returned a positive value. 0.0 only if everything failed (caller falls back)."""
    if not candles:
        return 0.0
    est = [
        close_to_close_vol(candles, period),
        parkinson_vol(candles, period),
        garman_klass_vol(candles, period),
        rogers_satchell_vol(candles, period),
    ]
    pairs = [(w, v) for w, v in zip(weights, est) if v > 0]
    if not pairs:
        return 0.0
    wsum = sum(w for w, _ in pairs)
    return sum(w * v for w, v in pairs) / wsum if wsum > 0 else 0.0


def _selftest():
    # Synthetic candles with a steady intraday range and a mild trend.
    cs, p = [], 100.0
    for i in range(40):
        p *= 1.003
        cs.append({"open": p * 0.998, "high": p * 1.02, "low": p * 0.985, "close": p})
    cc = close_to_close_vol(cs); pk = parkinson_vol(cs)
    gk = garman_klass_vol(cs); rs = rogers_satchell_vol(cs)
    comp = composite_realized_vol(cs)
    print(f"CC={cc:.3f} Park={pk:.3f} GK={gk:.3f} RS={rs:.3f} -> composite={comp:.3f}")
    assert all(v > 0 for v in (pk, gk, rs, comp)), "range estimators + composite must be > 0"
    assert 0.0 < comp < 3.0, "composite vol should be a sane fraction"
    # composite should sit among the estimators, not wildly outside them
    assert min(cc, pk, gk, rs) * 0.5 <= comp <= max(cc, pk, gk, rs) * 1.5
    assert composite_realized_vol([]) == 0.0
    print("OK: vol-models self-test passed.")


if __name__ == "__main__":
    _selftest()
