---
name: shade-the-zone-not-just-lines
description: c80 — "shade the put-sell zone" means a FILLED translucent band under the lines, one reusable klinecharts overlay (color via extendData), guarded to a real CSP cushion
metadata:
  type: project
---

c80 shipped Michael's chart-polish ask: SHADE the put-sell zone as a filled band, not just
lines, tinted by score. The put-sell zone = the cushion from spot DOWN to the strike (his
framing: put-sell zone below price, call-sell zone above when CC mode lands).

What the ask actually wanted, and the judgments behind it:
- A FILL, not another `priceLine`. KLineChart v9 has no built-in shaded band, so I
  `registerOverlay('zoneBand')` ONCE (a `polygon` figure spanning `bounding.width` between the
  two point y's) and reuse it for every pick. The per-pick fill color rides in via
  `extendData` so one template serves all scores (and later the call zone) — don't register a
  template per color.
- Sits UNDER the walls/candles: translucent `rgba` (alpha 0.13) via a `hexToRgba(heatColor())`
  helper, so the Keltner walls and S/R lines still read THROUGH it. "Keep the walls" = the
  shaded zone is additive, the lines stay.
- GUARDED: only paint when `spot > strike` (a real CSP cushion). No band on a degenerate/AVOID
  row where the strike sits at/above spot — same flag-don't-lie discipline as the card chips.

Verified headless (playwright, spying createOverlay via a window.klinecharts defineProperty
trap): exactly one zoneBand, values [spot>strike], rgba fill, 0 console errors. Frontend only,
no scan.json. Related: [[escape-data-before-innerhtml]], [[show-the-value-not-the-flag]],
[[basis-discount-on-card-face]].
