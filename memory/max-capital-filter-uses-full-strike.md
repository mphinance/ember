---
name: max-capital-filter-uses-full-strike
description: c74 max-$ filter sizes by strike*100 (cash collateral), NOT (strike-premium); affordability is unambiguous even though the RoC denominator is a settled judgment call
metadata:
  type: project
---

c74 shipped the GOAL Phase 3 (b) MAX-CAPITAL filter on the frontend (docs/app.js):
client-side "max $" pills (any/5k/10k/25k/50k) that keep only picks whose collateral
fits a per-trade budget. Render-only off the `strike` already in scan.json, fail-open
(a pick with no positive strike can't be sized, so it drops when a cap is active).

**Why:** A cash-secured put ties up the FULL `strike * 100` in cash buying power; the
broker holds that whole amount until expiry. The premium received does not reduce the
cash held. So affordability / max-capital is unambiguously `strike * 100`.

**How to apply:** Do NOT "fix" this filter to use `(strike - premium) * 100` to match
the RoC denominator. They are different questions. The RoC DENOMINATOR is a settled
judgment call Michael owns ((strike - premium), per c23, see
[[critics-dont-override-settled-calls]]); the COLLATERAL / buying-power a trade ties up
is just `strike * 100` and is not contestable. A future critic conflating the two should
be left for Michael, not acted on.

Same discipline as the rest of the frontend filter family: render-only off existing
scan.json fields is the cheapest on-thesis win (no engine touch, no scan.json, backward
compatible since the page guards on the field). Verified headless via a hand-rolled Node
DOM stub (no jsdom/chromium on the box), same pattern as c64/c69/c71.
