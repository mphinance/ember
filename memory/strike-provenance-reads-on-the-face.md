---
name: strike-provenance-reads-on-the-face
description: c84 - a missing badge is not a signal; when most picks ride the 1-sigma fallback, show a muted "1σ strike" chip so the strike's provenance always reads on the card face
metadata:
  type: project
---

c84: the card showed a green `⌂ support $383 x4` badge ONLY when the strike anchored a
tested price-action floor (`at_support` True). On the ~26-of-27 picks where no level
survived the >=3-touch gate, the strike is the ~1-sigma OTM statistical fallback and the
card showed NOTHING. Added a muted `≈ 1σ strike` chip on those (the honest inverse of the
floor badge), so the strike's PROVENANCE — structural level vs probability cushion — always
reads on the card face.

**Why:** a missing badge is not a signal. Michael should never have to INFER from the
absence of a green chip that a strike is a distance computation off realized vol, not a
level the market has defended. His whole thesis is "sell AT support"; making "this one is
NOT at support" visible is the same honesty as the support badge itself.

**How to apply:** when one state of a binary gets a prominent chip and the other (the
common one) gets blank, surface the blank state too — muted, so the strong signal still
leads. Render-only off `at_support` (and AVOID cards never reach the chip block, so it's
auto-gated to real picks). This addressed the trader critic 06-30 19:47Z bullet about
"24 of 26 picks: support null, at_support false with no visible chip" WITHOUT touching the
ranking or default filter (those are Michael's settled calls, see
[[critics-dont-override-settled-calls]]). Mirrors [[show-the-value-not-the-flag]] and
[[support-touch-count]]: tell a real floor from a fallback at a glance.
