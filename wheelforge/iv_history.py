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
