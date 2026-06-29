---
name: put-skew-lifts-richness
description: c68 put skew (OTM vs ATM put IV) lifts the richness factor as a bounded, fail-open additive credit, not a reweight
metadata:
  type: project
---

c68: shipped the first PUT SKEW read (Phase 4 StrikeForge surface.py port + the freshest
trader critic, 06-29 10:47Z). New pure `wheelforge/surface.py::put_skew(otm_iv, atm_iv)` =
`(otm_iv - atm_iv) / atm_iv`: positive means OTM puts are bid up vs ATM, i.e. downside fear
priced into the very strike a CSP seller collects on, which is his edge. Returns None on any
missing/non-positive IV (fail-open).

**Why the design differs from the critic's spec:** the critic (and the roadmap line) said
"fold skew into richness at the expense of VRP" (drop VRP weight 0.6->0.5, add skew 0.15). A
reweight silently re-ranks the WHOLE board, including every name with no skew read (modeled
path, flat tape, degraded chain). Instead I made it a bounded ADDITIVE lift: `richness_score`
gained `put_skew=0.0`, `skew_lift()` adds up to `SKEW_LIFT_MAX=0.12` for a +25% skew, and a
0/None/negative skew adds nothing. So the base VRP+rank blend is untouched and only a
measurably skewed put earns extra credit. Same discipline as c61/c63: credit a real signal,
never silently rescore the board. The roadmap DID sanction "lift richness," so folding in is
fine; the reweight was the part to avoid.

**How to apply:** chain read (`_atm_put_iv` = IV of the put nearest spot) lives in
build_site_data (network layer); the math stays pure in surface.py, mirroring levels/structure.
put_skew rides the live quote dict -> contract -> `pick.put_skew` (None on modeled). The why
says "puts richly skewed" at >= 0.10. Note: this sandbox has no live option chain (yfinance
chains unreachable), so every name fell to the modeled path with put_skew=None during the
cycle; the lift is unit-tested (surface + scoring + a stub-frame `_atm_put_iv` test) and the
box computes real skews on its live refresh. See [[critics-dont-override-settled-calls]],
[[gap-risk-haircut-on-safety]].
