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


def build_one(ticker):
    candles, closes = _fetch(ticker)
    if not candles:
        return None
    spot = closes[-1]
    rv = _realized_vol(closes[-63:]) or 0.25
    iv = rv * 1.15  # modeled VRP placeholder until live chains
    t = DTE / 365.0
    sigma_period = iv * math.sqrt(t)
    strike = round(spot * (1.0 - sigma_period), 0)  # ~1 sigma OTM put
    premium = _bs_put(spot, strike, t, R, iv)
    prob_otm = _norm_cdf((math.log(spot / strike) + (R - 0.5 * iv * iv) * t) / (iv * math.sqrt(t)))
    roc = (premium / strike) * (365.0 / DTE) if strike > 0 else 0.0
    spread = max(0.02, premium * 0.04)

    contract = {
        "opt_type": "put", "iv": iv, "rv": rv, "iv_rank": _iv_rank(closes),
        "prob_otm": prob_otm, "bid": round(premium - spread / 2, 2),
        "ask": round(premium + spread / 2, 2), "open_interest": 1500, "volume": 250,
        "annualized_roc": roc, "want_to_own": True, "dte": DTE,
        "days_to_earnings": 999, "trend_align": 0.6,
    }
    scored = score_contract(contract)
    return {
        "ticker": ticker, "spot": round(spot, 2), "candles": candles,
        "pick": {
            "strike": strike, "dte": DTE, "premium": round(premium, 2),
            "annualized_roc": round(roc * 100, 1), "prob_otm": round(prob_otm * 100, 1),
            "iv": round(iv * 100, 1), "iv_rank": contract["iv_rank"],
            **scored,
        },
    }


def main():
    tickers = []
    for tk in WATCHLIST:
        try:
            one = build_one(tk)
            if one:
                tickers.append(one)
                print(f"  {tk}: score {one['pick']['score']} {one['pick']['direction']}")
        except Exception as exc:
            print(f"  {tk}: skipped ({exc})")
    tickers.sort(key=lambda x: x["pick"]["score"], reverse=True)
    out = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_note": "Candles are real (yfinance). Premium is modeled from realized "
                       "vol (BS, ~1 sigma OTM 30 DTE put); live option chains come next.",
        "dte": DTE, "tickers": tickers,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nwrote {OUT} ({len(tickers)} names)")


if __name__ == "__main__":
    main()
