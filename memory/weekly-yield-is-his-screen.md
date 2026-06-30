---
name: weekly-yield-is-his-screen
description: c77 - show yield PER WEEK on the card (his real pre-order screen), derive it as ann/52 so it never contradicts the headline
metadata:
  type: feedback
---

c77: Michael's mental screen before typing a CSP order is per-WEEK ("did I sell for at
least 1% this week?"), not the annualized math the headline leads with. So the card sub-line
now carries a muted `(N%/wk)` next to the `N% ann` number.

**Why:** the annualized figure is the right ranking unit but the wrong GLANCE unit; making
him divide by 52 in his head is friction on the most-used surface. One field, no new data.

**How to apply:** when a number is the ranking unit but not the decision unit, surface the
decision unit too, DERIVED from the same source so the two can never disagree (`weekly_yield_pct
= round(ann_roc/52, 2)` in build_site_data; `weeklyPct(p)` in app.js prefers the baked field
and falls back to `annualized_roc/52` so the page reads right before the box rebuilds, same
client-fallback discipline as gradeFor c41 and [[show-the-value-not-the-flag]]). Engine + page,
fail-open, no scan.json. See [[empirical-flywheel-feeds-the-score]] for the "ride it auditable,
never silently" rule this also follows.
