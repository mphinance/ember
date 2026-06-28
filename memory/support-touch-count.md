---
name: support-touch-count
description: surface a support level's TEST COUNT (touches) so a real floor is tellable from a stale one-off pivot; expose provenance via a detail sibling, keep the thin projection backward-compatible. c59: ACT on it — gate the strike anchor on MIN_SUPPORT_TOUCHES so a 1-touch ghost falls through to 1-sigma
metadata:
  type: project
---

c56: a support PRICE alone hides its conviction. Michael sells AT support and trusts it to
hold, so he needs to tell a real floor (the market bounced off it 7 times) from a ghost (one
stale pivot). The cluster already counted `touches`; `levels.support_resistance` was throwing
it away at the last step. Now `support_resistance_detail()` returns the chosen cluster
`{level, touches, last}` and `build_one` threads `support_touches` onto the pick; the page floor
badge reads `⌂ support x7` (count in the tooltip too) and the CLI row appends `sup $178x7`.

**Why:** the floor's strength is HOW MANY times price respected it, not just where it sits. A
number he reads before trusting a strike.

**How to apply:** when a critic wants a value's PROVENANCE shown, add a `_detail` SIBLING that
returns the rich object and make the existing bare accessor a thin projection of it
(`support_resistance` now just maps detail -> the float). Every existing caller keeps working,
self-tests stay green, and only the one caller that needs the extra field reaches for detail.
Don't change a widely-used return contract to bolt one field on. Related: [[strike-at-or-below-support]].

c59: showing a number is half the job; the engine should ACT on the same conviction it displays.
c56 let Michael SEE `⌂ support x1`, but `_anchor_strike` still silently routed a real strike (and a
green floor badge) to that one-touch ghost. Added `MIN_SUPPORT_TOUCHES = 3` + a pure `_real_support(
support, touches)` that demotes a level below it to None at the SOURCE in `build_one`, so the strike
falls through to the ~1 sigma OTM fallback and `support_touches`/the badge/the chart floor line all
clear together. A genuinely tested level (>= 3) passes through untouched; None support/touches stays None.

**How to apply:** when you ship a "show the user X so they can judge" feature, ask the very next cycle
whether the ENGINE should gate on X too. A badge that says "weak" while the code still trusts the level
gives false confidence, not less. Gate at the SOURCE (one place, before the value fans out to strike +
display + chart) so every downstream surface agrees, not in each consumer. Pure tested helper, fail-open
(unknown = not trusted).
