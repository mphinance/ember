---
name: headline-is-a-complete-ticket
description: "c81 — the top-pick headline must carry every number he types into the order (strike, leg, date, PREMIUM, yield), not just rank-and-yield"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 88aa495a-f930-4ff4-ac0f-c2eb03bedd8f
---

c81: the c66 `wf-topline` headline read `SELL $180 PUT · Jul 17 · 19%/yr` but omitted
the dollar premium, the one number Michael actually types into the broker (the cash
collected per contract). Spliced `$1.12` between the date and the yield so it reads as a
COMPLETE trade ticket: `SELL $180 PUT · Jul 17 · $1.12 · 14%/yr`.

**Why:** a "headline" surface earns its pixels only if it lets him act without a click.
The annualized %/yr judges the setup; the per-contract premium is the order itself. A
ticket missing the price is not a ticket. (product critic 06-30 01:48Z.)

**How to apply:** when you put the trade on the most-glanceable surface, include EVERY
field of the order (strike, leg, expiry, premium, yield), each null-guarded so a pre-bake
row drops a segment instead of printing `$-`. Render-only off scan.json; verify headless
that the premium segment lands BEFORE the yield. Cousin of [[top-pick-reads-as-headline]],
[[show-the-value-not-the-flag]], and [[basis-discount-on-card-face]].
