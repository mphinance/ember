# reference: CSP intelligence from Michael's proven screeners (VoPR + TraderDaddy)

Michael asked me to learn from his existing cash-secured-put screeners after a code
review found WheelForge has DEAD factors. These are READ-ONLY scripture (charter rule 2):
PORT the approach into my own clean modules, do not copy wholesale. Paths under
`C:\Users\mphan\OneDrive\Documents\GitHub\`.

The review found two blockers, and his screeners solve both (mostly):

## 1. Real STRUCTURE / trend (fixes my hardcoded trend_align=0.6)
- **VoPR `scanner/technicals.py` + `filters.py`** (production): Keltner Channel = 20-bar SMA
  +/- 3.0 * ATR14 (Wilder). `calculate_price_position()` maps `(spot - KC_lower)/KC_width`
  to a 0..1 score. That score IS my missing `trend_align`. VoPR even derives dynamic delta
  bounds from it: `put_skew = 0.10 + 0.15 * score`. Strike must sit below BOTH KC_lower AND
  the EM (1 sigma) floor.
- **TraderDaddy `CSPScreener.ts` + `bounce_finder.py`**: ADX < 35, RSI 30-70 pre-filter; a
  9-component composite (KC/RSI/StochRSI/BB%B/MACD/volume/W%R/CCI/divergence) fires the
  csp_trigger. Heavier than I need; the VoPR Keltner score is the clean port.
- **PORT FIRST:** VoPR's `calculate_price_position()` Keltner score -> a real
  `structure`/`trend_align` per name (I already pull OHLCV). Replaces the constant. Below
  KC_lower or in a downtrend should LOWER the structure score (do not sell into a knife).

## 2. RICHNESS: composite realized vol + true VRP (upgrades my single-RV proxy)
- **VoPR `scanner/volatility_models.py`** (the crown jewel): `composite_realized_vol()`
  blends Close-to-Close 15%, Parkinson 25%, Garman-Klass 25%, Rogers-Satchell 35%.
  `calculate_vrp_ratio()` = atm_iv / composite_RV, flags HIGH VRP EDGE at >= 1.25.
  `classify_regime()` = low/expanding/high/compressing.
- **VoPR `scanner/surface.py`**: per-side IV percentile within the chain, skew slope
  (25d put IV - 25d call IV), surface distortion score.
- **PORT:** the 4-estimator composite RV (I use only close-to-close). My richness already
  does iv/rv; a better RV denominator makes the VRP honest. The surface/skew is a later add.

## 3. "Would you want to own it" (blocker #2) — OPEN in his stack too
- Neither VoPR nor TraderDaddy actually GATES on quality. TraderDaddy fetches sector /
  marketCap / divYield / ROE / ownership but only displays them.
- So this is mine to invent honestly. Cheapest real version: a market-cap / liquidity
  quality proxy from the TradingView screener (I already query it), OR drop the
  hardcoded want_to_own=True and default it from the lane (liquid lane = ownable staples
  True; high-IV lane = speculative, default False or a user toggle). Do NOT keep it True
  for everyone, that is the dead-factor bug.

## 4. Strike selection + structural bonuses (later)
- VoPR: strike below KC_lower AND EM_lower, delta [0.10, put_skew], DTE 21-50.
- TraderDaddy: targetStrike = price*(1 - otm_pct), evaluate all expiries, max-pain +
  put-wall structural bonus. Worth a small structure bonus later.

## 5. Earnings — already covered
TraderDaddy hard-excludes earnings within 14d from a local DB. I already approximate this
with the TradingView earnings field + a hard veto (cycle 8). Good enough.

## Honesty note
VoPR has NO earnings logic and NO quality gate; TraderDaddy has both but a coarser VRP. I
am combining the best of each: VoPR's vol/structure math + TraderDaddy's earnings/quality
instincts. Port the math, keep it mine, stay on-thesis.

## The LIVE TraderDaddy CSP-wheel PAGE — UX to borrow (Michael pointed me here)
His shipped page `traderdaddy.pro/screeners/csp-wheel` already solves UX things WheelForge is
missing. Code: `TraderDaddy-Pro---Whop/.../frontend/app/screeners/[id]/page.tsx` +
`components/screeners/DailyCutsView.tsx` (+ wheel/ components). Borrow:
- **Letter GRADE (A-F) per pick** on top of the 0-100 score. Reads instantly; "63.5" does not.
  Map my score bands -> a grade and lead with it. (Answers "the scoring is not clear".)
- **supportFloor per pick** — he shows the OI-based support level for every name. This is the
  "sell near support" idea, already built. Pairs with my Keltner + the Phase-4 OI walls.
- **Configurable param FILTERS** (number/range/select with defaults), not just a sort + a
  min-score toggle. This is how he filters e.g. "min annualized" -> enables the yield mode.
- **"Prime Picks"** — a highlighted best-of subset above the full list (a "today's standouts").
- (Beyond my scope, his wheel/ system: assignment + buyback tracking + a CC strike picker.
  The CcStrikePicker is worth a look when I build covered-call mode.)
