---
name: clamp-noise-both-tails
description: c63 — a noise clamp on a small-sample estimator must bracket BOTH tails; a one-sided floor still lets the other tail corrupt the signal.
metadata:
  type: feedback
---

When you clamp a noisy small-sample statistic (e.g. the 5-obs `short_rv` VRP denominator),
clamp BOTH tails, not one. c49's `_floor_short_rv` floored only the low tail (a quiet week
inventing richness), but the SAME 5-observation noise spikes UP just as easily: one outlier
session pushed `short_rv` to 2-3x the 20-day rv, dragging VRP below 1.0 and ZEROING the
richness score on a genuinely rich name for days. c63 made it `_clamp_short_rv` →
`[SHORT_RV_FLOOR 0.70, SHORT_RV_CEIL 1.50] x rv`.

**Why:** sampling noise is symmetric by nature; a one-sided clamp leaves the opposite tail
free to corrupt the exact signal the clamp was meant to protect. Here the unprotected tail
hit the richest setups — the names Michael's thesis is built to find.

**How to apply:** whenever you write a floor (or a ceiling) on a noisy ratio, ask "what does
the other tail do to the downstream score?" If the answer is "also corrupts it," bracket
both. Mirror the existing constant + self-test so the symmetry is visible in the code, not
just in your head. Related: [[critics-dont-override-settled-calls]] — this was a critic
finding I DID act on, because it's a genuine bug-fix that restores signal, not a contestable
rescore of a ticked decision.
