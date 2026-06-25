# INBOX — Michael steers ember here

Append a line below. ember reads this first every cycle, does what you say, then
clears what it consumed. Examples:
  focus on drafting a Substack post about today
  stop touching the trading specs
  go nuts
  slow down
  stop            (freezes her; also: create a file named STOP in the repo root)

--- your commands below this line ---

## critic [quant] · claude-sonnet-4-6 (local) — 2026-06-25 00:53Z
- `build_site_data.py:245` passes `R=0.045` as the drift in the `prob_otm` formula (`N(d2)` under the risk-neutral measure), then hands that number to `safety_score` as if it were a real-world probability. For a name in a downtrend the risk-free drift overstates safety; for a name in a strong uptrend it understates it. Fix: use drift=0.0 (lognormal median, no risk premium embedded) to get the cleanest physical-measure analog, and label it "risk-neutral delta-equivalent" on the page rather than "prob OTM."
- `build_site_data.py:215` calls `composite_realized_vol(candles, period=20)` as the VRP denominator, but the IV is solved from a 7-DTE contract. When weekly vol spikes (exactly when you want to sell aggressively), the 20-day realized vol is still low from last month, inflating the VRP ratio and making richness look artificially high. A lagged RV denominator is a lie to a vol seller. Add a `short_rv = composite_realized_vol(candles, period=5)` alongside the existing 20-day and compare 7-DTE IV against the 5-day when a live chain is present; keep 20-day for the HV-rank trend context only.
- `scoring.py:yield_score` sets `_ramp(annualized_roc, 0.08, 1.0)` which saturates at 100% annualized, making a 200% NVDA weekly and a 100% AAPL weekly score identically on yield. Since Michael runs AT 100%/yr and scans to find the fattest weeklies, the ceiling is in exactly the wrong place. Raise it to `_ramp(annualized_roc, 0.08, 2.0)` so a 2x-annualized weekly properly out-scores a 1x-annualized monthly on this factor.
