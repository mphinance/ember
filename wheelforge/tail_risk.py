"""
wheelforge/tail_risk.py — a GAP-RISK read for the safety factor (ported in spirit from
StrikeForge's tail_risk.py).

The blind spot it closes: WheelForge's safety factor is `prob_otm`, a lognormal
"stays-OTM" estimate. But the lognormal has thin tails. Two names can sit the SAME
distance OTM with the same prob_otm and be wildly different risks: one drifts, the
other gaps 12% overnight on a guide-down and blows clean through your strike before
you can react. A disciplined put seller should treat the chronic gapper as LESS safe
at the same distance. That is what this module measures.

It looks only at DOWNSIDE overnight gaps (open vs the prior close): for a cash-secured
put, the upside gap is a gift, the downside gap is the assignment-at-a-loss that the
smooth prob_otm never saw coming. The metric is driven by the WORST recent gaps (the
move that matters), averaged over a few so one data glitch cannot dominate.

Pure Python (WheelForge carries candle lists, not pandas). Fail-open to 0.0 = "no
evidence of gap risk, do not penalize" so missing/short data never manufactures a
haircut. No third-party deps, no import of scoring (the haircut lives there; this just
emits the 0..1 number it consumes).
"""

from __future__ import annotations


def _clamp01(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return 0.0
    if x != x:  # NaN
        return 0.0
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def _ramp(x, lo, hi):
    """Linear 0..1 as x goes lo..hi (saturating)."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return 0.0
    if hi == lo:
        return 0.0
    return _clamp01((x - lo) / (hi - lo))


def overnight_gaps(candles):
    """Overnight gap returns: today's OPEN vs yesterday's CLOSE (open_i / close_{i-1} - 1).
    A daily candle's high/low/close move is intraday; THIS is the jump you cannot trade
    around. Skips bars with junk fields rather than failing the whole series."""
    gaps = []
    if not candles or len(candles) < 2:
        return gaps
    for i in range(1, len(candles)):
        try:
            prev_close = float(candles[i - 1]["close"])
            today_open = float(candles[i]["open"])
        except (KeyError, TypeError, ValueError):
            continue
        if prev_close > 0:
            gaps.append(today_open / prev_close - 1.0)
    return gaps


# Sub-1% overnight moves are not gaps, they are the normal open. Counting them as "downside
# gaps" would dilute the worst-few average with noise, so only real gaps past this floor count.
NOISE_FLOOR = 0.01


def gap_risk(candles, lookback=60, worst_n=3):
    """A 0..1 tail-risk read for a PUT seller from daily OHLCV, driven by the worst recent
    DOWNSIDE overnight gaps. 0 = well-behaved (no gap past the noise floor), 1 = a chronic
    gapper whose worst overnight drops would jump a far-OTM strike.

    A ~4% worst downside gap is normal market noise (no haircut); ~15%+ is a serious gapper
    (full haircut). Averages the worst `worst_n` REAL gaps (past NOISE_FLOOR) so a single bad
    print cannot define the name, and the day-to-day open wobble cannot dilute it. Returns 0.0
    (fail-open, no penalty) on missing/short/clean data."""
    gaps = overnight_gaps(candles)
    if not gaps:
        return 0.0
    gaps = gaps[-lookback:]
    downs = sorted(g for g in gaps if g < -NOISE_FLOOR)   # real downside gaps, most negative first
    if not downs:
        return 0.0
    worst = downs[:max(1, worst_n)]
    avg_worst = sum(worst) / len(worst)
    return _ramp(abs(avg_worst), 0.04, 0.15)


# ── self-test (keep WheelForge runnable every cycle) ─────────────────────────

def _flat_series(n=80, price=100.0):
    """A calm tape: small, symmetric overnight drift, no jumps."""
    out = []
    p = price
    for i in range(n):
        o = p * (1.0 + (0.002 if i % 2 else -0.002))  # ~0.2% overnight wobble
        out.append({"open": o, "high": o * 1.01, "low": o * 0.99, "close": o})
        p = o
    return out


def _gappy_series():
    """The same calm tape, but with a couple of brutal downside overnight gaps spliced in."""
    s = _flat_series()
    # day 40 opens 12% below the prior close; day 60 opens 9% below.
    s[40]["open"] = s[39]["close"] * 0.88
    s[60]["open"] = s[59]["close"] * 0.91
    return s


def _selftest():
    calm = gap_risk(_flat_series())
    gappy = gap_risk(_gappy_series())
    print(f"gap_risk: calm={round(calm, 3)}  gappy={round(gappy, 3)}")

    assert calm == 0.0, "a calm, gap-free tape must read 0 gap risk (no haircut)"
    assert gappy > 0.5, "a name with 9-12% overnight drops must read as a serious gapper"
    assert gappy <= 1.0, "the read saturates at 1.0"

    # fail-open: junk / too-short data never manufactures a penalty.
    assert gap_risk(None) == 0.0, "no candles -> 0.0 fail-open"
    assert gap_risk([]) == 0.0, "empty -> 0.0"
    assert gap_risk([{"open": 1, "close": 1}]) == 0.0, "one bar -> 0.0 (no gap to measure)"
    assert gap_risk([{"x": 1}, {"y": 2}]) == 0.0, "junk fields -> 0.0, not a crash"

    # only DOWNSIDE gaps count: an upside gapper is a gift to a put seller, not a risk.
    up = _flat_series()
    up[40]["open"] = up[39]["close"] * 1.12   # +12% overnight
    assert gap_risk(up) == 0.0, "an upside-only gap must not haircut put safety"

    print("OK: tail_risk self-test passed.")


if __name__ == "__main__":
    _selftest()
