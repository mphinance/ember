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

# High-IV weeklies Michael actually watches. The Volatility.M screen returns the top ~11
# by vol on a given day, so a name like MSTR or COIN can rank 12th and silently vanish from
# the scan exactly on a week its premium is richest. These are SEEDED into the high-IV lane
# so they are never missed. Seeded by NAME (screen_universe ranks a slice; this screens for
# the exact symbols) so each still carries its REAL earnings date + sector — the earnings
# veto is never disabled for a seed.
HIGH_IV_SEEDS = [
    "COIN", "HOOD", "MSTR", "RDDT", "PLTR", "MARA", "RIOT",
    "AFRM", "SOFI", "CVNA", "IONQ", "RGTI", "SMCI", "APP",
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
                    price_hi: float = 800.0,
                    sort_by: str = "average_volume_90d_calc"):
    """Optionable-grade US names ordered by `sort_by` (default liquidity; pass
    'Volatility.M' for a high-IV lane), each carrying days-to-next-earnings. Returns
    a list of {ticker, earnings_days}. Fail-open to the staple list."""
    try:
        from tradingview_screener import Query, col
        q = (Query()
             .set_markets("america")
             .select("name", "close", "market_cap_basic", "average_volume_90d_calc",
                     "Volatility.M", "earnings_release_next_date", "sector")
             .where(
                 col("market_cap_basic") >= min_cap,
                 col("average_volume_90d_calc") >= (min_dollar_vol / max(price_lo, 1)),
                 col("close") >= price_lo,
                 col("close") <= price_hi,
             )
             .order_by(sort_by, ascending=False)
             .limit(int(limit) * 2))
        _count, df = q.get_scanner_data()
        out, seen = [], set()
        for _, row in df.iterrows():
            s = _clean(row.get("name"))
            if not s or s in seen:
                continue
            seen.add(s)
            sec = row.get("sector")
            sec = str(sec).strip() if sec else None
            out.append({"ticker": s,
                        "earnings_days": _earnings_days(row.get("earnings_release_next_date")),
                        "sector": sec or None})
            if len(out) >= limit:
                break
        if out:
            return out
    except Exception as exc:
        print(f"  universe: screener unavailable ({exc}); using fallback")
    return [{"ticker": t, "earnings_days": None, "sector": None} for t in FALLBACK[:limit]]


def seed_universe(symbols):
    """Screen for a SPECIFIC set of names (not a ranked slice). Used to guarantee the
    high-IV weeklies in HIGH_IV_SEEDS are in the scan even when the Volatility.M screen
    ranks them out of its top slice. Screening by name means each seed still carries its
    REAL earnings date + sector, so the earnings veto stays armed for it. Returns the same
    {ticker, earnings_days, sector} shape. Fail-open: still include the seeds (earnings
    unknown) rather than dropping them if the screener is unavailable."""
    syms = [s for s in (_clean(x) for x in (symbols or [])) if s]
    if not syms:
        return []
    want = set(syms)
    try:
        from tradingview_screener import Query, col
        q = (Query()
             .set_markets("america")
             .select("name", "earnings_release_next_date", "sector")
             .where(col("name").isin(syms))
             .limit(len(syms) * 2))
        _count, df = q.get_scanner_data()
        out, seen = [], set()
        for _, row in df.iterrows():
            s = _clean(row.get("name"))
            if not s or s in seen or s not in want:
                continue
            seen.add(s)
            sec = row.get("sector")
            sec = str(sec).strip() if sec else None
            out.append({"ticker": s,
                        "earnings_days": _earnings_days(row.get("earnings_release_next_date")),
                        "sector": sec or None})
        if out:
            return out
    except Exception as exc:
        print(f"  universe: seed screen unavailable ({exc}); seeds carry no earnings date")
    return [{"ticker": s, "earnings_days": None, "sector": None} for s in syms]


