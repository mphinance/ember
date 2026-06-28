---
name: explain-the-model-on-site
description: the page must say what its numbers MEAN, not just show them; factor tooltips were the first piece (c58)
metadata:
  type: project
---

WheelForge's page showed six factor bars (rich/safe/yield/shares/liq/struct) and a
0-100 score with NO legend anywhere. A glanceable board that never explains its own
axes is only legible to the person who wrote the engine. c58 added a plain-English
`title` tooltip on each `.fac` (FAC_HELP map in docs/app.js), wording tracked to
GOAL's factor definitions, with this pick's value appended `(NN/100)`.

**Why:** Michael asked to EXPLAIN the model on the site (GOAL Phase 3). The scoring is
the product; a number you cannot interpret you cannot trust or trade off.

**How to apply:** the GOAL bullet bundles three pieces — (1) factor tooltips [DONE c58],
(2) a short "how scoring works" blurb (6 factors blended, earnings = hard veto, lanes),
(3) a one-line "why this score" per pick (the `summary`/free-shares line already half
covers this). Ship 2 and 3 in later cycles. Also added a small `esc()` helper while here
(first step on the open frontend-robustness/esc-pass item) — reuse it for any future
innerHTML/attribute binding. Render-only, no scan.json. See [[support-touch-count]].
