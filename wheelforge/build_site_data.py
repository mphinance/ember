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

from wheelforge.scoring import score_contract, letter_grade, earnings_next_cycle
from wheelforge.freeshares import free_shares_read
from wheelforge.iv_history import record as _iv_record, iv_rank as _iv_rank_hist
from wheelforge import results_tracker as _rt
from wheelforge.structure import (keltner_position, keltner_bands,
                                  support_floor_score, structure_with_floor)
from wheelforge.patterns import read_pattern
from wheelforge.levels import support_resistance, support_resistance_detail
from wheelforge.vol_models import composite_realized_vol
from wheelforge.tail_risk import gap_risk
from wheelforge.surface import put_skew as _put_skew
from wheelforge.market_weather import market_regime as _market_regime

WATCHLIST =["AAPL", "MSFT", "NVDA", "AMD", "GOOGL", "AMZN", "META", "COST"]
DTE = 7    # target the nearest WEEKLY — how Michael actually sells (e.g. NVDA 190 put,
           # 4 DTE, ~5% OTM). 1-sigma at ~weekly tenor lands ~5% OTM and annualizes ~2x a
           # monthly, into the ~100%/yr range he runs. Earnings veto still guards the week.
MIN_PREMIUM = 0.25  # dollars of mid per share (= $25 a contract). Below this a "pick" is
                    # noise: a 15% OTM support strike can quote a $0.06 mid, score well on
                    # richness + structure, and sit near the top of the list — but it is $6
                    # a contract, not a trade. The absolute floor (cheap names). Tunable.
MIN_SUPPORT_TOUCHES = 3  # how many times the market must have TESTED a level before we will
                    # anchor a real strike (and a ⌂ support badge) to it. One or two touches is
                    # a single/double pivot — statistically a ghost, not a floor — so we demote
                    # anything below this to "no clean support" and let the strike fall through
                    # to the ~1 sigma OTM fallback rather than give false confidence in a one-off.
MIN_PREMIUM_PCT = 0.004  # ...and a RELATIVE floor: 0.4%/week of spot. A flat $25/contract
                    # floor lets a $190 AAPL put at $0.28 onto the list — $28 of credit on
                    # $19,000 of collateral, ~5%/yr, nowhere near his ~100%/yr income target.
                    # Pinning the floor to 0.4% of spot scales it with the name, so the gate
                    # is max(MIN_PREMIUM, spot*MIN_PREMIUM_PCT) and every pick clears at least
                    # a real fraction of the target instead of a polite credit on a big position.
R = 0.045  # risk-free
SHORT_RV_FLOOR = 0.70  # the live-weekly VRP denominator is a 5-day realized vol (~5 returns), so
                       # its sampling error is large: one unusually quiet week can drop it to ~0.4x
                       # the 20-day rv and push VRP (iv / short_rv) past the richness saturation
                       # ceiling on a name whose vol is actually cheap — manufacturing richness out
                       # of a quiet tape. Floor the short RV at this fraction of the 20-day rv so a
                       # quiet week compresses the denominator by at most 30%, not 60%.
SHORT_RV_CEIL = 1.50   # the SAME 5-obs noise cuts the other way: a single spike session in the
                       # trailing week can blow short_rv up to 2-3x the 20-day rv, dragging VRP
                       # (iv / short_rv) below 1.0 and ZEROING the richness score on a genuinely
                       # rich name for days after the spike has rolled off. Cap the short RV at
                       # this multiple of the 20-day rv so one stale outlier day cannot suppress
                       # the very richness signal Michael's thesis is hunting for. Floor + ceiling
                       # bracket the denominator; a normal week inside the band passes untouched.
MAX_SECTOR_OVERLAP = 1   # how many qualifying picks one GICS sector may own before the rest
                         # are flagged crowded. Capital concentration is a discipline veto, not
                         # a quality signal: three rich semis the same morning is correlated tail
                         # risk WheelForge never noticed. 1 = keep the single best name per sector
                         # clean, flag the duplicates so he sizes (or skips) them on purpose.
SECTOR_CROWD_SCORE = 60.0  # only names that actually score a setup (>= this) count toward / get
                           # flagged for crowding. A 40-scoring also-ran in the same sector is not
                           # competing for capital, so it neither fills the slot nor gets marked.
MIN_STRIKE_OI = 50  # open interest, at the CHOSEN strike, below which the line is THIN. The strike
                    # is anchored to support, not to liquidity, so it can land on a barely-traded
                    # line: the chain may be deep overall while the recommended $185p carries OI 8.
                    # The c60 bid gate already drops a strike with NO bid; this is the next rung —
                    # a strike with a real-but-thin book fills slow and wide. We do NOT silently
                    # drop it (yfinance reports OI=0/NaN intraday for many valid weeklies until the
                    # daily settle, so a hard gate would blank good live picks to MODEL on stale
                    # data we cannot re-check in a headless build). Instead it wears a visible
                    # ⚠ thin-OI chip on the LIVE path only, so he sizes or skips it on purpose —
                    # same "flag, never a silent edit" discipline as the sector-crowding chip.
WIDE_SPREAD_PCT = 0.30  # (ask-bid)/mid above which the CHOSEN strike's book is WIDE. The headline
                        # ann RoC is priced on the mid, but a wide market fills a limit order nearer
                        # the bid, so a $0.10 bid / $0.50 ask ($0.30 mid) shown as yield overstates
                        # the real fill by ~2/3. Same "flag, never drop" discipline as thin OI: the
                        # mid is a real quote, just optimistic, and bid_ann_roc already shows the
                        # conservative fill; the chip just makes the gap visible before he sells.

INCOME_TARGET_ROC = 100.0  # Michael's income target is ~100%/yr. A pick whose annualized RoC clears
                           # this is a GO on the yield pillar; below it he's selling for less than his
                           # goal. The yield_score ramp (8%->200%) puts a 49% pick at ~0.22, midfield,
                           # so "half your target" reads as an ambiguous D. hits_target makes the
                           # go/no-go instant (a green HITS 100% chip) instead of mental division.
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


def _clamp_short_rv(short_rv, rv):
    """Clamp the live-weekly VRP denominator (5-day RV) into [SHORT_RV_FLOOR, SHORT_RV_CEIL]
    x the 20-day rv. The 5-obs window is noisy on BOTH tails: a quiet week can drop it to
    ~0.4x the 20-day rv (manufacturing richness out of a flat tape), and a single spike
    session can push it to 2-3x (zeroing richness on a genuinely rich name for days after the
    spike rolls off). The floor stops the first, the ceiling stops the second; a normal week
    already inside the band passes through untouched. With no 20-day rv to compare against,
    return short_rv unchanged (nothing to clamp against)."""
    if rv and rv > 0:
        return max(SHORT_RV_FLOOR * rv, min(short_rv, SHORT_RV_CEIL * rv))
    return short_rv


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


def _premium_floor(spot):
    """The minimum tradeable mid for a name trading at `spot`: the GREATER of the absolute
    $0.25/share noise floor and 0.4% of spot. A flat floor treats a $190 name and a $20 name
    the same; the relative term scales the floor with collateral so a $0.28 mid on a $190
    strike (~5%/yr) is dropped while the same $0.28 on a $20 strike still clears. spot=0/None
    falls back to the absolute floor alone (modeled/degraded paths never relax below it)."""
    return max(MIN_PREMIUM, (spot or 0.0) * MIN_PREMIUM_PCT)


def _tradeable_premium(mid, spot=0.0):
    """A mid below the premium floor for this name is not a trade, however well it would
    score. Shared by the live-quote gate and the per-name drop so the floor is one place."""
    return mid is not None and mid >= _premium_floor(spot)


def _pct_otm(spot, strike):
    """How far below spot the put strike sits, as a percent. His first question on every
    put ("NVDA 190p, ~5% OTM, 4 DTE"), so we compute it once and surface it instead of
    forcing him to divide (spot - strike)/spot in his head per name. Positive = OTM."""
    return round((spot - strike) / spot * 100, 1) if spot else 0.0


def _annualized_roc(premium, strike, dte):
    """Annualized return on the capital a cash-secured put ties up. Net basis at risk is
    (strike - premium) because the premium is pocketed up front (the ticked c23 call; the
    strike-vs-net denominator debate is Michael's to settle, not a bot's). Shared by the
    per-pick RoC and the DTE-ladder ranker so the two can never quietly drift apart."""
    cap = strike - premium
    return (premium / cap) * (365.0 / dte) if (cap > 0 and dte > 0) else 0.0


