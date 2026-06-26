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
from wheelforge.freeshares import free_shares_read
from wheelforge.iv_history import record as _iv_record, iv_rank as _iv_rank_hist
from wheelforge.structure import (keltner_position, keltner_bands,
                                  support_floor_score, structure_with_floor)
from wheelforge.levels import support_resistance
from wheelforge.vol_models import composite_realized_vol

WATCHLIST = ["AAPL", "MSFT", "NVDA", "AMD", "GOOGL", "AMZN", "META", "COST"]
DTE = 7    # target the nearest WEEKLY — how Michael actually sells (e.g. NVDA 190 put,
           # 4 DTE, ~5% OTM). 1-sigma at ~weekly tenor lands ~5% OTM and annualizes ~2x a
           # monthly, into the ~100%/yr range he runs. Earnings veto still guards the week.
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


def _iv_from_put(premium, S, K, t, r):
    """Back implied vol out of a REAL put premium by bisection. yfinance's quoted
    impliedVolatility is garbage on some strikes (stale quotes), and a wrong IV
    poisons both prob_otm and the VRP/richness score. The premium is real, so solve
    for the vol that reproduces it. Returns None if it can't."""
    if not (premium and premium > 0 and S > 0 and K > 0 and t > 0):
        return None
    lo, hi = 0.01, 5.0
    if _bs_put(S, K, t, r, hi) < premium:   # premium richer than even 500% vol -> bail
        return None
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if _bs_put(S, K, t, r, mid) > premium:
            hi = mid
        else:
            lo = mid
    iv = (lo + hi) / 2.0
    return iv if 0.01 < iv < 5.0 else None


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


def _nearest_expiry(exps, target_dte, lo=3, hi=21):
    """Pick the listed expiry nearest target_dte, CONSTRAINED to the weekly CSP window
    [lo, hi] days (default 3-21). Michael sells short-dated weeklies (~4 DTE), so the
    sweet spot is the nearest weekly, not a monthly. We only fall outside the window if
    nothing at all lands inside it. Floor at 2 DTE so true weeklies qualify but we never
    pick same/next-day gamma roulette by accident."""
    from datetime import date
    today = date.today()
    in_win, in_best = None, 1e9
    any_pick, any_best = None, 1e9
    for e in exps:
        try:
            d = (date.fromisoformat(e) - today).days
        except Exception:
            continue
        if d < 2:
            continue
        if abs(d - target_dte) < any_best:
            any_pick, any_best = (e, d), abs(d - target_dte)
        if lo <= d <= hi and abs(d - target_dte) < in_best:
            in_win, in_best = (e, d), abs(d - target_dte)
    pick = in_win or any_pick
    return (pick[0], int(pick[1])) if pick else (None, None)


def _anchor_strike(spot, rv, dte, support):
    """Where to sell the put. Michael's method: sell AT support and trust it (he does not
    trade off delta). So if there is a real support level in a sane band below spot, that
    IS the strike. Only when there is no clean support do we fall back to ~1 sigma OTM.
    Returns (target_price, at_support)."""
    sigma = spot * (1.0 - rv * math.sqrt(dte / 365.0))   # ~1 sigma OTM, the fallback
    if support and spot * 0.80 <= support < spot:
        return support, True
    return sigma, False


def _live_put(ticker, spot, rv, support=None):
    """REAL nearest-weekly (~7 DTE) cash-secured put off the live yfinance chain, struck AT
    support when there is one (else ~1 sigma OTM). Returns a dict with real
    iv/bid/ask/oi/volume/strike/dte + at_support, or None (fail-open)."""
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
        target, at_support = _anchor_strike(spot, rv, dte, support)
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
            "strike": float(row["strike"]), "dte": int(dte), "exp": exp, "premium": mid,
            "iv": iv, "bid": bid, "ask": ask, "at_support": at_support,
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


def _levels(candles, spot, support=None, resistance=None):
    """Chart levels: Keltner volatility walls + major price-action S/R + spot. S/R can be
    passed in (computed once upstream) to avoid recomputing the pivots."""
    if support is None and resistance is None:
        support, resistance = support_resistance(candles, spot)
    return {
        "keltner": keltner_bands(candles),
        "support": support, "resistance": resistance,
        "spot": round(spot, 2),
    }


