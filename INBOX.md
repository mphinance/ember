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
- [DONE c31] roll_advisor.py shipped — three states (BTC_NOW / HOLD / ROLL_ALERT) driven by captured premium + sigma-to-strike, exposed as `python -m wheelforge roll TICKER --strike X --exp DATE --entry P --qty N`. The trade lifecycle no longer ends at entry.
- The IBKR MCP (`mcp__claude_ai_Interactive_Brokers_IBKR__get_account_positions` + `get_option_data`) is already wired into this session. A `wheelforge/portfolio.py` module that pulls live positions, prices the current option mid against entry, and runs each through `roll_advisor` would give Michael a morning brief: open positions ranked by roll urgency, not just new entry ideas. Zero new API credentials needed.
- In `build_site_data._live_put()`, the scan commits to one expiry (nearest 7 DTE) and never shows whether the 14- or 21-DTE at the same support strike annualizes better. Pull 3 candidate expiries, compute annualized yield for each, surface the winner with a `best_dte` field. Occasionally the bi-weekly puts 2x the premium in Michael's pocket for trivially more risk; right now that comparison is invisible.

## critic [quant] · claude-sonnet-4-6 (local) — 2026-06-26 04:47Z
- `build_site_data.py:267` — `cap = strike - premium` overstates RoC. A cash-secured put requires the full strike price in cash (the broker holds `strike × 100`); the received premium does not reduce your collateral requirement. The honest denominator is `strike`, not `strike - premium`. On a $2 premium against a $195 strike the error is ~1%, but it systematically inflates every quoted yield and misleads Michael on exactly the number he uses to judge entries.
- `build_site_data.py:242` — the modeled-fallback path hard-codes `iv = rv * 1.15`, which fixes VRP at exactly 1.15× on every name that fails to return a live chain. In `richness_score`, 1.15× maps to `vrp_s = _ramp(1.15, 1.0, 1.6) = 0.25`, always. A cheap, dead name and a genuinely rich one score identically when the chain is unavailable. At minimum add a `"vrp_assumed": True` flag so the UI can visually dim or badge those picks rather than presenting an invented richness number as real.

## critic [growth] · claude-sonnet-4-6 (local) — 2026-06-26 07:46Z
- `roll_advisor.py` fires ROLL_ALERT and says "roll down-and-out for a credit" but stops there. The immediate next question is: to which strike, at which expiry, for what net credit? Add a `roll_target(ticker, current_strike, current_mid, spot, iv, qty)` function that queries `yf.Ticker(ticker).option_chain(new_exp)` at `dte_total + 14` DTE, finds the strike nearest 1-sigma below current spot, and returns `{new_strike, new_exp, new_premium, net_credit, net_credit_dollars}`. Expose it in the `roll` CLI subcommand so ROLL_ALERT prints a specific trade instruction rather than generic advice. The diagnostic is done; the prescription is not.
- The scanner has no concept of capital concentration. Michael can have NVDA, AMD, and TSLA all flagged BUY the same morning, sell puts on all three simultaneously, and WheelForge never notices the correlated semiconductor exposure. Add a `correlation_penalty` pass in `build_site_data.build_one()` (or a post-sort step in `__main__.py scan`) that groups picks by GICS sector and discounts rank when more than one name in the same sector already scores above 60. One field, one config constant (`MAX_SECTOR_OVERLAP = 1`), no new data source needed.
