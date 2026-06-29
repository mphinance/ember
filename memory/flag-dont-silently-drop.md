---
name: flag-dont-silently-drop
description: when a gate's INPUT is noisy or unverifiable, surface a visible chip, do not silently drop or rescore the board
metadata:
  type: feedback
---

When a critic (or I) wants to GATE a pick out, first ask: how trustworthy is the gate's
input, and can I verify the live effect? If the input is stale/noisy and I cannot re-check
it in a headless build, prefer a VISIBLE FLAG over a silent drop or rescore.

c71 case: the strike-level OI gate (critic asked: drop any strike with OI < 50). Real hole
(the support-anchored strike can land on a thin line), but yfinance reports OI=0/NaN intraday
for many valid weeklies until the daily settle, and the cycle env has no live chain to verify.
A hard drop-gate would have blanked good LIVE picks to MODEL on data I could not trust. So I
shipped a `thin_oi` flag + a `⚠ thin OI` chip (live path only; modeled carries oi=0 and already
says MODEL) instead. The c60 bid<=0 drop was different and a drop WAS right: no bid is
unambiguous and unfillable, not a stale-data artifact.

**Why:** a silent drop/rescore on bad input is invisible and unfalsifiable; it reads as
"covered everything" while quietly removing real trades. A flag is honest, reversible, lets
Michael judge, and never regresses the board on a data glitch.

**How to apply:** drop/veto ONLY on inputs that are unambiguous and trustworthy (no bid, an
earnings print, premium under the floor). For a contestable or stale-prone signal (thin OI,
sector crowding, skew, bid-vs-mid yield), surface a visible chip/field and let the score and
rank stand. Same lineage: [[critics-dont-override-settled-calls]], [[no-bid-no-trade]],
[[put-skew-lifts-richness]], [[support-touch-count]].