def _merge_lanes(liquid, high, seed):
    """Pure lane-merge (no network): the liquid slice owns the 'liquid' lane; the screener
    high-IV slice and the seed watchlist share the 'high_iv' lane. Dedupe the lane tag, and
    never lose a known earnings date or sector to an unknown one. Kept pure so the union
    invariants can be self-tested offline."""
    by_t = {}
    for d in liquid:
        by_t[d["ticker"]] = {"ticker": d["ticker"], "earnings_days": d["earnings_days"],
                             "sector": d.get("sector"), "lanes": ["liquid"]}
    for d in list(high) + list(seed):
        if d["ticker"] in by_t:
            e = by_t[d["ticker"]]
            if "high_iv" not in e["lanes"]:
                e["lanes"].append("high_iv")
            e["sector"] = e.get("sector") or d.get("sector")
            if e.get("earnings_days") is None and d.get("earnings_days") is not None:
                e["earnings_days"] = d["earnings_days"]
        else:
            by_t[d["ticker"]] = {"ticker": d["ticker"], "earnings_days": d["earnings_days"],
                                 "sector": d.get("sector"), "lanes": ["high_iv"]}
    return list(by_t.values())


def combined_universe(liquid_n: int = 13, highiv_n: int = 11, seeds=None):
    """Union of the most-LIQUID lane, the highest-VOLATILITY lane, and the HIGH_IV_SEEDS
    watchlist, deduped, each name tagged with which lane(s) it belongs to. The high-IV
    lane is where the rich premium lives; the liquid lane is the safe staples; the seeds
    guarantee the weeklies Michael watches never silently miss the cut. Returns a list of
    {ticker, earnings_days, lanes:[...]}. Fail-open."""
    liquid = screen_universe(limit=liquid_n)
    high = screen_universe(limit=highiv_n, sort_by="Volatility.M")
    seed = seed_universe(HIGH_IV_SEEDS if seeds is None else seeds)
    return _merge_lanes(liquid, high, seed)


def liquid_universe(limit: int = 30, **kw):
    """Just the tickers (back-compat wrapper over screen_universe)."""
    return [d["ticker"] for d in screen_universe(limit, **kw)]


def _selftest():
    """Offline invariants for the lane merge + seed union (no network)."""
    liquid = [{"ticker": "AAPL", "earnings_days": 12, "sector": "Technology"},
              {"ticker": "COIN", "earnings_days": 30, "sector": "Finance"}]
    high = [{"ticker": "COIN", "earnings_days": 30, "sector": "Finance"},
            {"ticker": "MARA", "earnings_days": 5, "sector": "Finance"}]
    seed = [{"ticker": "MSTR", "earnings_days": 8, "sector": "Technology Services"},
            {"ticker": "MARA", "earnings_days": 5, "sector": "Finance"},   # dup of high
            {"ticker": "AAPL", "earnings_days": None, "sector": None}]      # dup of liquid
    merged = {d["ticker"]: d for d in _merge_lanes(liquid, high, seed)}

    # every seed name made it in (the whole point: never silently missed)
    for t in ("MSTR", "MARA"):
        assert t in merged, f"seed {t} must survive the union"
    # a name in both liquid and high carries BOTH lane tags, once each
    assert merged["COIN"]["lanes"] == ["liquid", "high_iv"], merged["COIN"]["lanes"]
    # a seed that duplicates the high slice is not double-tagged
    assert merged["MARA"]["lanes"] == ["high_iv"], merged["MARA"]["lanes"]
    # a seed-only name lands in the high_iv lane
    assert merged["MSTR"]["lanes"] == ["high_iv"], merged["MSTR"]["lanes"]
    # a None earnings date from a seed never erases a known one from the liquid lane
    assert merged["AAPL"]["earnings_days"] == 12, "known earnings date must not be lost to a seed None"
    assert merged["AAPL"]["sector"] == "Technology", "known sector must not be lost to a seed None"

    # seed_universe fails open to the symbols themselves (network-free path)
    fo = seed_universe([])
    assert fo == [], "empty seed list -> empty"
    print("universe self-test passed")


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        _selftest()
    else:
        u = liquid_universe(30)
        print(f"{len(u)} names:", ", ".join(u))