def build_one(ticker, earnings_days=None, lanes=None):
    candles, closes = _fetch(ticker)
    if not candles:
        return None
    # Would a disciplined seller WANT assignment here? Default from the lane: the
    # liquid lane is ownable staples (True); a name ONLY in the high-IV lane is
    # speculative, so assignment is not automatically welcome (False). An explicit
    # CLI scan (no lanes) is a name you chose, so default True. Kills the dead
    # hardcoded-True that made the free-shares quality penalty never fire.
    want_to_own = True if lanes is None else ("liquid" in (lanes or []))
    spot = closes[-1]
    # Composite realized vol (VoPR: CC + Parkinson + Garman-Klass + Rogers-Satchell)
    # gives an honest VRP denominator vs the old close-to-close-only RV.
    rv = composite_realized_vol(candles, period=20) or _realized_vol(closes[-63:]) or 0.25
    # Short-horizon RV for the VRP denominator. The 20-day rv is a LAGGED lie to a weekly
    # vol seller: when this week's vol spikes (exactly when you want to sell), 20-day RV is
    # still cool from last month and the VRP looks fat that isn't. A 7-DTE IV must be judged
    # against a ~week of realized vol, so compare it to the 5-day. The 20-day stays as the
    # HV-rank / trend context. Only the LIVE (weekly) path swaps the denominator; the modeled
    # monthly keeps the 20-day match.
    short_rv = composite_realized_vol(candles, period=5) or rv

    from datetime import date, timedelta
    # Major price-action support: the level he sells AT (computed once, reused for the chart).
    support, resistance = support_resistance(candles, spot)
    live = _live_put(ticker, spot, rv, support=support)
    vrp_rv = rv                                # VRP denominator; live weekly swaps to 5-day below
    if live:                                   # REAL chain: real IV is the edge
        strike, dte, exp = live["strike"], live["dte"], live["exp"]
        premium, bid, ask = live["premium"], live["bid"], live["ask"]
        oi, vol, source = live["open_interest"], live["volume"], "live"
        at_support = live["at_support"]
        # Trust the premium, not the quoted IV: solve IV from the real mid. Fall back
        # to a sane quoted IV, then to realized vol.
        qiv = live["iv"]
        iv = (_iv_from_put(premium, spot, strike, dte / 365.0, R)
              or (qiv if (qiv and 0.33 * rv <= qiv <= 4 * rv) else rv))
        vrp_rv = short_rv                      # a 7-DTE IV vs ~a week of realized vol
    else:                                      # fail-open: model it from realized vol
        iv, dte = rv * 1.15, DTE
        target, at_support = _anchor_strike(spot, iv, dte, support)
        strike = round(target, 0)
        premium = _bs_put(spot, strike, dte / 365.0, R, iv)
        spread = max(0.02, premium * 0.04)
        bid, ask = round(premium - spread / 2, 2), round(premium + spread / 2, 2)
        oi, vol, source = 1500, 250, "modeled"
        exp = (date.today() + timedelta(days=dte)).isoformat()
    # His edge gate: rich premium = IV over HV (the VRP). A flag he reads at a glance.
    # Judged against vrp_rv (5-day for a live weekly, 20-day for the modeled monthly).
    iv_gt_hv = bool(iv > vrp_rv)
    vrp = round(iv / vrp_rv, 2) if vrp_rv > 0 else None

    t = dte / 365.0
    # Drift = 0.0, NOT the risk-free R. This is the cleanest physical-measure analog
    # (the lognormal MEDIAN, no risk premium baked in): a "stays-OTM" estimate that is
    # really a risk-neutral delta-equivalent. Using R=0.045 here would tilt the median
    # UP, overstating safety on a downtrending name and understating it on a ripping one.
    # (R still belongs in _iv_from_put, which is genuine risk-neutral option pricing.)
    prob_otm = (_norm_cdf((math.log(spot / strike) + (0.0 - 0.5 * iv * iv) * t) / (iv * math.sqrt(t)))
                if (strike > 0 and iv > 0 and t > 0) else 0.0)
    # Return on the capital actually tied up: a cash-secured put pockets the premium
    # up front, so the net basis at risk is (strike - premium), not the full strike.
    # That is the honest denominator a wheel seller uses to judge yield.
    cap = strike - premium
    roc = (premium / cap) * (365.0 / dte) if (cap > 0 and dte > 0) else 0.0

    # REAL structure: the broad trend (VoPR Keltner position, low = falling = do not sell
    # into it) BLENDED with the per-strike support floor. Selling AT/just-above a major
    # support level (Michael's method) is the A+ structural CSP, so a real floor under the
    # strike lifts the factor; selling through the floor into the void drags it.
    keltner = keltner_position(candles)
    floor = support_floor_score(strike, support, spot)
    struct = structure_with_floor(keltner, floor)

    # IV rank: record today's IV, then rank vs this name's own accumulated history.
    # Falls back to the realized-vol proxy until the store has enough days.
    _iv_record(ticker, iv)
    ivr_hist = _iv_rank_hist(ticker, iv)
    ivr = ivr_hist if ivr_hist is not None else _iv_rank(closes)

    contract = {
        "opt_type": "put", "iv": iv, "rv": vrp_rv, "iv_rank": ivr,
        "prob_otm": prob_otm, "bid": bid, "ask": ask, "open_interest": oi, "volume": vol,
        "annualized_roc": roc, "want_to_own": want_to_own, "dte": dte,
        "days_to_earnings": (earnings_days if earnings_days is not None else 999),
        "trend_align": struct,
    }
    scored = score_contract(contract)
    return {
        "ticker": ticker, "spot": round(spot, 2), "candles": candles,
        "pick": {
            "strike": round(strike, 2), "dte": dte, "exp": exp, "premium": round(premium, 2),
            "annualized_roc": round(roc * 100, 1), "prob_otm": round(prob_otm * 100, 1),
            "iv": round(iv * 100, 1), "iv_rank": contract["iv_rank"],
            "iv_rank_real": ivr_hist is not None, "source": source,
            "earnings_days": earnings_days, "want_to_own": want_to_own,
            # His method, surfaced: struck AT support (or 1-sigma fallback), and the
            # IV-over-HV edge gate (rich premium = VRP > 1).
            "at_support": at_support, "support": (round(support, 2) if support else None),
            "support_floor": (round(floor, 3) if floor is not None else None),
            "iv_gt_hv": iv_gt_hv, "vrp": vrp,
            # Levels for the chart: the Keltner volatility walls PLUS the major
            # price-action support/resistance (where the stock actually bounces).
            "levels": _levels(candles, spot, support, resistance),
            "free_shares": free_shares_read(spot, strike, premium, roc, prob_otm,
                                            want_to_own=True),
            **scored,
        },
    }


