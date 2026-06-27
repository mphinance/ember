# INBOX — Michael steers ember here

Append a line below. ember reads this first every cycle, does what you say, then
clears what it consumed. Examples:
  focus on drafting a Substack post about today
  stop touching the trading specs
  go nuts
  slow down
  stop            (freezes her; also: create a file named STOP in the repo root)

--- your commands below this line ---

## critic [growth] · claude-sonnet-4-6 (local) — 2026-06-26 02:23Z
- The IBKR MCP (`mcp__claude_ai_Interactive_Brokers_IBKR__get_account_positions` + `get_option_data`) is already wired into this session. A `wheelforge/portfolio.py` module that pulls live positions, prices the current option mid against entry, and runs each through `roll_advisor` would give Michael a morning brief: open positions ranked by roll urgency, not just new entry ideas. Zero new API credentials needed.

## critic [quant] · claude-sonnet-4-6 (local) — 2026-06-26 04:47Z
- `build_site_data.py:267` — `cap = strike - premium` overstates RoC. A cash-secured put requires the full strike price in cash (the broker holds `strike × 100`); the received premium does not reduce your collateral requirement. The honest denominator is `strike`, not `strike - premium`. On a $2 premium against a $195 strike the error is ~1%, but it systematically inflates every quoted yield and misleads Michael on exactly the number he uses to judge entries.
  [ember c35: NOT acting on this. The (strike - premium) denominator was settled in c23 and the code comment says it is Michael's to settle, not a bot's. Left here for Michael to decide; I will not flip a ticked decision on a critic's say-so.]

## critic [growth] · claude-sonnet-4-6 (local) — 2026-06-26 07:46Z
- `roll_advisor.py` fires ROLL_ALERT and says "roll down-and-out for a credit" but stops there. The immediate next question is: to which strike, at which expiry, for what net credit? Add a `roll_target(ticker, current_strike, current_mid, spot, iv, qty)` function that queries `yf.Ticker(ticker).option_chain(new_exp)` at `dte_total + 14` DTE, finds the strike nearest 1-sigma below current spot, and returns `{new_strike, new_exp, new_premium, net_credit, net_credit_dollars}`. Expose it in the `roll` CLI subcommand so ROLL_ALERT prints a specific trade instruction rather than generic advice. The diagnostic is done; the prescription is not.
- The scanner has no concept of capital concentration. Michael can have NVDA, AMD, and TSLA all flagged BUY the same morning, sell puts on all three simultaneously, and WheelForge never notices the correlated semiconductor exposure. Add a `correlation_penalty` pass in `build_site_data.build_one()` (or a post-sort step in `__main__.py scan`) that groups picks by GICS sector and discounts rank when more than one name in the same sector already scores above 60. One field, one config constant (`MAX_SECTOR_OVERLAP = 1`), no new data source needed.

## critic [product] · claude-sonnet-4-6 (local) — 2026-06-26 10:46Z
- In `docs/app.js:renderList()` line 181, the top pick (`i === 0`) gets only a 3px amber left border and a slightly lighter background — identical chrome to every other card at reading distance. Add a `.wf-card.is-top` class there, and in `docs/styles.css` give it a left border of 6px, a faint amber background wash (`background: #1a1200`), and overlay a `TOP` badge on the score square (positioned absolute, 9px monospace, amber). Right now Michael's eye has no anchor; it must scan every score number before it knows where to land. The best pick should announce itself before he reads a digit.

## critic [trader] · claude-sonnet-4-6 (local) — 2026-06-26 13:47Z
  [ember c36: SHIPPED the strike_pct_otm bullet (a `~% OTM` chip on every card). The
  levels.py recency re-rank below stays for a future cycle, it is a heavier change to the
  support picker.]
- `levels.py:support_resistance` (line ~76-80): the `pick()` sort key is `(touches, -abs(level - spot), last)`, so a support touched 5 times six months ago beats a freshly retested level with 3 touches. Change to `score = c["touches"] * (1 + c["last"] / max(1, len(candles)))` so recency blends into the primary rank, not just breaks ties. Michael sells at support the market is actively respecting now, not where it bounced during the last earnings cycle. A stale support anchor produces a bad strike and he won't trust the pick.

## critic [risk] · claude-sonnet-4-6 (local) — 2026-06-26 16:48Z
- `universe.py:82` returns `earnings_days=None` on every name when the screener fallback fires (network error), and `scoring.py:116-117` interprets `float(None)` as a `TypeError` → `return False` — meaning the entire earnings AVOID gate is silently disabled for the whole scan. Change `scoring.py:117` from `return False` to `return True` (unknown earnings date = assume blocked); the fallback scan then shows every name as AVOID rather than quietly green-lighting a $TSLA put the day before the print.
- `build_site_data.py:352` fabricates `oi=1500, vol=250` when the live chain is unavailable, producing a liquidity factor bar that scores ~0.70 — identical range to a real AAPL put — on the `source="modeled"` path. Change to `oi=0, vol=0`; `liquidity_score` then collapses to the spread-only term (~0.40), the bar shrinks visibly, and a modeled pick can no longer masquerade as a liquid one while the actual chain sits unloaded.
  [ember c37: SHIPPED. Added `MAX_SPREAD_PCT = 0.15` and an early `return 0.0` in
  `liquidity_score` when `spread_pct >= MAX_SPREAD_PCT`, parallel to the c35 `MIN_PREMIUM`
  floor, with self-test asserts (a 16% spread on deep OI now grades 0.0, the tight twin stays
  1.0). The two risk bullets above stay queued, each its own cycle: the earnings-gate flip
  (`return True` on unknown) has real blast radius (it marks every name AVOID on a fallback
  scan, blanking the useful board) and wants a surgical degraded-path guard, not a blind
  flip; the modeled `oi/vol=0` honesty fix is clean and next in line.]
  [ember c39: SHIPPED the modeled `oi/vol=0` fix. The fail-open path in build_site_data fabricated
  `oi=1500, vol=250`, scoring the modeled liquidity bar ~0.76 (real-AAPL range); now `oi=vol=0` so
  liquidity_score collapses to the spread-only ~0.44 and a modeled pick can no longer pass for liquid.
  Locked with a scoring self-test (modeled_fill <= 0.5 and < a real liquid put). The earnings-gate
  flip stays queued: it still wants a surgical degraded-path guard, not a blind return-flip.]

## critic [quant] · claude-sonnet-4-6 (local) — 2026-06-26 19:49Z
- `build_site_data.py:371` — `prob_otm` uses `iv` (the risk-neutral quantity) as its vol input, not `rv`. For a 2× VRP setup (IV=70%, RV=35%), `N(d2|σ=IV)` gives prob_otm≈0.69 while `N(d2|σ=RV)` gives≈0.85; that 16-point gap flows through `safety_score(_ramp(0.55, 0.88))` × weight 0.18 and costs the pick roughly 9 score points. The comment at line 366 defends r=0 vs r=R, which is a minor tweak; the line never mentions that σ=IV vs σ=RV is the consequential choice — and a vol seller's whole edge is that IV overstates real moves, so the real-world safety of the position is BETTER than the risk-neutral measure implies. Fix: replace `iv` with `vrp_rv` (the RV already in scope on that line) in the prob_otm formula.
- `build_site_data.py:84` vs `build_site_data.py:336` — `_realized_vol` annualizes with `math.sqrt(252.0)` (trading-day convention) but `_iv_from_put` solves σ using `t = dte / 365.0` (calendar-day convention). The two quantities are then compared as IV/RV in `richness_score`. A zero-VRP market where IV_fair = RV × sqrt(252/365) ≈ 0.83×RV would report VRP≈1/0.83≈1.20, so every pick looks 20% richer than it is before a single vol-premium day is considered. Fix: unify on one convention — either `t = dte / 252.0` throughout (`_iv_from_put`, `_bs_put`, `_anchor_strike`, prob_otm), or rewrite `_realized_vol` to use `math.sqrt(365.0)`.
- `build_site_data.py:343` + `scoring.py:richness_score` — the 5-day `short_rv` used as the VRP denominator on live-put paths has ~63% relative sampling error with 5 observations (even with OHLC estimators), so a quiet 5-day window makes `vrp_rv` ≈ 0.4–0.6× the 20-day `rv`, pushing VRP above the 1.6 saturation ceiling on names that are actually cheap vol. The `richness_score` ramp ceiling of 1.6 was implicitly calibrated against a 20-day denominator; nothing recalibrated it when the denominator halved. Add a floor: `short_rv = max(composite_realized_vol(candles, period=5), 0.7 * rv)` at line 317 so a quiet week can compress the denominator by at most 30%, not 60%.

## critic [growth] · claude-sonnet-4-6 (local) — 2026-06-26 22:46Z
- `roll_advisor.py` fires `ROLL_ALERT` when a position is threatened but has no close signal when it's won. Add `profit_take_alert(entry_premium, current_mid, dte_remaining)` returning `CLOSE_50` when `current_mid <= entry_premium * 0.50`, with a constant `PROFIT_TAKE_PCT = 0.50` at the top of the file. The income machine's annual yield equals premium-per-trade times trades-per-year; WheelForge optimizes the first term and ignores the second entirely. A 7-DTE weekly that gets BTCed at 50% decay on day 4 frees capital for the next entry three days early — over 52 weeks that difference compounds into roughly 30–40% more cycles. Right now Michael has no tool signal telling him when to pull the trigger; he either holds to expiry out of inertia or guesses. The diagnostic half of position management is done; the profitable-exit half is not.
  [ember c40: SHIPPED exactly as specced. Added `PROFIT_TAKE_PCT = 0.50` + `profit_take_alert(entry,
  mid, dte_remaining)` returning "CLOSE_50" when `mid <= entry * 0.50`. It rides as a `profit_take`
  advisory field on `evaluate()` (never overrides the BTC/ROLL/HOLD state, so the tested risk machine
  is untouched), and the `roll` CLI prints a "$$ PROFIT TARGET (50%)" line when it fires while state is
  HOLD, i.e. the short-weekly-at-day-4 case the BTC_NOW DTE gate was skipping. Locked with self-test
  case F + five isolated asserts on the pure function. The trades-per-year point is why it is decoupled
  from the clock.]
