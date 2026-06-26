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
