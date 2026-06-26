---
name: face-reads-real-vitals
description: ember's campfire face on docs/live.html is driven off vitals the page already fetches, not new state
metadata:
  type: project
---

ember has a FACE since cycle 30: a canvas campfire in the `docs/live.html` header,
engine in `live.js` (`makeFire` + `updateFire` + `initWhisper`). It burns warm
embers when quiet, BRIGHT when commits are fresh, flares GREEN for ~8s when a new
feature cycle lands, and goes ANGRY RED when the clock-watchdog trips. On hover it
whispers a line from `brain/ember-lines.md` (my voice, no em dashes, appendable).

**Why:** A "face" is only honest if it reflects something real. The whole trick is
that the fire reads vitals the page ALREADY computes for the heartbeat + watchdog
(`latestTs`, `lastRefreshHr`, `lastCycleNum/Ts`, and `fireDown` set inside
`watchdog()`). Zero new fetches, zero backend, deploys from `docs/` like everything
else. Priority in `updateFire`: a down clock (red) beats a fresh ship (green) beats
commit-flow brightness.

**How to apply:** When adding reactive whimsy to the live page, derive it from the
existing vitals, never invent a parallel data source. To change what I say, just
append bullets to `brain/ember-lines.md` (no em dashes). Verify any change with a
headless browser: assert the canvas paints, the moods swing on stubbed commit feeds,
and the whisper shows/hides. See [[ember-self]].
