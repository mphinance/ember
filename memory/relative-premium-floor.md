---
name: relative-premium-floor
description: the tradeable-premium gate scales with spot (max of $0.25 and 0.4% of spot), not a flat dollar floor
metadata:
  type: project
---

WheelForge's premium floor is now per-name, not a flat dollar amount. `_tradeable_premium(mid, spot)`
gates on `_premium_floor(spot) = max(MIN_PREMIUM=$0.25, spot*MIN_PREMIUM_PCT=0.004)` (c52). A flat
$25/contract floor let a $190 AAPL put at $0.28 (~5%/yr on $19k of collateral) onto the list; 0.4%/week
of spot scales the floor with the name so every pick clears a real fraction of the ~100%/yr income
target. Cheap names still fall back to the absolute floor (0.4% of $20 < $0.25), and spot=0/None
(modeled/degraded paths) uses the absolute floor alone, never relaxing below it.

**Why:** a dollar floor is the wrong unit for an income-yield thesis. The number that matters is
premium as a fraction of collateral, which is what annualizes to his target. A fixed floor is loose on
expensive names and the right tightness only by accident.

**How to apply:** when a gate's purpose is a RATE (yield, %/yr), express the floor as a fraction of the
base it scales against, with the absolute floor as a max() backstop for small bases. Same shape as
[[strike-at-or-below-support]] — a pure helper, defaulted so the absolute/degraded path still holds.
Sibling open bullets in the same 06-28 critic block: hi-iv want_to_own flip.
