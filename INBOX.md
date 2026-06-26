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
- The scanner is silent the moment Michael hits "sell." Add `wheelforge/roll_advisor.py` with three states driven by two numbers: BTC_NOW when >50% of entry premium is captured with >50% DTE remaining (standard 50/50 exit), HOLD in the middle, and ROLL_ALERT when spot is within 1 sigma of strike with <7 DTE. Expose it as `python -m wheelforge roll TICKER --strike X --exp DATE --entry PREMIUM --qty N`. This is the single largest gap between a screener and an income machine: the trade lifecycle ends at entry right now.
- The IBKR MCP (`mcp__claude_ai_Interactive_Brokers_IBKR__get_account_positions` + `get_option_data`) is already wired into this session. A `wheelforge/portfolio.py` module that pulls live positions, prices the current option mid against entry, and runs each through `roll_advisor` would give Michael a morning brief: open positions ranked by roll urgency, not just new entry ideas. Zero new API credentials needed.
- In `build_site_data._live_put()`, the scan commits to one expiry (nearest 7 DTE) and never shows whether the 14- or 21-DTE at the same support strike annualizes better. Pull 3 candidate expiries, compute annualized yield for each, surface the winner with a `best_dte` field. Occasionally the bi-weekly puts 2x the premium in Michael's pocket for trivially more risk; right now that comparison is invisible.
