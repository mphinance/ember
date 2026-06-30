---
name: show-the-value-not-the-flag
description: a "shown per name" UX item means surface the actual VALUE on the card, not just a presence flag
metadata:
  type: feedback
---

c76: the floor badge said `⌂ support x4` (a boolean "there is support" plus a touch
count); the support PRICE ($382.97) lived only in the tooltip and on the chart line. The
GOAL page-UX item "a supportFloor shown per name" wanted the number, not the flag. Fixed
by adding ` $' + fmt(p.support)` to the badge, render-only off the existing scan.json field.

**Why:** a seller acts on WHERE the floor is, not merely THAT one exists. A badge that
carries the value ("$383") is decisions-grade; a badge that only asserts presence makes him
hover or open the chart. Most-glanceable pixels should carry the number.

**How to apply:** when a roadmap item says "X shown per name," check whether the card shows
X's VALUE or just a flag/icon that X applies. If the real number is already in scan.json,
surface it inline (null-guarded, through `fmt`/`esc`). Same family as
[[top-pick-reads-as-headline]] (the #1 card shows the actual trade, not just a TOP badge).
