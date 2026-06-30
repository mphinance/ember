---
name: unverifiable-hard-gate-warns
description: when a HARD avoid gate's input is entirely ABSENT (not just noisy), warn visibly instead of failing open silently or closed blindly
metadata:
  type: feedback
---

c78: the earnings veto is a hard thesis gate, but it can only fire on a known date. When
BOTH the screener feed and the c62 yfinance re-lookup come back empty, `earnings_days` stays
None, collapses to the `999` sentinel, and `earnings_blocks(999, dte)` is False, so a name
printing tomorrow surfaces as a CLEAN pick. Fix: emit `earnings_unknown = (earnings_days is
None)` on the pick and show a red `⚠ earnings unknown` chip; no scan.json (the box bakes it).

**Why:** two wrong defaults bracket the honest one. Fail-OPEN silently (today's behavior)
re-arms the exact blowup the gate exists to stop. Fail-CLOSED blindly (mark every such name
AVOID) blanks good names off the board every time a flaky feed hiccups, the same trap I
declined on the c37 earnings-gate flip. When you cannot run a hard gate at all, you say so.

**How to apply:** this is the ABSENT-INPUT cousin of [[flag-dont-silently-drop]] (which is
about NOISY-but-present inputs like thin OI). Same verdict, different cause: surface a visible
"could not verify" chip, let Michael size or skip, never silently assume the coast is clear and
never blank the board on missing data. The drop-the-pick verdict ([[no-bid-no-trade]]) is only
for UNAMBIGUOUS kills (no bid, a known print inside the window, sub-floor premium). Keep it
backward-compatible: an undefined field reads falsy, so a pre-bake scan.json renders unchanged.
