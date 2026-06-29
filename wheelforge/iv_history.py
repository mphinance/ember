"""
wheelforge/iv_history.py — remember each name's IV so "IV rank" can be REAL.

There is no free historical implied-vol feed, so the honest way to know whether a
name's IV is high vs its own past is to start writing it down. Every build records the
current solved IV per ticker into a tiny local SQLite store (daily-collapsed), and the
rank is just where today's IV sits in that name's accumulated range. It starts empty
and gets truer every day, especially on the box where the 30-minute cron feeds it.

The DB is LOCAL / gitignored (it is per-machine working data, like the commits DB).
While history is thin, callers fall back to a realized-vol proxy. Fail-open everywhere.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import date, timedelta

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(HERE, "data", "iv_history.db")
_MIN_SAMPLES = 20


def _con():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    con = sqlite3.connect(DB, timeout=5)
    con.execute("CREATE TABLE IF NOT EXISTS iv_hist "
                "(ticker TEXT, day TEXT, iv REAL, PRIMARY KEY(ticker, day))")
    return con


def record(ticker, iv):
    """Store today's IV for a ticker (one row per day, latest wins). Fail-open."""
    try:
        if not ticker or not iv or float(iv) <= 0:
            return
        con = _con()
        con.execute("INSERT INTO iv_hist (ticker, day, iv) VALUES (?,?,?) "
                    "ON CONFLICT(ticker, day) DO UPDATE SET iv=excluded.iv",
                    (str(ticker).upper(), date.today().isoformat(), float(iv)))
        con.commit()
        con.close()
    except Exception:
        pass


def iv_rank(ticker, current_iv, window_days=365):
    """Percentile (0..100) of current_iv within this ticker's stored IV over the
    window. Returns None until there are >= _MIN_SAMPLES days (caller falls back)."""
    try:
        if not ticker or not current_iv:
            return None
        cutoff = (date.today() - timedelta(days=window_days)).isoformat()
        con = _con()
        rows = con.execute("SELECT iv FROM iv_hist WHERE ticker=? AND day>=?",
                           (str(ticker).upper(), cutoff)).fetchall()
        con.close()
        ivs = [r[0] for r in rows if r[0] and r[0] > 0]
        if len(ivs) < _MIN_SAMPLES:
            return None
        lo, hi = min(ivs), max(ivs)
        if hi == lo:
            return 50.0
        return round((float(current_iv) - lo) / (hi - lo) * 100.0, 1)
    except Exception:
        return None


def sample_count(ticker, window_days=365):
    try:
        cutoff = (date.today() - timedelta(days=window_days)).isoformat()
        con = _con()
        n = con.execute("SELECT COUNT(*) FROM iv_hist WHERE ticker=? AND day>=?",
                        (str(ticker).upper(), cutoff)).fetchone()[0]
        con.close()
        return n
    except Exception:
        return 0


def _selftest():
    """Offline invariants for the IV-rank percentile. Points the store at a throwaway temp
    DB (never the real gitignored data/iv_history.db) and seeds known IVs by hand so the
    percentile math is checked, not the network. The whole honesty of the iv-rank surface
    rests on this: thin history must read None (caller falls back to the rv proxy), and a
    thick history must place today's IV correctly inside its own range."""
    import tempfile
    global DB
    real_db = DB
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    DB = tmp.name
    try:
        # Thin history: fewer than _MIN_SAMPLES days -> None, so the caller falls back to the
        # realized-vol proxy rather than ranking against a handful of points.
        con = _con()
        base = date(2026, 1, 1)
        for i in range(_MIN_SAMPLES - 1):
            con.execute("INSERT INTO iv_hist (ticker, day, iv) VALUES (?,?,?)",
                        ("THIN", (base + timedelta(days=i)).isoformat(), 0.40))
        con.commit()
        con.close()
        assert iv_rank("THIN", 0.40) is None, "below _MIN_SAMPLES days must read None (fall back)"
        assert sample_count("THIN") == _MIN_SAMPLES - 1, "sample_count tracks the stored days"

        # Thick history spanning IV 0.20 .. 0.58 (20 evenly-spaced days). Today at the LOW
        # is rank 0, at the HIGH is 100, dead-centre is ~50, and a value beyond the range
        # clamps to the edges by construction (it falls outside [lo, hi]).
        con = _con()
        ivs = [0.20 + 0.02 * i for i in range(_MIN_SAMPLES)]  # 0.20 .. 0.58
        for i, iv in enumerate(ivs):
            con.execute("INSERT INTO iv_hist (ticker, day, iv) VALUES (?,?,?)",
                        ("RICH", (base + timedelta(days=i)).isoformat(), iv))
        con.commit()
        con.close()
        lo, hi = min(ivs), max(ivs)
        assert iv_rank("RICH", lo) == 0.0, "today's IV at the 1y low ranks 0"
        assert iv_rank("RICH", hi) == 100.0, "today's IV at the 1y high ranks 100"
        mid = (lo + hi) / 2.0
        assert iv_rank("RICH", mid) == 50.0, "today's IV dead-centre ranks ~50"
        print(f"iv-rank: {len(ivs)} days {lo:.2f}..{hi:.2f} -> {mid:.2f} ranks "
              f"{iv_rank('RICH', mid)}")

        # A flat history (every day the same IV) has no range, so any current IV ranks 50
        # rather than dividing by zero.
        con = _con()
        for i in range(_MIN_SAMPLES):
            con.execute("INSERT INTO iv_hist (ticker, day, iv) VALUES (?,?,?)",
                        ("FLAT", (base + timedelta(days=i)).isoformat(), 0.33))
        con.commit()
        con.close()
        assert iv_rank("FLAT", 0.33) == 50.0, "a flat history (hi==lo) ranks 50, never divides by zero"

        # Fail-open: junk ticker / missing current IV never raise, they read None.
        assert iv_rank("", 0.40) is None and iv_rank("RICH", None) is None, \
            "empty ticker or missing current IV fails open to None"
        print("OK: iv_history iv-rank self-test passed.")
    finally:
        DB = real_db
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


if __name__ == "__main__":
    _selftest()
