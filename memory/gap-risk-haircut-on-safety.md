---
name: gap-risk-haircut-on-safety
description: c67 — prob_otm is thin-tailed and blind to jump risk; a gap-risk haircut docks the chronic overnight gapper's safety at the same distance.
metadata:
  type: project
---

c67: ported StrikeForge's tail/gap risk as a haircut on the SAFETY factor. `prob_otm` is a
lognormal "stays-OTM" estimate with thin tails, so two CSPs at the same distance can read
equally safe while one drifts and the other gaps 12% overnight on a guide-down and blows
clean through the strike before you can react.

**Why:** safety was a single number (`safety_score(prob_otm)`) that the smooth model flatters
on exactly the names that jump. A disciplined seller should treat the chronic gapper as LESS
safe at the same prob_otm.

**How to apply:** `wheelforge/tail_risk.py::gap_risk(candles)` reads the worst recent DOWNSIDE
overnight gaps (open vs prior close, past a 1% noise floor, worst-3 averaged) off the OHLCV I
already pull -> 0..1. `scoring.gap_haircut` turns it into a bounded multiplier (up to -35%) on
the prob_otm safety; `safety_score(prob_otm, gap_risk)` applies it. Downside only (an upside gap
is a gift to a put seller). Fail-open: missing/short/clean data -> 0.0 -> no haircut, never a
silent penalty. Surfaced as `pick.gap_risk` in scan.json and a "watch overnight gap risk" note
in the why when >=0.5. Phase-4 StrikeForge ports still open: put skew, OI walls, regime banner.
See [[strikeforge-intelligence]], [[clamp-noise-both-tails]].
