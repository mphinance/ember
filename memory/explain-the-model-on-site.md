---
name: explain-the-model-on-site
description: the page must say what its numbers MEAN, not just show them; factor tooltips (c58) + "how scoring works" panel (c69) + per-card why line (c70) — EXPLAIN item DONE
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
(2) a short "how scoring works" blurb [DONE c69], (3) a one-line "why this score" per pick
(the `summary`/free-shares line already half covers this) [still OPEN]. c69 shipped (2): a
collapsed `<details id="wf-how">` panel (`renderHowItWorks()` in docs/app.js, called once in
boot) that says the score is a 0-100 blend of six factors, earnings before expiry is a hard
AVOID veto (not a factor), the A/B/C/D/F grade bands, and the two lanes. KEY discipline: it
renders the factor list from the SAME `FAC_HELP` map the per-bar tooltips use (via a
`stripLead()` helper), so the explainer and the tooltips can never drift out of sync — one
source of truth for "what a factor means." Render-only, no scan.json; verified with a Node
DOM stub (no chromium on the box).

c70 shipped (3) and CLOSES the EXPLAIN item: the plain-English `p.why` ("rich premium, safe
distance, fat annualized yield, ...") now rides each card as a muted italic `.wf-why` caption
under the trade line, not just in the readout you have to click into. Non-avoid only (an AVOID
card already leads with its veto reason). Bound via `textContent`, never innerHTML, so it is
XSS-safe by construction (see [[escape-data-before-innerhtml]]). The numbers say WHAT; this one
line says WHY, in his terms, on the most-glanceable surface. See [[support-touch-count]] and
[[top-pick-reads-as-headline]].
