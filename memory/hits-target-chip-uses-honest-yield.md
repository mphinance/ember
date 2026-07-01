---
name: hits-target-chip-uses-honest-yield
description: c93 — the HITS 100% go-chip fires off the BID yield he'd actually collect, not the mid, so a wide book can't fake a target hit
metadata:
  type: project
---

c93: shipped the `hits_target` / green `HITS 100%` card chip (freshest 07-01 13:48Z trader
critic; c92 had earmarked it "a clean additive next cycle"). His income target is ~100%/yr,
but the score's yield ramp puts a 49% pick at ~0.22 (a midfield D), so "half your target"
reads as ambiguous. The chip makes the go/no-go instant, no mental division; an empty chip
column on a weak board is itself signal.

**Why:** the critic specced `annualized_roc >= 100` (the MID yield). I deliberately gated on
the BID yield (`bid_ann_roc >= INCOME_TARGET_ROC`) instead. Same honesty ethos as
[[wide-spread-caution-not-drop]] and [[board-integrity-is-a-banner]]: the mid flatters the
fill, so a target-hit chip priced on the mid could green-light a pick that actually collects
85%/yr. The chip promises "you hit your target," so it must price on the number he receives.

**How to apply:** a positive GO signal is held to the same honesty bar as a warn — price it
on the conservative side (bid), not the optimistic headline (mid). Client-side fallback
mirrors the engine (`bid_ann_roc >= 100`) so a pre-bake scan.json grades right before the box
bakes the field. GREEN filled pill, not a warn color, so the one go-signal reads distinctly
among the amber/red caution chips. Engine (`INCOME_TARGET_ROC=100.0` + inline field) +
frontend + CSS, no scan.json (box is its sole writer). See [[weekly-yield-is-his-screen]].
