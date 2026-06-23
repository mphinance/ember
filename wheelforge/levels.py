"""
wheelforge/levels.py — major price-action support & resistance, per ticker.

The chart already draws the Keltner VOLATILITY walls. This adds the PRICE-ACTION
levels: the actual horizontals a stock has bounced off (support) and rejected from
(resistance), found from swing pivots in the OHLCV. "Major" = the level that has been
TESTED the most (a price the market keeps respecting), nearest-in-play as the tiebreak.

Pure Python over WheelForge's candle dicts. Returns (support, resistance) below/above
spot, either may be None. No deps.
"""

from __future__ import annotations


def _hi(c):
    try: return float(c["high"])
    except (KeyError, TypeError, ValueError): return None


def _lo(c):
    try: return float(c["low"])
    except (KeyError, TypeError, ValueError): return None


def _pivots(candles, win):
    """Swing pivot highs/lows: a bar that is the extreme within +/- win bars."""
    n = len(candles)
    highs = [_hi(c) for c in candles]
    lows = [_lo(c) for c in candles]
    piv_hi, piv_lo = [], []
    for i in range(win, n - win):
        h, l = highs[i], lows[i]
        if h is None or l is None:
            continue
        seg_h = [x for x in highs[i - win:i + win + 1] if x is not None]
        seg_l = [x for x in lows[i - win:i + win + 1] if x is not None]
        if seg_h and h >= max(seg_h):
            piv_hi.append((i, h))
        if seg_l and l <= min(seg_l):
            piv_lo.append((i, l))
    return piv_hi, piv_lo


def _cluster(pivs, tol):
    """Merge pivots within tol (fractional) into tested levels: {level, touches, last}."""
    clusters = []
    for idx, price in pivs:
        placed = False
        for c in clusters:
            if abs(price - c["level"]) / c["level"] <= tol:
                c["level"] = (c["level"] * c["touches"] + price) / (c["touches"] + 1)
                c["touches"] += 1
                c["last"] = max(c["last"], idx)
                placed = True
                break
        if not placed:
            clusters.append({"level": price, "touches": 1, "last": idx})
    return clusters


def support_resistance(candles, spot, win=5, tol=0.015):
    """Major price-action support (below spot) + resistance (above spot).
    Major = most-tested level; tiebreak nearer to spot. Returns (support, resistance),
    either None. Needs enough history."""
    if not candles or len(candles) < 2 * win + 10 or not spot or spot <= 0:
        return None, None
    piv_hi, piv_lo = _pivots(candles, win)
    hi_c = _cluster(piv_hi, tol)
    lo_c = _cluster(piv_lo, tol)

    def pick(clusters, above):
        cand = [c for c in clusters
                if (c["level"] > spot if above else c["level"] < spot)]
        if not cand:
            return None
        # most touches first; tiebreak nearer to spot, then more recent
        cand.sort(key=lambda c: (c["touches"], -abs(c["level"] - spot), c["last"]),
                  reverse=True)
        return round(cand[0]["level"], 2)

    return pick(lo_c, above=False), pick(hi_c, above=True)


def _selftest():
    # A stock that keeps bouncing off ~100 (support) and rejecting ~120 (resistance),
    # currently at ~110. Build candles that touch those levels repeatedly.
    cs = []
    seq = [110, 118, 119, 112, 101, 100.5, 108, 120, 119.5, 113, 100, 102, 115,
           121, 118, 105, 99.5, 101, 112, 120.5, 110]
    for p in seq:
        cs.append({"high": p * 1.005, "low": p * 0.995, "close": p})
    # pad so there are enough bars and pivots resolve
    cs = cs + cs + cs
    sup, res = support_resistance(cs, spot=110, win=2, tol=0.02)
    print(f"support={sup}  resistance={res}")
    assert sup is not None and 98 <= sup <= 103, "support should sit near 100"
    assert res is not None and 118 <= res <= 122, "resistance should sit near 120"
    assert sup < 110 < res, "support below spot, resistance above"
    assert support_resistance([], 100) == (None, None)
    print("OK: levels self-test passed.")


if __name__ == "__main__":
    _selftest()
