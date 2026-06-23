"""
wheelforge/universe.py — stop scanning a toy watchlist; screen the real market.

Uses tradingview-screener (no auth, same source StrikeForge's funnel uses) to pull
a big list of liquid, sanely-priced US names that are almost certainly optionable
(large/mid cap + heavy dollar volume), most-liquid first. WheelForge then scores
that universe instead of 8 hand-picked tickers.

Field catalog: reference/tradingview-fields.md (the full menu, for widening this).
Fails open to a static staple list so a screener hiccup never empties the scan.
"""

from __future__ import annotations

# Liquid, optionable staples — the floor if the live screener is unavailable.
FALLBACK = [
    "AAPL", "MSFT", "NVDA", "AMD", "GOOGL", "AMZN", "META", "COST", "TSLA", "NFLX",
    "AVGO", "JPM", "V", "MA", "HD", "WMT", "CRM", "ADBE", "QCOM", "MU",
    "BAC", "DIS", "INTC", "PYPL", "UBER", "COIN", "PLTR", "SHOP", "SMCI", "MRVL",
]


def _clean(sym):
    s = str(sym or "").strip().upper()
    if ":" in s:           # "NASDAQ:AAPL" -> "AAPL"
        s = s.split(":")[-1]
    return s if s.isalpha() else None


def liquid_universe(limit: int = 30, min_cap: float = 5e9,
                    min_dollar_vol: float = 2e7, price_lo: float = 15.0,
                    price_hi: float = 800.0):
    """Most-liquid, optionable-grade US names, most-liquid first. Fail-open."""
    try:
        from tradingview_screener import Query, col
        q = (Query()
             .set_markets("america")
             .select("name", "close", "market_cap_basic", "average_volume_90d_calc")
             .where(
                 col("market_cap_basic") >= min_cap,
                 col("average_volume_90d_calc") >= (min_dollar_vol / max(price_lo, 1)),
                 col("close") >= price_lo,
                 col("close") <= price_hi,
             )
             .order_by("average_volume_90d_calc", ascending=False)
             .limit(int(limit) * 2))   # over-pull, then clean/dedupe to limit
        _count, df = q.get_scanner_data()
        out, seen = [], set()
        for raw in df["name"].tolist():
            s = _clean(raw)
            if s and s not in seen:
                seen.add(s)
                out.append(s)
            if len(out) >= limit:
                break
        if out:
            return out
    except Exception as exc:
        print(f"  universe: screener unavailable ({exc}); using fallback")
    return FALLBACK[:limit]


if __name__ == "__main__":
    u = liquid_universe(30)
    print(f"{len(u)} names:", ", ".join(u))
