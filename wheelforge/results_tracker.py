"""
wheelforge/results_tracker.py — track whether MY OWN forward picks actually worked.

The backtest (wheelforge/backtest.py) is historical: it tests the safety MODEL on past
OHLCV. It does NOT tell you whether the picks this scanner printed on a given morning
held up. This module is the forward, honest version: every build snapshots the day's
actionable cash-secured-put picks (ticker, strike, exp, premium, score, predicted
prob_otm, lane) into a tiny local SQLite store. When an expiry passes, we settle it
against the price: did the stock hold ABOVE the strike (expired OTM, premium kept) or
breach it (would have been assigned). The track record then compares the FORWARD hit
rate to the prob_otm the model predicted, the premium actually captured, by lane.

Same shape + spirit as iv_history.py: the DB is LOCAL / gitignored (per-machine working
data), it starts empty and fills over weeks, and every call is fail-open. On the box the
30-minute cron feeds the snapshot and settles freshly-passed weeklies off the same spot
the build already pulls. A name that has left the universe simply stays pending until a
price for it is known again.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import date

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(HERE, "data", "results.db")

# The canonical wheel exit: once a short can be bought back for <= half what you sold it
# for, you have captured most of the edge and the remaining theta is the slow tail. Closing
# frees the full strike collateral to re-sell a fresh week. Same constant + meaning as
# roll_advisor.PROFIT_TAKE_PCT; the income machine's annual yield is premium-per-trade
# times trades-per-year, and this is the lever on the second term.
PROFIT_TAKE_PCT = 0.50


def _con(db_path=None):
    path = db_path or DB
    os.makedirs(os.path.dirname(path), exist_ok=True)
    con = sqlite3.connect(path, timeout=5)
    # One row per (record-day, ticker, exp, strike). A pick re-seen on a later day is a
    # NEW forward observation, so the day is part of the key; same pick same day updates.
    con.execute(
        "CREATE TABLE IF NOT EXISTS picks ("
        "day TEXT, ticker TEXT, strike REAL, exp TEXT, premium REAL, score REAL,"
        "prob_otm REAL, lane TEXT, direction TEXT,"
        "outcome TEXT, settle_price REAL, settled_day TEXT,"
        "PRIMARY KEY(day, ticker, exp, strike))"
    )
    return con


def _outcome(direction, strike, price):
    """Pure: did the sold strike stay safe at this settle price? For a cash-secured PUT
    the seller is safe when price holds AT or ABOVE the strike (expired OTM); below is a
    breach (assignment). For a covered CALL it is the mirror: safe when price stays AT or
    BELOW the strike. Returns 'otm' (kept the premium) or 'breach'."""
    try:
        strike = float(strike)
        price = float(price)
    except (TypeError, ValueError):
        return None
    if "call" in (direction or "").lower():
        return "otm" if price <= strike else "breach"
    return "otm" if price >= strike else "breach"


def _lane_of(pick):
    lanes = pick.get("lanes") or []
    if "liquid" in lanes:
        return "liquid"
    if lanes:
        return lanes[0]
    return "?"


def snapshot(picks, day=None, db_path=None):
    """Record today's ACTIONABLE cash-secured-put picks as forward observations.

    `picks` is the list build_site_data assembles (each item is {"ticker", "pick": {...}}).
    We only log real, sellable CSPs: a live/modeled put with a strike, an expiry, and a
    non-zero score (earnings-veto AVOIDs and covered-call rows are skipped — we are
    tracking the entries the scanner actually recommends). Returns the count stored.
    Fail-open: a malformed row is skipped, never raised."""
    day = day or date.today().isoformat()
    n = 0
    try:
        con = _con(db_path)
        for item in picks or []:
            try:
                p = item.get("pick") or {}
                tk = item.get("ticker")
                direction = p.get("direction") or ""
                if p.get("avoid") or "put" not in direction.lower():
                    continue
                strike, exp = p.get("strike"), p.get("exp")
                if not tk or not strike or not exp:
                    continue
                if not p.get("score"):
                    continue
                con.execute(
                    "INSERT INTO picks (day,ticker,strike,exp,premium,score,prob_otm,lane,"
                    "direction,outcome,settle_price,settled_day) "
                    "VALUES (?,?,?,?,?,?,?,?,?,NULL,NULL,NULL) "
                    "ON CONFLICT(day,ticker,exp,strike) DO UPDATE SET "
                    "premium=excluded.premium, score=excluded.score, "
                    "prob_otm=excluded.prob_otm, lane=excluded.lane, "
                    "direction=excluded.direction",
                    (day, str(tk).upper(), round(float(strike), 2), str(exp),
                     float(p.get("premium") or 0.0), float(p.get("score") or 0.0),
                     float(p.get("prob_otm") or 0.0), _lane_of(p), direction),
                )
                n += 1
            except Exception:
                continue
        con.commit()
        con.close()
    except Exception:
        pass
    return n


def settle(prices, today=None, db_path=None):
    """Settle every PENDING pick whose expiry is on/before `today` and for which we have
    a price. `prices` maps TICKER -> price (a dict, or any object with .get). Returns the
    number newly settled. Fail-open."""
    today = today or date.today().isoformat()
    settled = 0
    try:
        get = prices.get if hasattr(prices, "get") else (lambda k: None)
        con = _con(db_path)
        rows = con.execute(
            "SELECT rowid, ticker, strike, exp, direction FROM picks "
            "WHERE outcome IS NULL AND exp<=?", (today,)
        ).fetchall()
        for rowid, tk, strike, exp, direction in rows:
            price = get(str(tk).upper())
            if not price:
                continue
            out = _outcome(direction, strike, price)
            if out is None:
                continue
            con.execute(
                "UPDATE picks SET outcome=?, settle_price=?, settled_day=? WHERE rowid=?",
                (out, float(price), today, rowid),
            )
            settled += 1
        con.commit()
        con.close()
    except Exception:
        pass
    return settled


def open_positions(db_path=None):
    """Every still-PENDING pick (no outcome yet), deduped to one row per option, as the
    open short positions the tracker is watching. A pick re-seen on later days is logged
    once per day (each a fresh forward observation for the hit-rate scorecard), but for a
    profit-take we want ONE position per (ticker, exp, strike) anchored on its EARLIEST
    snapshot, since that is closest to when the entry was actually sold. Returns a list of
    dicts carrying that entry premium. Fail-open: [] on any error."""
    seen = {}
    try:
        con = _con(db_path)
        # earliest day first, so the first time we see an option wins (its entry premium)
        rows = con.execute(
            "SELECT day,ticker,strike,exp,premium,score,lane,direction "
            "FROM picks WHERE outcome IS NULL ORDER BY day ASC"
        ).fetchall()
        con.close()
        for day, tk, strike, exp, prem, score, lane, direction in rows:
            try:
                key = (str(tk).upper(), str(exp), round(float(strike), 2))
            except (TypeError, ValueError):
                continue
            if key in seen:
                continue
            seen[key] = {
                "first_day": day, "ticker": str(tk).upper(), "strike": float(strike),
                "exp": str(exp), "entry_premium": float(prem or 0.0),
                "score": score, "lane": lane or "?", "direction": direction or "",
            }
    except Exception:
        pass
    return list(seen.values())


def _captured_pct(entry, current):
    """Pure: fraction of the max premium captured if you buy the short back NOW. You sold
    for `entry` and can repurchase at `current`, so you keep `entry - current`, i.e. you
    have banked `(entry - current) / entry` of the max profit. Returns a 0..1 float, or
    None when `entry` is non-positive or either input is junk (fail-open)."""
    try:
        entry = float(entry)
        current = float(current)
    except (TypeError, ValueError):
        return None
    if entry <= 0:
        return None
    return (entry - current) / entry


def profit_take_alerts(quote, db_path=None, threshold=PROFIT_TAKE_PCT, today=None):
    """The morning close-the-winners brief. For every OPEN tracked short, look up its
    current mid via `quote` and flag the ones now buyable for <= `threshold` of the entry
    premium (i.e. >= 1-threshold of max profit captured). On a short weekly that typically
    lands by day 3-4; closing frees the collateral to re-sell a fresh week instead of
    grinding the slow tail to expiry.

    `quote` is either a callable `quote(ticker, exp, strike) -> current_mid_or_None` (the
    CLI passes a yfinance-backed one) or a dict keyed `(ticker, exp, round(strike, 2))`.
    Only still-LIVE options are judged (a passed expiry is settle()'s job, not a take).
    Returns the alerts sorted most-captured first; fail-open, a name we cannot price is
    simply skipped, never raised."""
    today = today or date.today().isoformat()
    getq = quote if callable(quote) else (
        lambda t, e, k: quote.get((t, e, round(float(k), 2))))
    alerts = []
    for pos in open_positions(db_path):
        try:
            if pos["exp"] <= today:        # already expired -> settle(), not profit-take
                continue
            cur = getq(pos["ticker"], pos["exp"], pos["strike"])
            if cur is None:
                continue
            cur = float(cur)
            cap = _captured_pct(pos["entry_premium"], cur)
            if cap is None or cur > pos["entry_premium"] * threshold:
                continue
            alerts.append({**pos, "current_mid": round(cur, 2),
                           "captured_pct": round(cap * 100.0, 1)})
        except Exception:
            continue
    alerts.sort(key=lambda a: a["captured_pct"], reverse=True)
    return alerts


def _bucket(rows):
    """rows: iterable of (prob_otm, premium, outcome). Aggregate a settled cohort into the
    forward scorecard: n, hit rate (fraction that expired OTM), the AVG prob_otm the model
    predicted (so you can read forward-actual vs predicted side by side), and the average
    premium captured. Returns None for an empty cohort."""
    n = len(rows)
    if not n:
        return None
    kept = sum(1 for _, _, o in rows if o == "otm")
    pred = [pr for pr, _, _ in rows if pr]
    return {
        "n": n,
        "hit_rate": round(kept / n * 100.0, 1),
        "predicted_otm": round(sum(pred) / len(pred), 1) if pred else None,
        "avg_premium": round(sum(pm for _, pm, _ in rows) / n, 2),
    }


def track_record(db_path=None):
    """The forward scorecard: overall + per-lane forward hit rate vs the predicted
    prob_otm, plus avg premium captured and how many picks are still pending. Returns a
    dict (always, even when empty) so a caller / frontend can render it from day one."""
    out = {"overall": None, "by_lane": {}, "pending": 0, "settled": 0}
    try:
        con = _con(db_path)
        rows = con.execute(
            "SELECT prob_otm, premium, outcome, lane FROM picks WHERE outcome IS NOT NULL"
        ).fetchall()
        out["pending"] = con.execute(
            "SELECT COUNT(*) FROM picks WHERE outcome IS NULL"
        ).fetchone()[0]
        con.close()
        out["settled"] = len(rows)
        out["overall"] = _bucket([(r[0], r[1], r[2]) for r in rows])
        lanes = {}
        for pr, pm, oc, lane in rows:
            lanes.setdefault(lane or "?", []).append((pr, pm, oc))
        out["by_lane"] = {k: _bucket(v) for k, v in sorted(lanes.items())}
    except Exception:
        pass
    return out


def _selftest():
    """Pure, offline self-test on a throwaway DB (never touches the real store)."""
    import tempfile

    tmp = os.path.join(tempfile.mkdtemp(), "rt_test.db")

    # outcome math, both legs
    assert _outcome("cash-secured put", 100, 105) == "otm"     # held above -> kept
    assert _outcome("cash-secured put", 100, 95) == "breach"   # broke below -> assigned
    assert _outcome("cash-secured put", 100, 100) == "otm"     # at-the-money = OTM (safe)
    assert _outcome("covered call", 100, 95) == "otm"          # call mirror: stayed below
    assert _outcome("covered call", 100, 105) == "breach"      # called away
    assert _outcome("cash-secured put", 100, None) is None     # no price = no verdict

    picks = [
        {"ticker": "AAA", "pick": {"strike": 100, "exp": "2026-01-10", "premium": 1.5,
                                   "score": 72, "prob_otm": 88.0,
                                   "direction": "cash-secured put", "lanes": ["liquid"]}},
        {"ticker": "BBB", "pick": {"strike": 50, "exp": "2026-01-10", "premium": 0.9,
                                   "score": 61, "prob_otm": 80.0,
                                   "direction": "cash-secured put", "lanes": ["hi-iv"]}},
        # skipped: an earnings-veto AVOID is not an entry the scanner recommends
        {"ticker": "CCC", "pick": {"strike": 30, "exp": "2026-01-10", "premium": 0.5,
                                   "score": 0.0, "avoid": True,
                                   "direction": "avoid", "lanes": ["liquid"]}},
    ]
    assert snapshot(picks, day="2026-01-01", db_path=tmp) == 2, "only the 2 real CSPs log"

    # re-seeing the SAME picks a LATER day is a fresh forward observation, not a dup
    assert snapshot(picks, day="2026-01-02", db_path=tmp) == 2
    tr = track_record(db_path=tmp)
    assert tr["pending"] == 4 and tr["settled"] == 0, tr

    # nothing settles before expiry
    assert settle({"AAA": 110, "BBB": 40}, today="2026-01-05", db_path=tmp) == 0

    # at/after expiry: AAA held (otm), BBB breached. Two record-days -> 4 settlements.
    assert settle({"AAA": 110, "BBB": 40}, today="2026-01-11", db_path=tmp) == 4
    tr = track_record(db_path=tmp)
    assert tr["settled"] == 4 and tr["pending"] == 0, tr
    assert tr["overall"]["n"] == 4 and tr["overall"]["hit_rate"] == 50.0, tr["overall"]
    assert tr["overall"]["predicted_otm"] == 84.0, tr["overall"]  # (88+80+88+80)/4
    assert tr["by_lane"]["liquid"]["hit_rate"] == 100.0, tr["by_lane"]  # AAA held both days
    assert tr["by_lane"]["hi-iv"]["hit_rate"] == 0.0, tr["by_lane"]     # BBB broke both days
    assert tr["by_lane"]["liquid"]["avg_premium"] == 1.5, tr["by_lane"]

    # a missing price leaves the pick pending, never crashes
    snapshot([{"ticker": "DDD", "pick": {"strike": 10, "exp": "2026-01-01", "premium": 0.2,
                                         "score": 55, "prob_otm": 90.0,
                                         "direction": "cash-secured put",
                                         "lanes": ["liquid"]}}], day="2025-12-20", db_path=tmp)
    assert settle({}, today="2026-02-01", db_path=tmp) == 0  # no price -> still pending
    assert track_record(db_path=tmp)["pending"] == 1

    # --- profit-take brief (close the winners, recycle the collateral) ---
    assert _captured_pct(2.00, 1.00) == 0.50      # bought back at half = 50% captured
    assert _captured_pct(2.00, 0.50) == 0.75      # quarter = 75% captured
    assert _captured_pct(0.0, 0.0) is None        # no entry premium -> no read (fail-open)
    assert _captured_pct(2.00, None) is None      # junk current -> None

    pt = os.path.join(tempfile.mkdtemp(), "pt_test.db")
    opens = [
        {"ticker": "EEE", "pick": {"strike": 100, "exp": "2026-03-20", "premium": 2.00,
                                   "score": 70, "prob_otm": 85.0,
                                   "direction": "cash-secured put", "lanes": ["liquid"]}},
        {"ticker": "FFF", "pick": {"strike": 40, "exp": "2026-03-20", "premium": 1.00,
                                   "score": 64, "prob_otm": 82.0,
                                   "direction": "cash-secured put", "lanes": ["hi-iv"]}},
    ]
    # logged twice, two days; the entry must anchor on the EARLIER day's premium ($2.10),
    # not the later $2.00, and open_positions must dedupe to ONE row per option.
    opens[0]["pick"]["premium"] = 2.10
    snapshot(opens, day="2026-03-01", db_path=pt)
    opens[0]["pick"]["premium"] = 2.00
    snapshot(opens, day="2026-03-02", db_path=pt)
    pos = {p["ticker"]: p for p in open_positions(db_path=pt)}
    assert len(pos) == 2, "deduped to one row per option"
    assert pos["EEE"]["entry_premium"] == 2.10, "anchors on the earliest snapshot's premium"
    assert pos["EEE"]["first_day"] == "2026-03-01", pos["EEE"]

    # EEE now buyable at $0.90 (<= 50% of $2.10 -> CLOSE); FFF at $0.80 (still 80% -> hold)
    quotes = {("EEE", "2026-03-20", 100.0): 0.90, ("FFF", "2026-03-20", 40.0): 0.80}
    al = profit_take_alerts(quotes, db_path=pt, today="2026-03-04")
    assert [a["ticker"] for a in al] == ["EEE"], al
    assert al[0]["captured_pct"] == 57.1, al[0]          # (2.10-0.90)/2.10
    assert al[0]["current_mid"] == 0.90, al[0]

    # a callable quote works too, and an already-EXPIRED option is settle()'s job, not a take
    al2 = profit_take_alerts(lambda t, e, k: 0.10, db_path=pt, today="2026-03-21")
    assert al2 == [], "everything has expired past 2026-03-20 -> no profit-take"
    # a name we cannot price is skipped, never raised
    assert profit_take_alerts({}, db_path=pt, today="2026-03-04") == []

    print("results_tracker self-test OK")


if __name__ == "__main__":
    _selftest()
