---
name: wide-spread-caution-not-drop
description: c86 — a wide bid/ask spread means the mid-priced yield overstates the fill; flag it, do not drop it
metadata:
  type: project
---

c86: the headline annualized RoC is priced on the MID, but you sell-to-open into the BID, so a
wide book fills far below the quoted yield (a $0.10/$0.50 book has a $0.30 mid that a limit order
fills near $0.10). Added `_spread_pct(bid, ask)` = `(ask-bid)/mid` + `_wide_spread(bid, ask, source)`
(live path only, threshold `WIDE_SPREAD_PCT=0.30`) in build_site_data; baked `spread_pct` + `wide_spread`
onto each pick, and the card paints an amber `⚠ wide spread (N% of mid)` chip whose tooltip points at
the already-baked `bid_ann_roc` (the conservative fill).

**Why:** tradeability is definition-of-best #3 (edge you cannot fill is not edge); the recurring risk
critic kept flagging that a wide book overstates the displayed yield. It is the same integrity gap
[[no-bid-no-trade]] closed for the no-bid case, one rung softer.

**How to apply:** a WIDE spread is a real tradeable strike at a worse fill, so FLAG it, never drop it —
same discipline as [[flag-dont-silently-drop]] and the thin-OI chip. Drop only on unambiguous inputs
(no bid, earnings, sub-floor premium). Live path only: the modeled path carries a synthetic ~4% spread
by construction, so flagging it would be noise. Fail-open to not-wide on a missing/one-sided/crossed book.
