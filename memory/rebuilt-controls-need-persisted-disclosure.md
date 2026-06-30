---
name: rebuilt-controls-need-persisted-disclosure
description: c83 - a collapsible inside a panel that re-renders wholesale on every click must persist its open state in app state, or it snaps shut on the next interaction
metadata:
  type: project
---

c83: WheelForge's `buildControls()` (docs/app.js) wipes and rebuilds the entire
`#wf-controls` host on EVERY pill click (`host.innerHTML = ''` then re-append). So
when I tucked the secondary filter rows behind a `<details class="ctl-more">` to clear
chrome off the #1 pick's headline, a naive disclosure snapped shut the moment Michael
clicked a lane/yield/cap pill inside it (the rebuild re-creates the element closed).

Fix: hold the open/closed flag in app state (`state.moreOpen`), set `more.open =
state.moreOpen` on each rebuild, and update it from the element's `toggle` event. The
DOM element is disposable; the UI state is not, so the state lives in the state object,
not on the element.

**Why:** any rebuilt-from-scratch control panel loses per-element UI state (open
disclosures, scroll, focus) unless that state is lifted into the model it rebuilds from.
**How to apply:** before adding a `<details>`, accordion, or any toggle inside a function
that re-renders its whole container, give it a `state.*` flag and re-apply it on rebuild
(and ideally restore focus/scroll too). Verify the persistence path explicitly in the
headless check: expand, trigger a rebuild (click a child control), assert still-open.

This served the headline arc [[top-pick-reads-as-headline]] / [[headline-is-a-complete-ticket]]
by clearing ~80px of chrome so the trade ticket leads. Same render-only, no-scan.json
discipline as the rest of [[explain-the-model-on-site]].
