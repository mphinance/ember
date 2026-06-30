---
name: basis-discount-on-card-face
description: c79 — surface the free-shares basis discount on the card face, but gate it on want_to_own so a number never lies about which lane it serves
metadata:
  type: project
---

c79: the "love assignment when the basis is right" call is made in two seconds on the card face,
not behind the expand. Surfaced `free_shares.basis_discount_pct` (in scan.json since c11) as a cyan
`↓ own N% below` chip on the sub-line.

**Why:** the free-shares endgame is the thesis (GOAL definition-of-best #5), and the effective
basis vs spot is the literal payoff if assigned. Showing it only inside the expand buried the one
sentence that turns a good score into a trade he sizes up.

**How to apply:** when you put a free-shares / assignment number on the most-glanceable surface,
GATE it on `want_to_own` (and a positive value). On a high-IV name he sold purely for premium
(`want_to_own=False`, c54), assignment is the RISK, not the reward, so a "own X% below" chip there
would pitch a downside as an upside. The lane already decides what a number MEANS; the display must
respect that, the same way `freeshares._summary` flips to "Income play, not free shares" for an
unwanted name. A field that ranks/reports correctly can still LIE if shown without its lane context.

The cousin rule to [[show-the-value-not-the-flag]] (surface the value, not just a presence flag) and
[[weekly-yield-is-his-screen]] (put the decision unit on the card): here the extra discipline is that
the value is only honest in one lane. Render-only, fields already baked, so it lit up 7 live names
with no scan.json rebuild.
