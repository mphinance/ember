---
name: no-bid-no-trade
description: a put with no market-maker bid cannot be sold; never quote a premium off lastPrice (c60)
metadata:
  type: project
---

c60: WheelForge quotes a cash-secured put's premium from the live chain, and you sell-to-open,
so the credit you actually receive is anchored on the BID. A strike with `bid <= 0` has no
buyer; it cannot be sold at any price. The old `_quote_expiry` fell back to `lastPrice` (a stale
historical fill) when there was no two-sided quote, and that phantom cleared `_tradeable_premium`,
scored 60-80 (liquidity is only ~13% of the blend), and landed on the board as actionable.

Fix: pure `_sellable_premium(bid, ask)` — None when `bid <= 0` (drop the strike), the mid when both
sides are real, the BID alone when there is a bid but no ask (conservative, never invent the offer
side). `_quote_expiry` returns None on None, killing the `lastPrice` fallback entirely.

**Why:** the income thesis is rich premium you can ACTUALLY collect; quoting credit nobody is offering
to pay is the same dishonesty as faking a roll credit (c46) or trusting a one-touch ghost floor
([[support-touch-count]]).

**How to apply:** when pricing any option leg off a chain, anchor on the side you trade (sell -> bid,
buy -> ask); the mid is a convenience, not a fillable promise, and `lastPrice` is never a quote. Still
open: `bid_ann_roc` so the YIELD reads off the bid not the mid (next risk bullet). See [[relative-premium-floor]].