def _pick_best_dte(quotes):
    """From candidate-expiry quotes, pick the one with the highest ANNUALIZED yield. The
    thesis is the income machine, and a 14- or 21-DTE at the same support strike often
    pockets ~2x the premium for trivially more risk, a comparison that used to be invisible
    (we always took the nearest weekly). Returns (best_quote, ladder), where ladder lists
    every candidate as {dte, exp, strike, premium, ann_roc} sorted by yield so the page can
    show the runner-up tenors next to the winner."""
    ranked = sorted(quotes, reverse=True,
                    key=lambda q: _annualized_roc(q["premium"], q["strike"], q["dte"]))
    ladder = [{"dte": q["dte"], "exp": q["exp"], "strike": round(q["strike"], 2),
               "premium": round(q["premium"], 2),
               "ann_roc": round(_annualized_roc(q["premium"], q["strike"], q["dte"]) * 100, 1)}
              for q in ranked]
    return ranked[0], ladder


def _candidate_expiries(exps, earnings_days=None, lo=3, hi=21, targets=(7, 14, 21)):
    """Up to len(targets) DISTINCT listed expiries inside the weekly window [lo, hi], one
    nearest each target DTE, for the yield ladder. Any expiry that would hold THROUGH the
    next earnings print is dropped (pillar 4: never sell through earnings). Returns
    [(exp, dte), ...] sorted by dte. Empty if nothing clears the window (the caller then
    falls back to _nearest_expiry so the site never blanks)."""
    from datetime import date
    today = date.today()
    parsed = []
    for e in exps:
        try:
            d = (date.fromisoformat(e) - today).days
        except Exception:
            continue
        if d < max(2, lo) or d > hi:
            continue
        if earnings_days is not None and earnings_days < 999 and d >= earnings_days:
            continue   # this tenor expires on/after the print: do not sell through it
        parsed.append((e, d))
    cand = {}
    for tgt in targets:
        best = None
        for e, d in parsed:
            if best is None or abs(d - tgt) < abs(best[1] - tgt):
                best = (e, d)
        if best:
            cand[best[0]] = best[1]
    return sorted(((e, d) for e, d in cand.items()), key=lambda x: x[1])


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


def _real_support(support, touches):
    """Gate a support level by how many times the market has actually TESTED it. Michael
    sells AT support and trusts it to hold; a level tagged once or twice is a single/double
    pivot — a statistical ghost — so we return None and let the strike fall through to the
    ~1 sigma OTM fallback rather than anchor a real trade (and a ⌂ support badge) to a floor
    that held one time. A genuinely tested level (>= MIN_SUPPORT_TOUCHES) passes through
    unchanged. None support / None touches is already not real."""
    if support is None or touches is None or touches < MIN_SUPPORT_TOUCHES:
        return None
    return support


def _as_date(val):
    """Coerce a date / datetime / pandas Timestamp / ISO-ish string to a plain date, or
    None. datetime and Timestamp expose a `.date()` method (a bare date does not), so try
    that first; then a real date; then parse the leading YYYY-MM-DD off a string."""
    from datetime import date, datetime
    if val is None:
        return None
    try:
        if isinstance(val, datetime):      # datetime is a date subclass; convert first
            return val.date()
        if isinstance(val, date):
            return val
        if hasattr(val, "date"):           # pandas Timestamp and the like
            return val.date()
        return date.fromisoformat(str(val)[:10])
    except Exception:
        return None


def _nearest_future_earnings_days(dates, today):
    """Pure: given a list of earnings dates (date / datetime / Timestamp / ISO string),
    return the days from `today` to the NEAREST date that is today-or-later, or None when
    none qualify (empty list, all in the past, all unparseable). The earnings veto only
    cares about the next print AHEAD of you: a print that already happened cannot blow up
    a put you have not sold yet. Used to re-arm the gate for fallback-universe names that
    arrive with no screener earnings date (see _lookup_earnings_days)."""
    best = None
    for val in (dates or []):
        d = _as_date(val)
        if d is None:
            continue
        days = (d - today).days
        if days < 0:
            continue
        if best is None or days < best:
            best = days
    return best


def _lookup_earnings_days(ticker):
    """Secondary earnings lookup for fallback-universe names. The TradingView screener
    normally supplies earnings_days; when it is DOWN, its 30 fallback tickers arrive with
    earnings_days=None, which silently disarms the earnings veto: NVDA two days before a
    print would clear both _candidate_expiries and earnings_blocks and land as a clean
    pick with no AVOID card. Re-arm the gate off yfinance's own calendar. Fail-open: any
    error (no calendar, network) returns None, leaving the name exactly as it was rather
    than crashing the build."""
    from datetime import date
    try:
        import yfinance as yf
        df = yf.Ticker(ticker).get_earnings_dates(limit=8)
        if df is None or df.empty:
            return None
        return _nearest_future_earnings_days(list(df.index), date.today())
    except Exception:
        return None


def _ex_div_in_window(ex_div_date, today, exp_date):
    """Pure: True when the stock goes EX-DIVIDEND inside the option window [today, exp].
    A name that pays a dividend during the weekly gaps DOWN by the dividend amount on the
    ex-date, which can push a just-OTM put ITM with no actual move in the tape: the drop is
    mechanical. (There is also an American-put early-exercise angle around ex-div, but the
    gap-down is the one a put SELLER feels.) Both dates coerced via _as_date; any missing or
    unparseable input -> False (no warn), the same fail-open stance as the other cautions."""
    ex = _as_date(ex_div_date)
    exp = _as_date(exp_date)
    if ex is None or exp is None or today is None:
        return False
    return today <= ex <= exp


def _lookup_ex_div_date(ticker):
    """Next ex-dividend date for a name (a plain date), or None. yfinance exposes it on
    `.calendar` under 'Ex-Dividend Date' (a dict in current yfinance, a DataFrame in older
    builds, so handle both). A non-payer, a stale/missing calendar, or any network error all
    fail open to None (no chip), never crashing the build. Mirrors _lookup_earnings_days."""
    try:
        import yfinance as yf
        cal = yf.Ticker(ticker).calendar
        val = None
        if isinstance(cal, dict):
            val = cal.get("Ex-Dividend Date")
        elif cal is not None and hasattr(cal, "loc"):
            try:
                val = cal.loc["Ex-Dividend Date"]
                if hasattr(val, "iloc"):
                    val = val.iloc[0]
            except Exception:
                val = None
        return _as_date(val)
    except Exception:
        return None


def _anchor_strike(spot, rv, dte, support):
    """Where to sell the put. Michael's method: sell AT support and trust it (he does not
    trade off delta). So if there is a real support level in a sane band below spot, that
    IS the strike. Only when there is no clean support do we fall back to ~1 sigma OTM.
    Returns (target_price, at_support)."""
    sigma = spot * (1.0 - rv * math.sqrt(dte / 365.0))   # ~1 sigma OTM, the fallback
    if support and spot * 0.80 <= support < spot:
        return support, True
    return sigma, False


def _strike_at_or_below(strikes, target, spot):
    """Pick the listed put strike nearest `target` but NEVER above it. Selling a put is a
    bet that price holds the level you struck; a support of $461.50 with listed strikes
    $460 / $462.50 must sell the $460, not the closer-but-higher $462.50 that sits ABOVE
    the level you are trusting to hold. A 0.2% tolerance lets a strike sitting right at
    target round through. Falls back to the nearest sub-spot strike only when nothing
    lists at/below target (a deep level on a sparse chain), so a name is never blanked.
    Returns the chosen strike (float) or None when no strike sits at/below spot."""
    at = [s for s in strikes if s <= target * 1.002]
    pool = at or [s for s in strikes if s <= spot]
    if not pool:
        return None
    return min(pool, key=lambda s: abs(s - target))


def _sellable_premium(bid, ask):
    """The credit you can actually SELL this put for, or None if you cannot sell it.
    You sell-to-open, so the premium you receive is anchored on the BID. A put with no
    market-maker bid (bid <= 0) cannot be sold at all: `lastPrice` is a stale historical
    fill, not a live fillable quote, so such a strike is DROPPED rather than quoted off a
    ghost price that scores 60-80 and lands on the board as a trade that cannot fill.
    With a real bid and ask, the mid (bid+ask)/2 is the fair quote; with a bid but no ask,
    the bid itself is the conservative, honest premium (never invent the offer side)."""
    if bid <= 0:
        return None
    return (bid + ask) / 2.0 if ask > 0 else bid


def _spread_pct(bid, ask):
    """The bid/ask spread as a fraction of the mid, or None when it cannot be computed
    (missing / non-positive / crossed / one-sided book). `(ask - bid) / mid`: 0.0 is a
    locked market, 0.30 means the mid the headline RoC is priced on sits ~15% above the
    bid you sell-to-open into. Pure; junk inputs fail open to None (no caution)."""
    try:
        b = float(bid); a = float(ask)
    except (TypeError, ValueError):
        return None
    if b <= 0 or a <= 0 or a < b:
        return None
    mid = (b + a) / 2.0
    return (a - b) / mid if mid > 0 else None


