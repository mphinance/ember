---
name: prime-picks-multi-pillar-gate
description: c75 a "standouts"/best-of highlight must gate on ALL thesis pillars at once, not top-N-by-score, and use a relative-friendly floor so it never renders empty
metadata:
  type: project
---

c75 shipped the "Prime Picks" standouts strip (GOAL Phase-3 page-UX). The design call:
a best-of highlight earns its keep only if it is a MULTI-PILLAR AND gate, not a top-N cut.

**Why:** top-N-by-score just re-shows the top of the list (the TOP badge already does that),
and a pure yield/safety floor surfaces high-IV junk the score already marked down (RGTI/AAOI
clear 80% OTM + 60% yield but are grade D speculative names). Prime = clears quality
(score>=50, grade C+), yield (>=25% ann), AND discipline (>=75% OTM) at once. On live data
that correctly DROPS the top-score name with a thin 19% yield (NVDA: safe, not a premium
standout) and keeps IREN/SMCI/INTC/PLTR/MRVL.

**How to apply:** for any "standouts / prime / best-of" surface, gate on every pillar of the
thesis simultaneously and pick a RELATIVE-friendly quality floor (grade C+, not A-only) so the
band still surfaces honest setups on a weak board (today's max score was 61, no A/B grades) and
hides cleanly when nothing qualifies rather than rendering an empty box. Render-only off fields
already in scan.json (score/annualized_roc/prob_otm/avoid); mirror the current filters so the
strip never names a pick the board isn't showing. Same family as [[top-pick-reads-as-headline]]
and [[max-capital-filter-uses-full-strike]] (legible surfaces off existing JSON, no engine touch).
