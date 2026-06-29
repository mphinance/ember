---
name: top-pick-reads-as-headline
description: the
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b9e51730-3afa-47ef-be35-55ac9922f392
---

c66: gave the `is-top` card a bold amber `wf-topline` that reads `SELL $STRIKE PUT · DATE · ANN%/yr`
in 14px, spanning the grid row under the ticker, so the winning trade reads in one second from arm's
length instead of being buried in the dense 11px sub-line.

**Why:** a string of product critics (c42 TOP badge, c47 grade leads the tile, c49 yield over raw
score, c57 badge floats above the tile, c66 the headline trade) all circle one principle — the most
glanceable pixels must carry the DECISION, not the metadata. A 9px "TOP" chip says *which* card won
but not *what the trade is*; the eye still has to parse the sub-line. The top pick earns one bold
anchor that states strike, expiry, and yield outright.

**How to apply:** when surfacing a ranked board, make the single most prominent element answer "what
do I do?" not "where does this rank?". Keep it to the #1 only so it stays an anchor, never per-card
noise. Always verify headless: exactly one element, on the first non-avoid card, re-anchoring live on
re-sort/filter, zero console errors. Render-only, never touch scan.json. See [[explain-the-model-on-site]]
and [[support-touch-count]].
