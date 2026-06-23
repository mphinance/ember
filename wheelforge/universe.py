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


def _earnings_days(val):
    """TradingView earnings_release_next_date -> days from today (or None).
    The field comes back as a unix timestamp (sec) or an ISO date; handle both."""
    from datetime import date, datetime, timezone
    if val is None:
        return None
    try:
        if isinstance(val, (int, float)):
            d = datetime.fromtimestamp(float(val), tz=timezone.utc).date()
        else:
            d = date.fromisoformat(str(val)[:10])
        return (d - date.today()).days
    except Exception:
        return None


def screen_universe(limit: int = 30, min_cap: float = 5e9,
                    min_dollar_vol: float = 2e7, price_lo: float = 15.0,
                    price_hi: float = 800.0):
    """Most-liquid, optionable-grade US names, most-liquid first, each carrying its
    days-to-next-earnings (for the avoid gate). Returns a list of
    {ticker, earnings_days}. Fail-open to the staple list (earnings_days None)."""
    try:
        from tradingview_screener import Query, col
        q = (Query()
             .set_markets("america")
             .select("name", "close", "market_cap_basic",
                     "average_volume_90d_calc", "earnings_release_next_date")
             .where(
                 col("market_cap_basic") >= min_cap,
                 col("average_volume_90d_calc") >= (min_dollar_vol / max(price_lo, 1)),
                 col("close") >= price_lo,
                 col("close") <= price_hi,
             )
             .order_by("average_volume_90d_calc", ascending=False)
             .limit(int(limit) * 2))
        _count, df = q.get_scanner_data()
        out, seen = [], set()
        for _, row in df.iterrows():
            s = _clean(row.get("name"))
            if not s or s in seen:
                continue
            seen.add(s)
            out.append({"ticker": s,
                        "earnings_days": _earnings_days(row.get("earnings_release_next_date"))})
            if len(out) >= limit:
                break
        if out:
            return out
    except Exception as exc:
        print(f"  universe: screener unavailable ({exc}); using fallback")
    return [{"ticker": t, "earnings_days": None} for t in FALLBACK[:limit]]


def liquid_universe(limit: int = 30, **kw):
    """Just the tickers (back-compat wrapper over screen_universe)."""
    return [d["ticker"] for d in screen_universe(limit, **kw)]


if __name__ == "__main__":
    u = liquid_universe(30)
    print(f"{len(u)} names:", ", ".join(u))