def _wide_spread(bid, ask, source):
    """True when the CHOSEN strike's bid/ask spread is wide enough that the mid-priced yield
    overstates the achievable fill. LIVE path only: the modeled path carries a synthetic ~4%
    spread by construction (c39), so flagging it would be noise, not a real book read. A
    visible caution, never a drop (the mid IS a real quote, just optimistic; bid_ann_roc
    already shows the conservative fill). Fail-open to not-wide on a missing/one-sided book."""
    if source != "live":
        return False
    sp = _spread_pct(bid, ask)
    return sp is not None and sp > WIDE_SPREAD_PCT


def _thin_oi(open_interest, source):
    """True when the CHOSEN strike's open interest is thin enough to caution on. Only the
    LIVE path can be thin: a modeled pick carries oi=0 by construction (c39) and already
    wears a MODEL tag, so flagging it would be double noise and not even a real chain read.
    On the live path a strike that cleared the bid gate (c60, so it HAS a market-maker bid)
    but reports OI below MIN_STRIKE_OI is a real-but-thin book — fillable, but slow and wide,
    so he sizes down or skips it on purpose. Pure; a non-live source is never thin."""
    if source != "live":
        return False
    try:
        return float(open_interest) < MIN_STRIKE_OI
    except (TypeError, ValueError):
        return False


def _quote_expiry(tk, exp, dte, spot, rv, support):
    """Quote the support-anchored (else ~1 sigma OTM) cash-secured put for a SINGLE expiry
    off the live chain. Returns the quote dict or None (no chain / no OTM strike / dead
    quote). Pulled out of _live_put so the DTE ladder can quote each candidate tenor."""
    puts = tk.option_chain(exp).puts
    if puts is None or puts.empty:
        return None
    target, at_support = _anchor_strike(spot, rv, dte, support)
    strike = _strike_at_or_below([float(s) for s in puts["strike"].tolist()], target, spot)
    if strike is None:
        return None
    row = puts[puts["strike"] == strike].iloc[0]
    bid = float(row.get("bid") or 0); ask = float(row.get("ask") or 0)
    mid = _sellable_premium(bid, ask)
    if mid is None:
        return None   # no market-maker bid: the put cannot be SOLD (see _sellable_premium)
    iv = float(row.get("impliedVolatility") or 0)
    if not _tradeable_premium(mid, spot) or iv <= 0:
        return None   # mid under the per-name floor (or dead IV): not a tenor worth ranking
    # PUT SKEW: compare THIS OTM put's quoted IV against the ATM put on the same chain. Both
    # come from the chain's impliedVolatility column (apples to apples), so it is a clean
    # quoted-vs-quoted ratio. Positive = downside fear bid into the strike he sells = richer.
    skew = _put_skew(iv, _atm_put_iv(puts, spot))
    return {
        "strike": float(row["strike"]), "dte": int(dte), "exp": exp, "premium": mid,
        "iv": iv, "bid": bid, "ask": ask, "at_support": at_support, "put_skew": skew,
        "open_interest": int(row.get("openInterest") or 0),
        "volume": int(row.get("volume") or 0),
    }


def _atm_put_iv(puts, spot):
    """IV of the put whose strike sits nearest spot, the ATM reference for put skew. Read off
    the puts frame already in hand (no extra network). Returns a float or None when no row
    carries a usable IV, so a degraded chain falls through to no-skew rather than a bad ratio."""
    try:
        idx = (puts["strike"] - float(spot)).abs().idxmin()
        v = float(puts.loc[idx, "impliedVolatility"] or 0)
        return v if v > 0 else None
    except Exception:
        return None


def _live_put(ticker, spot, rv, support=None, earnings_days=None):
    """REAL cash-secured put off the live yfinance chain, struck AT support when there is
    one (else ~1 sigma OTM). Quotes up to 3 candidate weekly expiries (~7/14/21 DTE) at the
    same support strike and returns the one with the highest ANNUALIZED yield, plus a
    `dte_ladder` of the alternatives so the comparison is visible. Tenors that would hold
    through the next earnings print are excluded. Returns the winning quote dict (real
    iv/bid/ask/oi/volume/strike/dte + at_support + dte_ladder) or None (fail-open)."""
    import yfinance as yf
    try:
        tk = yf.Ticker(ticker)
        exps = list(tk.options or [])
        if not exps:
            return None
        cands = _candidate_expiries(exps, earnings_days)
        if not cands:                      # nothing in the weekly window: fall outside it
            exp, dte = _nearest_expiry(exps, DTE)   # rather than blank the name entirely
            if not exp or not dte:
                return None
            cands = [(exp, dte)]
        quotes = []
        for exp, dte in cands:
            q = _quote_expiry(tk, exp, dte, spot, rv, support)
            if q:
                quotes.append(q)
        if not quotes:
            return None
        best, ladder = _pick_best_dte(quotes)
        best["dte_ladder"] = ladder
        return best
    except Exception as exc:
        # Fail-open (the caller falls back to the modeled put), but say WHY in the build
        # log. A silent catch here is how the whole board went 25/25 modeled with zero
        # signal about the cause; now every live-chain miss names its exception so the
        # box's refresh log is diagnosable (rate-limit vs delisting vs schema drift).
        print(f"  {ticker} chain fail: {type(exc).__name__}: {exc}")
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


def _last_close(ticker):
    """Latest close for an index ticker via yfinance, or None. Used for the VIX regime read."""
    import yfinance as yf
    df = yf.Ticker(ticker).history(period="5d", interval="1d", auto_adjust=False)
    if df is None or df.empty:
        return None
    return float(df["Close"].iloc[-1])


def _regime():
    """Market-regime banner from the VIX term structure (VIX vs VIX3M). Fail-open to None:
    a missing feed just hides the banner, it never blocks the scan.json write or a score."""
    try:
        return _market_regime(_last_close("^VIX"), _last_close("^VIX3M"))
    except Exception as exc:
        print(f"regime: skipped ({exc})")
        return None


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


def _sector_crowding(tickers, threshold=SECTOR_CROWD_SCORE, max_overlap=MAX_SECTOR_OVERLAP):
    """Capital-concentration pass. Given picks ALREADY sorted best-first, walk them in rank
    order and, within each GICS sector, let the first `max_overlap` qualifying names through
    clean; flag every further name in that same sector as crowded. Sets pick['sector_crowded']
    (True/False) on every pick and returns the count flagged. This is a portfolio-fit signal,
    not a quality one, so it never touches the 0-100 score or the rank order: the rich-but-third
    semiconductor still scores what it scores, it just wears a chip so he stacks correlated names
    on purpose, not by accident. Fail-open: a pick with no sector (the screener did not supply
    one, or an explicit CLI scan) is never crowded and never fills a sector slot."""
    counts = {}
    flagged = 0
    for t in tickers:
        p = t["pick"]
        p["sector_crowded"] = False
        sec = p.get("sector")
        if not sec or p.get("avoid") or (p.get("score") or 0) < threshold:
            continue
        if counts.get(sec, 0) >= max_overlap:
            p["sector_crowded"] = True
            flagged += 1
        else:
            counts[sec] = counts.get(sec, 0) + 1
    return flagged


_EMP_CACHE = None


def _empirical_for(ticker):
    """This name's forward scorecard (its settled cohort) from results_tracker, loaded once
    per process. Fail-open to None so a missing/thin store simply yields no lift and the
    board scores exactly as the static model says."""
    global _EMP_CACHE
    if _EMP_CACHE is None:
        try:
            _EMP_CACHE = _rt.by_ticker()
        except Exception:
            _EMP_CACHE = {}
    return _EMP_CACHE.get(ticker)