def _load_prev():
    """Snapshot of the PREVIOUS scan (read before we overwrite it) for the diff."""
    try:
        with open(OUT) as f:
            d = json.load(f)
        prev = {t["ticker"]: {"score": t["pick"].get("score"), "avoid": t["pick"].get("avoid")}
                for t in d.get("tickers", [])}
        return prev, d.get("generated_at")
    except Exception:
        return {}, None


def _compute_changes(prev, tickers):
    """What moved since the last scan: new/gone names, AVOID flips, score movers."""
    cur = {t["ticker"]: t["pick"] for t in tickers}
    movers = []
    for tk, p in cur.items():
        pv = prev.get(tk)
        if pv and pv.get("score") is not None and p.get("score") is not None:
            d = round(p["score"] - pv["score"], 1)
            if abs(d) >= 3:
                movers.append({"ticker": tk, "delta": d})
    movers.sort(key=lambda x: abs(x["delta"]), reverse=True)
    return {
        "new": [tk for tk in cur if tk not in prev][:6],
        "gone": [tk for tk in prev if tk not in cur][:6],
        "to_avoid": [tk for tk in cur if cur[tk].get("avoid")
                     and tk in prev and not prev[tk].get("avoid")][:6],
        "from_avoid": [tk for tk in cur if not cur[tk].get("avoid")
                       and tk in prev and prev[tk].get("avoid")][:6],
        "movers": movers[:6],
    }


def main():
    prev, prev_ts = _load_prev()
    from wheelforge.universe import combined_universe
    rows = combined_universe()  # liquid lane + high-IV lane (rich premium), lane-tagged
    print(f"universe: {len(rows)} names (liquid + high-IV lanes)")
    tickers = []
    for r in rows:
        tk = r["ticker"]
        try:
            one = build_one(tk, r.get("earnings_days"), r.get("lanes"))
            if one:
                one["pick"]["lanes"] = r.get("lanes", [])
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
    if not tickers:
        # Never blank the live site: a transient screener/data failure must leave the
        # last good scan.json in place, not overwrite it with an empty list.
        print("scan produced 0 names; keeping the last good scan.json")
        return

    out = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_note": note, "dte": DTE, "tickers": tickers,
        "changes": _compute_changes(prev, tickers),
        "prev_generated_at": prev_ts,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nwrote {OUT} ({len(tickers)} names)")


if __name__ == "__main__":
    main()
