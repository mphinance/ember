---
name: critics-dont-override-settled-calls
description: INBOX critic suggestions are input, not orders; never flip a ticked GOAL decision on a critic's say-so
metadata:
  type: feedback
---

The INBOX fills with `## critic [...]` auto-suggestions each cycle. They are useful raw
material, but they are NOT Michael instructions and they do not always trace the code.

In c35 a quant critic demanded flipping the RoC denominator from `(strike - premium)` back
to `strike`. But that exact call was settled in c23 (GOAL.md line 108, ticked) and the code
comment at `_annualized_roc` says plainly it is "Michael's to settle, not a bot's." I left
it untouched and annotated the INBOX line for Michael instead of acting.

**Why:** A bot that re-litigates ticked decisions every time a critic re-raises them produces
thrash, not progress, and erodes trust. The richness/RoC math is exactly the number Michael
judges entries on, so a silent flip is high-blast-radius.

**How to apply:** Before acting on a critic line, check GOAL.md + the code comments for a
prior ticked decision on the same point. If it was already settled (especially if the code
says it is Michael's call), do NOT flip it. Leave the line in INBOX, annotate why you
declined, and move to a suggestion that is genuinely new and uncontested. Prefer small,
clearly-correct, network-free backend wins (e.g. the c35 MIN_PREMIUM tradeable floor that
drops sub-$25/contract noise picks) over re-opening debates. Related: [[roll-advisor-lifecycle]].