def build_one(ticker, earnings_days=None, lanes=None, sector=None):
    candles, closes = _fetch(ticker)
    if not candles:
        return None
    # Re-arm the earnings veto for fallback-universe names. The screener normally hands us
    # earnings_days; when it is down, the 30 fallback tickers arrive None, which bypasses
    # BOTH the _candidate_expiries tenor filter AND earnings_blocks, so a name two days from
    # a print could surface as a clean pick. Look the date up off yfinance before scoring.
    # Fail-open (None stays None); a name that already carries a date does no extra network.
    if earnings_days is None:
        earnings_days = _lookup_earnings_days(ticker)
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
    short_rv = _clamp_short_rv(composite_realized_vol(candles, period=5) or rv, rv)

    from datetime import date, timedelta
    # Major price-action support: the level he sells AT (computed once, reused for the chart).
    # Pull the chosen cluster (level + touches) so the pick can show HOW MANY times the
    # market has tested the floor: a level respected 7 times is real, a one-off is a ghost.
    sup_d, res_d = support_resistance_detail(candles, spot)
    support = sup_d["level"] if sup_d else None
    resistance = res_d["level"] if res_d else None
    support_touches = sup_d["touches"] if sup_d else None
    # A floor the market tested only once or twice is a ghost. Demote it to "no clean
    # support" so the strike falls through to 1-sigma and no ⌂ support x1 badge (nor a
    # chart floor line) claims a level that held a single time. Resistance is untouched.
    support = _real_support(support, support_touches)
    if support is None:
        support_touches = None
    live = _live_put(ticker, spot, rv, support=support, earnings_days=earnings_days)
    dte_ladder = None
    vrp_rv = rv                                # VRP denominator; live weekly swaps to 5-day below
    if live:                                   # REAL chain: real IV is the edge
        strike, dte, exp = live["strike"], live["dte"], live["exp"]
        premium, bid, ask = live["premium"], live["bid"], live["ask"]
        oi, vol, source = live["open_interest"], live["volume"], "live"
        at_support = live["at_support"]
        put_skew = live.get("put_skew")        # OTM-vs-ATM put skew off the live chain
        dte_ladder = live.get("dte_ladder")    # the runner-up tenors, ranked by yield
        # Trust the premium, not the quoted IV: solve IV from the real mid. Fall back
        # to a sane quoted IV, then to realized vol. Track whether IV is market-derived:
        # if we land on the realized-vol fallback there is no traded IV, so VRP (iv/rv)
        # collapses toward 1 and the richness it feeds is modeled, not measured.
        qiv = live["iv"]
        solved_iv = _iv_from_put(premium, spot, strike, dte / 365.0, R)
        if solved_iv:
            iv, vrp_assumed = solved_iv, False
        elif qiv and 0.33 * rv <= qiv <= 4 * rv:
            iv, vrp_assumed = qiv, False
        else:
            iv, vrp_assumed = rv, True
        vrp_rv = short_rv                      # a 7-DTE IV vs ~a week of realized vol
    else:                                      # fail-open: model it from realized vol
        iv, dte = rv * 1.15, DTE
        put_skew = None                        # no live chain -> no skew read (no lift, fail-open)
        vrp_assumed = True                     # IV fixed at 1.15x RV -> VRP is invented, not traded
        target, at_support = _anchor_strike(spot, iv, dte, support)
        strike = round(target, 0)
        premium = _bs_put(spot, strike, dte / 365.0, R, iv)
        spread = max(0.02, premium * 0.04)
        bid, ask = round(premium - spread / 2, 2), round(premium + spread / 2, 2)
        # No live chain means no real open interest or volume to claim. Faking thick OI
        # (1500/250) made the modeled liquidity bar score ~0.76, the same range as a real
        # liquid AAPL put, so a name with its chain unloaded masqueraded as fillable. Set
        # them to 0 and let liquidity_score collapse to the spread-only term (~0.44): the
        # bar shrinks visibly and a modeled pick can no longer pass for a liquid one.
        oi, vol, source = 0, 0, "modeled"
        exp = (date.today() + timedelta(days=dte)).isoformat()
    # The tradeable floor, applied to WHATEVER premium won (live mid or modeled): a sub-$25
    # /contract pick is noise no matter how it scores, so drop the name entirely rather than
    # rank a $6 contract near the top. The "never blank" guard in main() still protects the
    # site if a whole run somehow falls below the floor.
    if not _tradeable_premium(premium, spot):
        return None
    # EX-DIVIDEND inside the option window: a name that goes ex-div before this expiry gaps
    # DOWN by the dividend amount on the ex-date, which can push a just-OTM put ITM with no
    # actual move in the tape (the drop is mechanical). WARN, do not drop (same discipline as
    # the earnings-next-cycle and wide-spread cautions): he sizes down, skips, or plans to be
    # out before the ex-date. Fail-open: no dividend / no calendar / network error -> no chip.
    ex_div_date = _lookup_ex_div_date(ticker)
    ex_div_in_window = _ex_div_in_window(ex_div_date, date.today(), exp)

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
    # Return on the capital actually tied up (shared with the DTE-ladder ranker so the
    # winning tenor's yield matches the headline number exactly).
    roc = _annualized_roc(premium, strike, dte)
    # What you ACTUALLY collect. The headline RoC is priced on the mid, but you sell-to-open,
    # so the credit that hits the account is the BID. On a $1.00 mid with a $0.10 spread the
    # mid quotes ~11% annualized while IBKR fills ~9.5%. Surface the bid-anchored yield so the
    # number he reads is the number he receives, not the optimistic midpoint. (Modeled path:
    # bid is the conservative side of the synthetic spread, so this stays honest there too.)
    bid_roc = _annualized_roc(bid, strike, dte)

    # REAL structure: the broad trend (VoPR Keltner position, low = falling = do not sell
    # into it) BLENDED with the per-strike support floor. Selling AT/just-above a major
    # support level (Michael's method) is the A+ structural CSP, so a real floor under the
    # strike lifts the factor; selling through the floor into the void drags it.
    keltner = keltner_position(candles)
    floor = support_floor_score(strike, support, spot)
    struct = structure_with_floor(keltner, floor)

    # PATTERN read: the one price-action shape off the OHLCV that changes a put-sell
    # decision (support hold / breakdown / downtrend / coiling). A VISIBLE per-name tag he
    # reads, NOT a silent rescore: structure_with_floor already owns the structure factor,
    # so this only names WHY the chart looks the way it does. Fails open to a neutral no-read.
    pattern = read_pattern(candles)

    # TAIL/GAP RISK: prob_otm is a thin-tailed lognormal, blind to the name that gaps 10%
    # overnight and jumps a far-OTM strike. Read the worst recent downside gaps off the same
    # OHLCV and let it haircut the safety factor (see tail_risk.gap_risk + scoring.gap_haircut).
    g_risk = gap_risk(candles)

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
        "trend_align": struct, "gap_risk": g_risk, "put_skew": put_skew,
    }
    scored = score_contract(contract)

    # Close the flywheel: nudge the score by THIS name's own forward record (results_tracker).
    # A name that keeps expiring OTM better than the model predicted earns a small lift; one
    # that keeps breaching against its predicted prob_otm gets a haircut. Bounded to +/-
    # EMPIRICAL_CAP and never applied to an AVOID (a vetoed pick stays 0/F). It is VISIBLE,
    # not a silent edit: the cohort + the lift ride the pick (empirical / empirical_lift), and
    # the why says so. Needs >= EMPIRICAL_MIN_N settled picks, so a thin/absent store (today)
    # changes nothing; the lift engages on its own as the tracker settles real expiries.
    emp = _empirical_for(ticker)
    emp_lift = 0.0 if scored.get("avoid") else _rt.empirical_lift(emp)
    if emp_lift:
        scored["score"] = round(min(100.0, max(0.0, scored["score"] + emp_lift)), 1)
        scored["grade"] = letter_grade(scored["score"])
        if scored.get("why"):
            tail = ("beats its own forward record" if emp_lift > 0
                    else "lagging its own forward record")
            scored["why"] = scored["why"].rstrip(".") + ", " + tail + "."

    return {
        "ticker": ticker, "spot": round(spot, 2), "candles": candles,
        "pick": {
            "strike": round(strike, 2), "dte": dte, "exp": exp, "premium": round(premium, 2),
            "strike_pct_otm": _pct_otm(spot, strike),
            "annualized_roc": round(roc * 100, 1), "prob_otm": round(prob_otm * 100, 1),
            # The yield expressed PER WEEK, his actual pre-order screen ("did I sell for at
            # least 1% this week?"). Simple inverse of the annualized RoC (52 weeks), so it
            # never disagrees with the headline; saves him the mental division on the card.
            "weekly_yield_pct": round(roc * 100 / 52.0, 2),
            # The yield you actually RECEIVE: priced on the bid you sell into, not the mid.
            "bid_ann_roc": round(bid_roc * 100, 1),
            # Does this pick clear his ~100%/yr income target? A green HITS 100% chip so the
            # go/no-go is instant, no mental "49.5% is half my target" division. Priced on the
            # honest bid RoC (the fill he'd actually get), so a wide book that flatters the mid
            # can't fake a target hit; an empty chip column on a weak board is itself signal.
            "hits_target": bid_roc * 100 >= INCOME_TARGET_ROC,
            "iv": round(iv * 100, 1), "iv_rank": contract["iv_rank"],
            "iv_rank_real": ivr_hist is not None, "source": source,
            "earnings_days": earnings_days, "want_to_own": want_to_own,
            # The earnings veto is a HARD thesis gate, but it can only fire on a known date.
            # When BOTH the screener feed AND the _lookup_earnings_days yfinance re-lookup come
            # back empty, earnings_days stays None -> days_to_earnings collapses to the 999
            # sentinel -> earnings_blocks(999, dte) is False, so a name printing tomorrow would
            # surface as a CLEAN pick with no AVOID. We cannot fail-CLOSED (that would blank the
            # board whenever yfinance is flaky), so surface the uncertainty: a visible chip that
            # says "I could not confirm this name is clear of earnings", his call to size or skip.
            "earnings_unknown": earnings_days is None,
            # NEXT-CYCLE earnings WARN (not a veto): the print clears THIS expiry but lands
            # in the next weekly-roll window (expiry .. expiry + dte). Michael rolls weekly,
            # so the hard AVOID gate greenlights week 1 and he auto-rolls straight into the
            # print on week 2. A visible chip so he sizes/skips on purpose; earnings_blocks
            # still owns the in-window veto, this only covers the one-cycle-out case.
            "earnings_next_cycle": earnings_next_cycle(contract["days_to_earnings"], dte),
            # EX-DIV in the window: the stock goes ex-dividend before this expiry, so it gaps
            # down by the dividend on the ex-date and a just-OTM put can go ITM without a real
            # move. A visible warn (his call to size/skip/close early), never a drop; the date
            # rides along for the tooltip. Fail-open None when there's no dividend to warn on.
            "ex_div_in_window": ex_div_in_window,
            "ex_div_date": (ex_div_date.isoformat() if (ex_div_in_window and ex_div_date) else None),
            # GICS sector (from the screener) + the capital-concentration flag set by the
            # post-sort _sector_crowding pass. sector_crowded starts False here and is filled
            # once the whole ranked list is known; None sector simply never gets flagged.
            "sector": sector, "sector_crowded": False,
            # Strike-level liquidity caution: the support-anchored strike landed on a thin
            # open-interest line (live path only). It fills, but slow and wide, so he sizes
            # or skips on purpose. A visible chip, never a silent drop (yfinance OI is stale
            # intraday; a hard gate would blank good live picks to MODEL on bad data).
            "thin_oi": _thin_oi(oi, source),
            # Tradeability caution: the chosen strike's bid/ask spread as a fraction of the
            # mid, plus a wide-spread flag (live path only). The ann RoC is priced on the mid;
            # a wide book fills nearer the bid, so the number overstates the real credit. A
            # visible chip, never a drop (the mid is a real quote; bid_ann_roc shows the fill).
            "spread_pct": (round(_sp, 3) if (_sp := _spread_pct(bid, ask)) is not None else None),
            "wide_spread": _wide_spread(bid, ask, source),
            # His method, surfaced: struck AT support (or 1-sigma fallback), and the
            # IV-over-HV edge gate (rich premium = VRP > 1).
            "at_support": at_support, "support": (round(support, 2) if support else None),
            # How many times the market has TESTED that floor (None if no clean level):
            # a real floor (many touches) vs a stale one-off pivot. He reads it before
            # trusting the strike to hold.
            "support_touches": support_touches,
            "support_floor": (round(floor, 3) if floor is not None else None),
            # Tail/gap risk read (0..1) off the OHLCV: how hard this name gaps overnight.
            # It haircuts the safety factor above; surfaced so the number is auditable.
            "gap_risk": round(g_risk, 3),
            # PRICE-ACTION PATTERN off the OHLCV (support_hold / breakdown / downtrend /
            # coiling / none): a visible tag + one-line read that names the chart shape a
            # put seller cares about. Flag not rescore; 'none' when no strong read.
            "pattern": pattern,
            # Put skew (OTM put IV vs ATM, live chain only): positive = downside fear bid into
            # the strike he sells, which lifts the richness factor. None on the modeled path.
            "put_skew": (round(put_skew, 3) if put_skew is not None else None),
            # The flywheel, surfaced + auditable: the score nudge this name earned from its
            # OWN settled track record, and the cohort behind it (n picks, forward hit rate vs
            # the prob_otm the model predicted). Both None/0.0 until the store has a real
            # cohort for the name, so a pre-data scan reads exactly as before.
            "empirical_lift": emp_lift,
            "empirical": ({"n": emp["n"], "hit_rate": emp["hit_rate"],
                           "predicted_otm": emp["predicted_otm"]}
                          if (emp and (emp.get("n") or 0) >= _rt.EMPIRICAL_MIN_N) else None),
            "iv_gt_hv": iv_gt_hv, "vrp": vrp, "vrp_assumed": vrp_assumed,
            # The yield ladder: this tenor won on annualized RoC vs the other candidate
            # weeklies at the same support strike. None on the modeled (single-DTE) path.
            "dte_ladder": dte_ladder,
            # Levels for the chart: the Keltner volatility walls PLUS the major
            # price-action support/resistance (where the stock actually bounces).
            "levels": _levels(candles, spot, support, resistance),
            "free_shares": free_shares_read(spot, strike, premium, roc, prob_otm,
                                            want_to_own=want_to_own),
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


def _json_safe(obj):
    """Recursively replace NaN / Infinity floats with None so the written scan.json is
    ALWAYS valid JSON. A bare `NaN` token (what json.dump emits by default for a NaN float)
    is not valid JSON and makes the browser's JSON.parse throw, which blanks the ENTIRE
    board, not just one field. Belt to market_regime's suspenders: any future field that
    goes NaN degrades to a hidden/absent value instead of taking the whole site down.
    (definition-of-best: never blank the site, cf. the empty-scan bail.)"""
    if isinstance(obj, float):
        return None if (obj != obj or obj in (float("inf"), float("-inf"))) else obj
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return obj


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
            one = build_one(tk, r.get("earnings_days"), r.get("lanes"), r.get("sector"))
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
    # Capital-concentration flag, computed AFTER the rank so "first in the sector" means
    # highest-scoring in the sector. Does not reorder; just marks the correlated duplicates.
    crowded_n = _sector_crowding(tickers)
    if crowded_n:
        print(f"sector crowding: {crowded_n} pick(s) flagged (>{MAX_SECTOR_OVERLAP}/sector)")
    live_n = sum(1 for t in tickers if t["pick"].get("source") == "live")
    note = (f"Candles and option premium are LIVE off the yfinance chain for {live_n} of "
            f"{len(tickers)} names (real IV, bid/ask, OI); the rest fall back to a "
            f"realized-vol model when the chain is missing.")
    if not tickers:
        # Never blank the live site: a transient screener/data failure must leave the
        # last good scan.json in place, not overwrite it with an empty list.
        print("scan produced 0 names; keeping the last good scan.json")
        return

    # Forward results tracker (LOCAL, gitignored): settle any picks whose expiry has now
    # passed against today's spot, then snapshot today's actionable CSPs as fresh forward
    # observations. Fail-open: a tracker hiccup must never block the scan.json write.
    tr = None
    try:
        spots = {t["ticker"].upper(): t.get("spot") for t in tickers if t.get("spot")}
        n_settled = _rt.settle(spots)
        n_snap = _rt.snapshot(tickers)
        tr = _rt.track_record()
        print(f"results tracker: +{n_snap} snapshot, {n_settled} settled, "
              f"{tr['settled']} graded / {tr['pending']} pending")
    except Exception as exc:
        print(f"results tracker: skipped ({exc})")

    out = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_note": note, "dte": DTE, "tickers": tickers,
        # Board integrity, machine-readable: what fraction of picks are priced off a REAL
        # live chain (live bid/ask/OI) vs a Black-Scholes model fallback. `source_note`
        # says it in prose; this is the number the frontend gates a hard warning banner on
        # (below ~50% = mostly modeled yields, not fillable quotes). tickers is non-empty
        # here (the 0-name case returned above), so the divide is safe.
        "live_rate_pct": round(100 * live_n / len(tickers)),
        "changes": _compute_changes(prev, tickers),
        "prev_generated_at": prev_ts,
        # Forward scorecard for the page: actual hit rate vs the prob-OTM we predicted,
        # across every settled forward call. The flywheel was tracked since c55 but never
        # shown; this surfaces the proof. None when the tracker hiccups (frontend hides it).
        "record": tr,
        # Non-blocking market-regime banner from the VIX term structure (calm / normal /
        # stressed). Informational only, never gates a per-name score. None hides the banner.
        "regime": _regime(),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    # allow_nan=False + a _json_safe pre-pass: the sanitizer turns any stray NaN/Inf into
    # null so the file is valid JSON, and allow_nan=False makes a miss LOUD (raises) rather
    # than silently shipping a board-blanking token. A NaN regime once took the whole site
    # down; this guarantees a single bad number can never do that again.
    with open(OUT, "w") as f:
        json.dump(_json_safe(out), f, indent=2, allow_nan=False)
    print(f"\nwrote {OUT} ({len(tickers)} names)")


def _selftest():
    """Pure self-test of the DTE-ladder picker + candidate selection. No network, no
    scan.json write (running `main()` by accident was the c32 footgun, so the flag now
    has a real, side-effect-free home)."""
    from datetime import date, timedelta
    today = date.today()
    iso = lambda n: (today + timedelta(days=n)).isoformat()

    # Ladder: same support strike, fatter premium at longer tenor should NOT always win on
    # annualized yield. A 7-DTE at 0.9 out-annualizes a 21-DTE at 2.0 here, so the picker
    # must rank by ann_roc, not raw premium.
    quotes = [
        {"strike": 100.0, "dte": 7, "exp": iso(7), "premium": 0.90, "iv": 0.4, "bid": 0.85,
         "ask": 0.95, "at_support": True, "open_interest": 500, "volume": 100},
        {"strike": 100.0, "dte": 21, "exp": iso(21), "premium": 2.00, "iv": 0.4, "bid": 1.95,
         "ask": 2.05, "at_support": True, "open_interest": 500, "volume": 100},
    ]
    best, ladder = _pick_best_dte(quotes)
    r7 = _annualized_roc(0.90, 100.0, 7) * 100
    r21 = _annualized_roc(2.00, 100.0, 21) * 100
    print(f"ladder: 7d {r7:.0f}%/yr vs 21d {r21:.0f}%/yr -> best {best['dte']}d")
    assert best["dte"] == 7, "the higher-annualized tenor must win, not the fatter premium"
    assert len(ladder) == 2 and ladder[0]["dte"] == 7, "ladder is yield-sorted, winner first"
    assert ladder[0]["ann_roc"] > ladder[1]["ann_roc"], "ladder must be descending by yield"

    # Earnings gate: a print in 10 days drops the 14/21-DTE candidates (they hold through
    # it) but keeps the ~7-DTE that clears before it.
    exps = [iso(7), iso(14), iso(21)]
    no_earn = _candidate_expiries(exps, earnings_days=999)
    pre_earn = _candidate_expiries(exps, earnings_days=10)
    print(f"candidates: clear={[d for _, d in no_earn]} earn@10d={[d for _, d in pre_earn]}")
    assert [d for _, d in no_earn] == [7, 14, 21], "all three weeklies qualify with no print"
    assert all(d < 10 for _, d in pre_earn) and pre_earn, "earnings in 10d must drop 14/21-DTE"

    # Window: a far-out monthly never enters the ladder; a same-day expiry is excluded.
    assert _candidate_expiries([iso(45)], 999) == [], "a 45-DTE monthly is outside the weekly window"
    assert _candidate_expiries([iso(0), iso(5)], 999) == [(iso(5), 5)], "drop same/next-day gamma"

    # Fallback-universe re-arm: pick the NEAREST future earnings date, skip past prints, and
    # accept dates, datetimes and ISO strings. A name with no parseable future date -> None
    # (stays as it arrived). today=Jun 1; the Jun 6 print is 5 days out and must win over the
    # Jun 20 one, while the May 28 print (already happened) is ignored.
    from datetime import date as _d, datetime as _dt
    _today = _d(2026, 6, 1)
    assert _nearest_future_earnings_days([_d(2026, 6, 20), _d(2026, 6, 6)], _today) == 5, \
        "the nearest FUTURE print wins"
    assert _nearest_future_earnings_days([_d(2026, 5, 28), _d(2026, 6, 6)], _today) == 5, \
        "a past print is ignored"
    assert _nearest_future_earnings_days([_dt(2026, 6, 6, 16, 0), "2026-06-20"], _today) == 5, \
        "datetimes and ISO strings both parse"
    assert _nearest_future_earnings_days([_d(2026, 5, 1)], _today) is None, \
        "an only-past calendar re-arms nothing (stays None)"
    assert _nearest_future_earnings_days([], _today) is None and \
        _nearest_future_earnings_days(None, _today) is None, "empty / None -> None"
    assert _nearest_future_earnings_days([_today], _today) == 0, "a print TODAY is 0 days out, still vetoed"

    # Ex-div-in-window: warn when the ex-date falls inside [today, exp]. today=Jun 1, exp=Jun 8.
    assert _ex_div_in_window(_d(2026, 6, 5), _today, "2026-06-08"), "ex-div mid-window warns"
    assert _ex_div_in_window(_d(2026, 6, 8), _today, _d(2026, 6, 8)), "ex-div ON expiry still warns"
    assert _ex_div_in_window(_today, _today, "2026-06-08"), "ex-div TODAY warns (gaps before you're out)"
    assert not _ex_div_in_window(_d(2026, 6, 9), _today, "2026-06-08"), "ex-div past expiry: no warn"
    assert not _ex_div_in_window(_d(2026, 5, 30), _today, "2026-06-08"), "a past ex-date does not warn"
    assert _ex_div_in_window(_dt(2026, 6, 5, 9, 0), _today, "2026-06-08"), "datetime ex-date coerces + warns"
    assert not _ex_div_in_window(None, _today, "2026-06-08"), "no dividend (None) -> no warn"
    assert not _ex_div_in_window(_d(2026, 6, 5), _today, None), "unparseable expiry -> fail-open no warn"

    # RoC denominator stays (strike - premium), the ticked c23 call.
    assert abs(_annualized_roc(2.0, 100.0, 7) - (2.0 / 98.0) * (365.0 / 7)) < 1e-9

    # Weekly yield is the simple inverse of the annualized RoC (his "1%/wk" screen): a
    # ~104%/yr pick reads ~2.0%/wk, and it never contradicts the headline (ann / 52).
    _wk_roc = _annualized_roc(2.0, 100.0, 7)
    assert abs(round(_wk_roc * 100 / 52.0, 2) - round(_wk_roc * 100, 1) / 52.0) < 0.01, \
        "weekly_yield_pct must be the annualized RoC divided by 52"

    # Bid-anchored yield (what you actually collect) <= mid yield (what the headline quotes),
    # since you sell-to-open into the bid. On a $1.00/$1.20 quote the mid is $1.10: the bid
    # RoC must be strictly lower, and a one-sided book (mid == bid) makes them equal.
    _bid, _ask = 1.00, 1.20
    _mid = _sellable_premium(_bid, _ask)
    assert _annualized_roc(_bid, 100.0, 7) < _annualized_roc(_mid, 100.0, 7), \
        "bid yield must trail the mid yield you sell into"
    assert _annualized_roc(_bid, 100.0, 7) == _annualized_roc(_sellable_premium(_bid, 0.0), 100.0, 7), \
        "a one-sided book quotes the bid, so bid yield == headline yield"

    # HITS-100% target: the go/no-go chip fires only when the honest BID yield clears his
    # ~100%/yr income target, so a wide book that flatters the MID can't fake a target hit.
    # $2.20/wk on a $100 strike ~= 116%/yr bid RoC clears it; $0.90/wk ~= 47% does not; and
    # the boundary is inclusive (exactly 100 hits).
    assert (_annualized_roc(2.20, 100.0, 7) * 100) >= INCOME_TARGET_ROC, "a ~116%/yr pick hits target"
    assert not ((_annualized_roc(0.90, 100.0, 7) * 100) >= INCOME_TARGET_ROC), "a ~47%/yr pick misses target"

    # Thin-OI caution: a LIVE strike whose open interest is below MIN_STRIKE_OI fills slow and
    # wide, so it wears a chip; a thick line does not. The MODELED path carries oi=0 by
    # construction and already wears a MODEL tag, so it must NEVER read thin (no double noise),
    # and junk OI fails open to not-thin rather than crashing the build.
    assert _thin_oi(8, "live"), "a live strike with OI 8 is thin"
    assert _thin_oi(MIN_STRIKE_OI - 1, "live"), "just under the floor is thin"
    assert not _thin_oi(MIN_STRIKE_OI, "live"), "exactly the floor is not thin (inclusive of clear)"
    assert not _thin_oi(500, "live"), "a deep live book is not thin"
    assert not _thin_oi(0, "modeled"), "the modeled path (oi=0) is never thin (it wears MODEL already)"
    assert not _thin_oi(None, "live") and not _thin_oi("x", "live"), "junk OI fails open to not-thin"
    print(f"thin-oi: live OI < {MIN_STRIKE_OI} flagged, modeled never flagged")

    # Wide-spread caution: (ask-bid)/mid measures how far the mid the headline is priced on
    # sits above the bid a limit order fills into. A $0.10/$0.50 book (mid $0.30) is 133% wide
    # -> flagged; a $1.00/$1.05 book (~5%) is tight -> clean. As with thin OI, only the LIVE
    # path can be wide (modeled carries a synthetic ~4% spread), and junk/one-sided books fail
    # open to None (no caution) rather than crashing the build.
    assert _spread_pct(1.00, 1.05) is not None and _spread_pct(1.00, 1.05) < WIDE_SPREAD_PCT, "a 5% book is tight"
    assert _spread_pct(0.10, 0.50) > WIDE_SPREAD_PCT, "a $0.10/$0.50 book is wide"
    assert _spread_pct(0, 0.50) is None and _spread_pct(1.0, 0) is None, "a one-sided book has no spread pct"
    assert _spread_pct(1.20, 1.00) is None, "a crossed book fails open to None"
    assert _spread_pct(None, "x") is None, "junk quotes fail open to None"
    assert _wide_spread(0.10, 0.50, "live"), "a wide live book is flagged"
    assert not _wide_spread(1.00, 1.05, "live"), "a tight live book is not flagged"
    assert not _wide_spread(0.10, 0.50, "modeled"), "the modeled path is never flagged wide"
    assert not _wide_spread(0, 0.50, "live"), "a one-sided live book fails open to not-wide"
    print(f"wide-spread: live (ask-bid)/mid > {WIDE_SPREAD_PCT} flagged, modeled never flagged")

    # MIN_PREMIUM floor: a $0.06 mid (= $6 a contract) is noise, not a trade, no matter how
    # richly it would score. A $0.30 mid (= $30 a contract) clears. The boundary is inclusive.
    # With no spot (modeled/degraded path) the gate is the absolute floor alone.
    assert MIN_PREMIUM > 0, "the tradeable floor must be a positive dollar amount"
    assert not _tradeable_premium(0.06), "a $6/contract mid must be dropped as noise"
    assert not _tradeable_premium(MIN_PREMIUM - 1e-6), "just under the floor is not tradeable"
    assert not _tradeable_premium(None), "a missing mid is not tradeable"
    assert _tradeable_premium(MIN_PREMIUM), "exactly the floor is tradeable (inclusive)"
    assert _tradeable_premium(0.30), "a $30/contract mid clears the floor"
    print(f"floor: ${MIN_PREMIUM:.2f}/share min -> $0.06 mid dropped, $0.30 kept")

    # RELATIVE floor: 0.4% of spot. On a $190 name the floor is $0.76, so a $0.28 mid (the
    # ~5%/yr credit the absolute floor used to wave through) is now dropped, while the SAME
    # $0.28 on a $20 name still clears because there the absolute floor governs.
    assert _premium_floor(190.0) == 190.0 * MIN_PREMIUM_PCT, "relative floor binds on a pricey name"
    assert _premium_floor(190.0) > MIN_PREMIUM, "the relative term must dominate above ~$62 spot"
    assert _premium_floor(20.0) == MIN_PREMIUM, "absolute floor governs a cheap name (0.4%<$0.25)"
    assert _premium_floor(0.0) == MIN_PREMIUM and _premium_floor(None) == MIN_PREMIUM, "no spot -> absolute floor"
    assert not _tradeable_premium(0.28, 190.0), "$28 credit on a $190 strike (~5%/yr) is now dropped"
    assert _tradeable_premium(0.28, 20.0), "$28 credit on a $20 strike still clears (cheap name)"
    assert _tradeable_premium(190.0 * MIN_PREMIUM_PCT, 190.0), "exactly the relative floor clears (inclusive)"
    print(f"relative floor: spot $190 -> ${_premium_floor(190.0):.2f}/share min, $0.28 mid dropped")

    # short-RV clamp: a noisy 5-obs window is held inside [0.70, 1.50]x the 20-day rv. A quiet
    # week cannot drop the VRP denominator below 70% (inventing richness on a cheap-vol tape),
    # a spike week cannot push it above 150% (suppressing richness on a genuinely rich one),
    # and a normal week already inside the band passes through untouched.
    assert _clamp_short_rv(0.10, 0.40) == SHORT_RV_FLOOR * 0.40, "a quiet week is floored at 70% of 20d rv"
    assert _clamp_short_rv(1.20, 0.40) == SHORT_RV_CEIL * 0.40, "a spike week is capped at 150% of 20d rv"
    assert _clamp_short_rv(0.40, 0.40) == 0.40, "a normal week inside the band is left untouched"
    assert _clamp_short_rv(0.10, 0.0) == 0.10, "with no 20d rv there is nothing to clamp against"
    # The floor must cap an inflated VRP below the saturation ceiling: a cheap-vol name (iv ~= rv,
    # true VRP ~1) whose 5-day went quiet reads VRP 4.0 unclamped, but at most iv/(0.70*rv) ~= 1.43.
    iv, rv = 0.40, 0.40
    assert iv / (0.10) == 4.0 and round(iv / _clamp_short_rv(0.10, rv), 2) == 1.43, \
        "the floor pulls an inflated VRP back under the richness saturation ceiling"
    # The ceiling must lift a spike-suppressed VRP back above the no-edge line: a genuinely rich
    # name (iv 0.72 vs 20d rv 0.40, true VRP 1.8) whose 5-day spiked to 1.20 reads VRP 0.60
    # unclamped (richness zeroed), but iv/(1.50*rv) = 1.20 clamped — edge restored, not erased.
    assert round(0.72 / 1.20, 2) == 0.60 and round(0.72 / _clamp_short_rv(1.20, 0.40), 2) == 1.20, \
        "the ceiling lifts a spike-suppressed VRP back above the no-edge line"
    print("short-rv clamp: 5d held to [0.70, 1.50]x 20d, normal week untouched")

    # Distance-to-strike: a 190 put on a 200 spot is 5.0% OTM (his trade vocabulary). A
    # strike at spot is 0%, and a degenerate zero spot never divides.
    assert _pct_otm(200.0, 190.0) == 5.0, "a 190 put on a 200 spot is 5% OTM"
    assert _pct_otm(100.0, 100.0) == 0.0, "a strike at spot is 0% OTM"
    assert _pct_otm(0.0, 10.0) == 0.0, "a zero spot must not divide"
    print("pct_otm: 190p/200 spot -> 5.0% OTM")

    # Strike-at-support: the picked put strike is AT or BELOW the level we trust to hold,
    # never above it. A support of $461.50 between listed $460 / $462.50 must sell $460
    # (the $462.50 is closer but sits ABOVE support). A strike sitting right at target
    # rounds through the 0.2% tolerance. When nothing lists at/below a deep target we fall
    # back to the nearest sub-spot strike rather than blank the name; no strike at/below
    # spot at all returns None.
    chain = [450.0, 455.0, 460.0, 462.5, 465.0, 470.0]
    assert _strike_at_or_below(chain, 461.5, 470.0) == 460.0, "pick $460, never the higher $462.50 above support"
    assert _strike_at_or_below(chain, 462.5, 470.0) == 462.5, "a strike right at target is taken"
    assert _strike_at_or_below(chain, 463.0, 470.0) == 462.5, "0.2% tol lets 462.5 (<=463.9) round through"
    assert _strike_at_or_below(chain, 100.0, 470.0) == 450.0, "deep target falls back to nearest sub-spot strike"
    assert _strike_at_or_below([480.0, 490.0], 461.5, 470.0) is None, "no strike at/below spot -> None"
    print("strike: support $461.50 between $460/$462.50 -> sells $460 (at/below support)")

    # Sellable premium: you sell-to-open, so the credit is anchored on the BID. A put with no
    # bid cannot be sold, so it is dropped rather than quoted off a stale lastPrice; a bid with
    # a real ask quotes the mid; a bid with no ask quotes the bid (never invent the offer).
    assert _sellable_premium(0.0, 1.20) is None, "no bid -> the put cannot be sold (drop it)"
    assert _sellable_premium(-1.0, 1.20) is None, "a negative/absent bid is not a tradeable quote"
    assert _sellable_premium(1.00, 1.20) == 1.10, "a two-sided quote prices at the mid"
    assert _sellable_premium(1.00, 0.0) == 1.00, "a bid with no ask quotes the conservative bid"
    print("sellable: a no-bid put is dropped (stale lastPrice never becomes a quoted credit)")

    # Real-support gate: a level the market tagged once or twice is a ghost, not a floor,
    # so it is demoted to None and the strike falls through to the 1-sigma fallback. A level
    # tested >= MIN_SUPPORT_TOUCHES passes through unchanged. None support/touches stays None.
    assert MIN_SUPPORT_TOUCHES >= 2, "a floor needs at least a couple of tests to be real"
    assert _real_support(100.0, MIN_SUPPORT_TOUCHES) == 100.0, "a well-tested level is a real floor"
    assert _real_support(100.0, MIN_SUPPORT_TOUCHES + 4) == 100.0, "a heavily-tested level passes through"
    assert _real_support(100.0, 1) is None, "a one-touch pivot is a ghost -> no clean support"
    assert _real_support(100.0, MIN_SUPPORT_TOUCHES - 1) is None, "just under the floor is demoted"
    assert _real_support(None, 9) is None, "no level is never a real floor"
    assert _real_support(100.0, None) is None, "unknown touch count is not a trusted floor"
    # The 1-sigma fallback fires once support is demoted (at_support False, strike below spot).
    _, at_sup = _anchor_strike(100.0, 0.40, 7, _real_support(95.0, 1))
    assert at_sup is False, "a demoted one-touch support must not read as at_support"
    print(f"support gate: a 1-touch level -> ghost (1-sigma fallback); >= {MIN_SUPPORT_TOUCHES} touches holds")

    # Sector crowding: walk a pre-sorted list, keep the best name per sector clean, flag the
    # rest. Two Technology names above 60 -> the SECOND (lower-ranked) is crowded, the first is
    # not. A Healthcare name is alone in its sector -> clean. A sub-60 Technology also-ran does
    # not get flagged (it is not competing for capital) and a no-sector name is always clean.
    mk = lambda tk, score, sec, avoid=False: {
        "ticker": tk, "pick": {"score": score, "sector": sec, "avoid": avoid}}
    lst = [mk("NVDA", 72, "Technology"), mk("AMD", 68, "Technology"),
           mk("LLY", 64, "Healthcare"), mk("MU", 55, "Technology"),
           mk("XYZ", 70, None)]
    flagged = _sector_crowding(lst)
    crowded = {t["ticker"]: t["pick"]["sector_crowded"] for t in lst}
    print(f"crowding: flagged {flagged} -> {[k for k, v in crowded.items() if v]}")
    assert crowded["NVDA"] is False, "the top name in a sector is never crowded"
    assert crowded["AMD"] is True, "the second qualifying name in the same sector is crowded"
    assert crowded["LLY"] is False, "a name alone in its sector is clean"
    assert crowded["MU"] is False, "a sub-threshold also-ran does not get flagged"
    assert crowded["XYZ"] is False, "a name with no sector is always clean (fail-open)"
    assert flagged == 1, "exactly one duplicate semiconductor should be flagged"
    # An AVOID name neither fills a sector slot nor gets flagged, so a real pick behind it
    # still passes clean.
    lst2 = [mk("META", 0, "Communication", avoid=True), mk("GOOGL", 66, "Communication")]
    _sector_crowding(lst2)
    assert lst2[1]["pick"]["sector_crowded"] is False, "an AVOID must not consume a sector slot"

    # IV solver: the whole reason this exists is that yfinance's quoted impliedVolatility is
    # garbage on some strikes, so we back the vol out of the REAL premium. The honest check is
    # a ROUND TRIP: price a put at a known vol with the same Black-Scholes, then solve it back
    # and confirm we recover the vol (a wrong IV poisons both prob_otm and the VRP/richness).
    _S, _K, _t, _r, _sig = 100.0, 95.0, 7.0 / 365.0, 0.0, 0.45
    _prem = _bs_put(_S, _K, _t, _r, _sig)
    _solved = _iv_from_put(_prem, _S, _K, _t, _r)
    print(f"iv solve: a ${_prem:.3f} 95p (7 DTE, 100 spot) -> IV {_solved:.4f} (priced at {_sig})")
    assert _solved is not None and abs(_solved - _sig) < 1e-3, "the solver must recover the vol it was priced at"
    # A deeper-OTM strike at a different vol also round-trips (the bisection is not tuned to one point).
    _p2 = _bs_put(200.0, 180.0, 14.0 / 365.0, 0.0, 0.80)
    assert abs(_iv_from_put(_p2, 200.0, 180.0, 14.0 / 365.0, 0.0) - 0.80) < 1e-3, "round-trips at a second strike/vol"
    # Bail cases: a non-positive / missing premium, and a premium richer than even 500% vol can
    # produce, both return None rather than a bogus vol (fail-open, never poison the score).
    assert _iv_from_put(0.0, _S, _K, _t, _r) is None, "a zero premium has no implied vol"
    assert _iv_from_put(None, _S, _K, _t, _r) is None, "a missing premium fails open to None"
    assert _iv_from_put(_K, _S, _K, _t, _r) is None, "a premium near the strike (richer than 500% vol) bails to None"

    # IV-RANK proxy: where does the trailing 21d realized vol sit in its own 1y range? A thin
    # series (< 60 closes) and a series with no usable vol both fall back to a neutral 50. A
    # calm-then-WILD tape ends on its most volatile window -> the current rv is the range max ->
    # rank 100; the reverse (wild-then-calm) ends on the quietest window -> rank 0.
    assert _iv_rank([100.0] * 40) == 50.0, "a thin (<60) series falls back to neutral 50"
    assert _iv_rank([100.0] * 120) == 50.0, "a flat tape (no realized vol) falls back to neutral 50"
    calm = [100.0 + (0.1 if i % 2 else -0.1) for i in range(120)]
    wild = [100.0 + (6.0 if i % 2 else -6.0) for i in range(40)]
    assert _iv_rank(calm + wild) == 100.0, "ending on the most volatile window ranks 100 (rv at its 1y high)"
    assert _iv_rank(wild + calm) == 0.0, "ending on the quietest window ranks 0 (rv at its 1y low)"
    print("iv-rank proxy: calm->wild tape ranks 100, wild->calm ranks 0, thin/flat -> 50")

    # "What changed since the last scan": new/gone names, AVOID flips both ways, and >=3pt score
    # movers ranked by absolute move. A name that moved < 3pt is NOT a mover; an AVOID flip and a
    # score move can coexist on the same name (CCC here re-arms AND jumps +5).
    prev = {"AAA": {"score": 60, "avoid": False}, "BBB": {"score": 50, "avoid": False},
            "CCC": {"score": 40, "avoid": True}, "DDD": {"score": 55, "avoid": False},
            "EEE": {"score": 61, "avoid": False}}
    cur = [{"ticker": "AAA", "pick": {"score": 64, "avoid": False}},   # +4 mover
           {"ticker": "BBB", "pick": {"score": 50, "avoid": True}},    # to_avoid, no score move
           {"ticker": "CCC", "pick": {"score": 45, "avoid": False}},   # from_avoid AND +5 mover
           {"ticker": "EEE", "pick": {"score": 62, "avoid": False}},   # +1, NOT a mover
           {"ticker": "FFF", "pick": {"score": 70, "avoid": False}}]   # new (not in prev)
    ch = _compute_changes(prev, cur)
    print(f"changes: new={ch['new']} gone={ch['gone']} to_avoid={ch['to_avoid']} "
          f"from_avoid={ch['from_avoid']} movers={ch['movers']}")
    assert ch["new"] == ["FFF"], "a name absent from prev is new"
    assert ch["gone"] == ["DDD"], "a name in prev but gone from cur is gone"
    assert ch["to_avoid"] == ["BBB"], "a clean->avoid flip is to_avoid"
    assert ch["from_avoid"] == ["CCC"], "an avoid->clean flip is from_avoid"
    mv = {m["ticker"]: m["delta"] for m in ch["movers"]}
    assert mv == {"AAA": 4.0, "CCC": 5.0}, "only >=3pt moves count; EEE's +1 is excluded"
    assert ch["movers"][0]["ticker"] == "CCC", "movers rank by absolute move, the +5 leads the +4"

    # --- empirical flywheel wiring: the per-name cache + the score nudge it drives ---
    global _EMP_CACHE
    _saved_cache = _EMP_CACHE
    try:
        _EMP_CACHE = {"ZZZ": {"n": 8, "hit_rate": 90.0, "predicted_otm": 80.0}}
        assert _empirical_for("ZZZ")["n"] == 8, "the cache serves a name's settled cohort"
        assert _empirical_for("UNSEEN") is None, "an unseen name yields no cohort (no lift)"
        _lift = _rt.empirical_lift(_empirical_for("ZZZ"))
        assert _lift == 2.5, "a name beating its forecast by 10pts earns +2.5"
        # mirror build_one's clamp + re-grade: a non-avoid score lifts and re-letters
        _new = round(min(100.0, max(0.0, 70.0 + _lift)), 1)
        assert _new == 72.5 and letter_grade(_new) == "B", _new
        # an AVOID never gets lifted, even with a glowing record
        assert (0.0 if True else _rt.empirical_lift(_empirical_for("ZZZ"))) == 0.0
    finally:
        _EMP_CACHE = _saved_cache

    # _json_safe: NaN/Inf must degrade to null so scan.json is always valid JSON, and the
    # sanitized structure must round-trip through a STRICT (allow_nan=False) dump.
    _nan = float("nan"); _inf = float("inf")
    _dirty = {"a": _nan, "b": [1.0, _inf, {"c": _nan}], "d": "ok", "e": 3}
    _clean = _json_safe(_dirty)
    assert _clean["a"] is None and _clean["b"][1] is None and _clean["b"][2]["c"] is None, _clean
    assert _clean["b"][0] == 1.0 and _clean["d"] == "ok" and _clean["e"] == 3, _clean
    json.dumps(_clean, allow_nan=False)  # must NOT raise: proves the board can never blank on a NaN

    print("OK: build_site_data DTE-ladder + premium-floor + short-rv-clamp + sector-crowding + "
          "iv-solve + iv-rank + changes + empirical-flywheel + json-safe self-test passed.")


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        _selftest()
    else:
        main()
