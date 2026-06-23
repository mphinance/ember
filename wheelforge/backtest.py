"""
wheelforge/backtest.py — does the "stays OTM" claim actually hold up?

Honest scope: I do not have a historical OPTION feed (past IV / premiums), so I can
NOT backtest the full edge score (rich vs cheap). What I CAN test with plain OHLCV is
the SAFETY axis, the disciplined seller's real question: when I sell a put about one
sigma out of the money and ~30 days to expiry, how often does it actually expire OTM,
and is that close to what the model PREDICTS?

Method (walk-forward, no lookahead): at each past day, size a put strike at
`spot * (1 - mult * sigma_horizon)` using ONLY trailing realized vol, then look ahead
`horizon` trading days and check whether price finished above the strike (expired OTM =
the put seller wins). Compare the empirical OTM rate to the lognormal prediction. A
well-calibrated safety model has empirical ~= predicted.

  python -m wheelforge.backtest NVDA AAPL TSLA

Pure core + self-test; the runner fetches OHLCV via yfinance.
"""

from __future__ import annotations

import math
import sys


def _norm_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _ann_rv(closes):
    rets = []
    for i in range(1, len(closes)):
        if closes[i - 1] > 0:
            rets.append(math.log(closes[i] / closes[i - 1]))
    if len(rets) < 10:
        return 0.0
    m = sum(rets) / len(rets)
    var = sum((x - m) ** 2 for x in rets) / (len(rets) - 1)
    return math.sqrt(var) * math.sqrt(252.0)


def backtest_otm(closes, horizon=21, mult=1.0, lookback=63):
    """Walk-forward OTM-expiry test on a list of closes. Returns
    {samples, otm_rate, predicted, gap} (rates in 0..1) or None if too short."""
    n = wins = 0
    pred_sum = 0.0
    last = len(closes) - horizon
    for i in range(lookback, last):
        rv = _ann_rv(closes[i - lookback:i + 1])
        if rv <= 0:
            continue
        spot = closes[i]
        sig_h = rv * math.sqrt(horizon / 252.0)
        if sig_h <= 0:
            continue
        strike = spot * (1.0 - mult * sig_h)
        if strike <= 0:
            continue
        wins += 1 if closes[i + horizon] >= strike else 0     # expired OTM
        d2 = (math.log(spot / strike) - 0.5 * sig_h * sig_h) / sig_h
        pred_sum += _norm_cdf(d2)
        n += 1
    if n < 30:
        return None
    otm = wins / n
    pred = pred_sum / n
    return {"samples": n, "otm_rate": round(otm, 4), "predicted": round(pred, 4),
            "gap": round(otm - pred, 4)}


def _selftest():
    # A steadily RISING series: a ~1 sigma OTM put almost always expires OTM.
    rising = [100.0 * (1.0 + 0.004) ** i for i in range(200)]
    r = backtest_otm(rising, horizon=21, lookback=40)
    print("rising:", r)
    assert r and r["otm_rate"] >= 0.95, "puts under a rising market should expire OTM"

    # A steadily FALLING series: the put gets breached far more often.
    falling = [100.0 * (1.0 - 0.004) ** i for i in range(200)]
    f = backtest_otm(falling, horizon=21, lookback=40)
    print("falling:", f)
    assert f and f["otm_rate"] <= r["otm_rate"], "a falling market breaches puts more"
    print("\nOK: backtest self-test passed.")


def run(tickers):
    import yfinance as yf
    print("\n  TICKER   SAMPLES  OTM-RATE  PREDICTED   GAP")
    print("  " + "-" * 46)
    agg_o = agg_p = k = 0
    for tk in tickers:
        try:
            df = yf.Ticker(tk).history(period="2y", interval="1d", auto_adjust=False)
            closes = [float(c) for c in df["Close"].tolist()]
            r = backtest_otm(closes)
            if not r:
                print(f"  {tk:<7}  (not enough history)"); continue
            print(f"  {tk:<7}  {r['samples']:>6}   {r['otm_rate']*100:>6.1f}%   "
                  f"{r['predicted']*100:>6.1f}%   {r['gap']*100:>+5.1f}pt")
            agg_o += r["otm_rate"]; agg_p += r["predicted"]; k += 1
        except Exception as exc:
            print(f"  {tk:<7}  skipped ({exc})")
    if k:
        print("  " + "-" * 46)
        print(f"  {'AVG':<7}  {'':>6}   {agg_o/k*100:>6.1f}%   {agg_p/k*100:>6.1f}%   "
              f"{(agg_o-agg_p)/k*100:>+5.1f}pt")
        print("\nTests the SAFETY/distance claim only (no historical option feed for the "
              "full edge). Positive gap = the put stays OTM MORE than the model predicts.")


if __name__ == "__main__":
    args = [a.upper() for a in sys.argv[1:] if a.isalpha()]
    if args:
        run(args)
    else:
        _selftest()
