"""
wheelforge/build_site_data.py — turn real market data into the deployable site feed.

Each cycle ember runs this. It pulls real daily OHLCV for a watchlist (yfinance,
fail-open), derives the inputs WheelForge needs, scores the best premium-sell setup
per name, and writes docs/data/scan.json for the KLineChart frontend to render.

v1 honesty: premium is MODELED from realized vol (Black-Scholes on a ~1 sigma OTM,
~30 DTE put), not a live option quote. Real option chains + earnings dates land in
later cycles. The chart candles ARE real. No em dashes in user-facing strings.
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, timezone

from wheelforge.scoring import score_contract

WATCHLIST = ["AAPL", "MSFT", "NVDA", "AMD", "GOOGL", "AMZN", "META", "COST"]
DTE = 30
R = 0.045  # risk-free
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "docs", "data", "scan.json")


def _norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _bs_put(S, K, t, r, sigma):
    """Black-Scholes European put value."""
    if S <= 0 or K <= 0 or t <= 0 or sigma <= 0:
        return 0.0
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)
    return K * math.exp(-r * t) * _norm_cdf(-d2) - S * _norm_cdf(-d1)


def _realized_vol(closes):
    """Annualized close-to-close realized vol from a list of closes."""
    rets = []
    for i in range(1, len(closes)):
        if closes[i - 1] > 0:
            rets.append(math.log(closes[i] / closes[i - 1]))
    if len(rets) < 20:
        return 0.0
    mean = sum(rets) / len(rets)
    var = sum((x - mean) ** 2 for x in rets) / (len(rets) - 1)
    return math.sqrt(var) * math.sqrt(252.0)


def _iv_rank(closes, window=252):
    """Crude IV-rank proxy: where does the trailing 21d realized vol sit in its own
    1y range? Real ATM IV history replaces this once option data is wired."""
    if len(closes) < 60:
        return 50.0
    rv_series = []
    for i in range(21, len(closes)):
        rv_series.append(_realized_vol(closes[i - 21:i + 1]))
    rv_series = [v for v in rv_series if v > 0][-window:]
    if len(rv_series) < 20:
        return 50.0
    cur = rv_series[-1]
    lo, hi = min(rv_series), max(rv_series)
    return 50.0 if hi == lo else round(100.0 * (cur - lo) / (hi - lo), 1)


def _nearest_expiry(exps, target_dte):
    """Pick the listed expiry closest to target_dte days out (>= 7 DTE)."""
    from datetime import date
    best, best_d = None, 1e9
    today = date.today()
    for e in exps:
        try:
            d = (date.fromisoformat(e) - today).days
        except Exception:
            continue
        if d < 7:
            continue
        if abs(d - target_dte) < abs(best_d - target_dte):
            best, best_d = e, d
    return best, (int(best_d) if best else None)


def _live_put(ticker, spot, rv):
    """REAL ~30 DTE, ~1-sigma OTM cash-secured put off the live yfinance chain.
    Returns a dict with real iv/bid/ask/oi/volume/strike/dte, or None (fail-open)."""
    import yfinance as yf
    try:
        tk = yf.Ticker(ticker)
        exps = list(tk.options or [])
        if not exps:
            return None
        exp, dte = _nearest_expiry(exps, DTE)
        if not exp or not dte:
            return None
        puts = tk.option_chain(exp).puts
        if puts is None or puts.empty:
            return None
        target = spot * (1.0 - rv * math.sqrt(dte / 365.0))  # ~1 sigma OTM
        otm = puts[puts["strike"] <= spot].copy()
        if otm.empty:
            return None
        otm["_d"] = (otm["strike"] - target).abs()
        row = otm.sort_values("_d").iloc[0]
        bid = float(row.get("bid") or 0); ask = float(row.get("ask") or 0)
        mid = (bid + ask) / 2.0 if (bid > 0 and ask > 0) else float(row.get("lastPrice") or 0)
        iv = float(row.get("impliedVolatility") or 0)
        if mid <= 0 or iv <= 0:
            return None
        return {
            "strike": float(row["strike"]), "dte": int(dte), "premium": mid,
            "iv": iv, "bid": bid, "ask": ask,
            "open_interest": int(row.get("openInterest") or 0),
            "volume": int(row.get("volume") or 0),
        }
    except Exception:
        return None


def _fetch(ticker):
    """Real daily OHLCV via yfinance. Returns (candles, closes) or (None, None)."""
    import yfinance as yf
    df = yf.Ticker(ticker).history(period="8mo", interval="1d", auto_adjust=False)
    if df is None or df.empty:
        return None, None
    candles, closes = [], []
    for ts, row in df.iterrows():
        c = float(row["Close"])
        closes.append(c)
        candles.append({
            "timestamp": int(ts.timestamp() * 1000),
            "open": round(float(row["Open"]), 2), "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2), "close": round(c, 2),
            "volume": int(row["Volume"]),
        })
    return candles, closes


def build_one(ticker, earnings_days=None):
    candles, closes = _fetch(ticker)
    if not candles:
        return None
    spot = closes[-1]
    rv = _realized_vol(closes[-63:]) or 0.25

    live = _live_put(ticker, spot, rv)
    if live:                                   # REAL chain: real IV is the edge
        strike, dte, iv = live["strike"], live["dte"], live["iv"]
        premium, bid, ask = live["premium"], live["bid"], live["ask"]
        oi, vol, source = live["open_interest"], live["volume"], "live"
    else:                                      # fail-open: model it from realized vol
        iv, dte = rv * 1.15, DTE
        sp = iv * math.sqrt(dte / 365.0)
        strike = round(spot * (1.0 - sp), 0)
        premium = _bs_put(spot, strike, dte / 365.0, R, iv)
        spread = max(0.02, premium * 0.04)
        bid, ask = round(premium - spread / 2, 2), round(premium + spread / 2, 2)
        oi, vol, source = 1500, 250, "modeled"

    t = dte / 365.0
    prob_otm = (_norm_cdf((math.log(spot / strike) + (R - 0.5 * iv * iv) * t) / (iv * math.sqrt(t)))
                if (strike > 0 and iv > 0 and t > 0) else 0.0)
    roc = (premium / strike) * (365.0 / dte) if (strike > 0 and dte > 0) else 0.0

    contract = {
        "opt_type": "put", "iv": iv, "rv": rv, "iv_rank": _iv_rank(closes),
        "prob_otm": prob_otm, "bid": bid, "ask": ask, "open_interest": oi, "volume": vol,
        "annualized_roc": roc, "want_to_own": True, "dte": dte,
        "days_to_earnings": (earnings_days if earnings_days is not None else 999),
        "trend_align": 0.6,
    }
    scored = score_contract(contract)
    return {
        "ticker": ticker, "spot": round(spot, 2), "candles": candles,
        "pick": {
            "strike": round(strike, 2), "dte": dte, "premium": round(premium, 2),
            "annualized_roc": round(roc * 100, 1), "prob_otm": round(prob_otm * 100, 1),
            "iv": round(iv * 100, 1), "iv_rank": contract["iv_rank"], "source": source,
            "earnings_days": earnings_days,
            **scored,
        },
    }


def main():
    from wheelforge.universe import screen_universe
    rows = screen_universe(limit=20)  # the real market, most-liquid first, + earnings dates
    print(f"universe: {len(rows)} names from the screener")
    tickers = []
    for r in rows:
        tk = r["ticker"]
        try:
            one = build_one(tk, r.get("earnings_days"))
            if one:
                tickers.append(one)
                ed = one["pick"].get("earnings_days")
                flag = " EARN-AVOID" if one["pick"]["avoid"] else ""
                print(f"  {tk}: {one['pick']['score']} ({one['pick']['source']}) "
                      f"IV {one['pick']['iv']} earn={ed}{flag}")
        except Exception as exc:
            print(f"  {tk}: skipped ({exc})")
    tickers.sort(key=lambda x: x["pick"]["score"], reverse=True)
    live_n = sum(1 for t in tickers if t["pick"].get("source") == "live")
    note = (f"Candles and option premium are LIVE off the yfinance chain for {live_n} of "
            f"{len(tickers)} names (real IV, bid/ask, OI); the rest fall back to a "
            f"realized-vol model when the chain is missing.")
    out = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_note": note, "dte": DTE, "tickers": tickers,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nwrote {OUT} ({len(tickers)} names)")


if __name__ == "__main__":
    main()
