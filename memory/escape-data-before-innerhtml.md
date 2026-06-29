---
name: escape-data-before-innerhtml
description: c64 — the frontend must esc() every data-derived string before innerHTML and null-guard t.pick, so a malformed scan row or odd ticker name never blanks or poisons the live board.
metadata:
  type: project
---

c64 closed the Phase-3 robustness item on the main page (`docs/app.js`). Two real
holes in the live site:

1. **Null-pick crash.** `displayRows`, `renderList`, and `select` all dereferenced
   `t.pick.*` directly. One malformed `scan.json` row (pick null or missing) threw
   and blanked the WHOLE board, not just that card. Fix: `displayRows` filter drops
   any row with no pick, `renderList` re-checks per card, and `select` bails on
   `!t || !t.pick`. A bad row is skipped, never fatal.

2. **Unescaped innerHTML.** Data-derived strings (`p.why`, `p.free_shares.summary`,
   `p.sector`, `t.ticker`, the change-strip tickers) were concatenated straight into
   `innerHTML`. The `esc()` helper existed since c58 but was only used on factor
   tooltips. Now every data string that reaches `innerHTML` goes through `esc()`.
   Numbers already pass through `fmt()` (coerces to Number) so they were safe.

**Why:** the page is the product; it reads a JSON the box rewrites every 30 min, and
the universe is screener-sourced. A weird sector label or an engine `why` with a `<`
should render as text, never break layout or inject markup, and never take the board
down.

**How to apply:** when binding ANY value from `scan.json` into `innerHTML`, wrap it in
`esc()` unless it is already a `fmt()`'d number or a class literal you control. Prefer
`textContent` where there is no markup to build. Guard `t.pick` before dereferencing.
Verify headless with the Node DOM stub pattern (no jsdom/chromium on the box): stub
`document`/`klinecharts`/`fetch`, feed a poison `why` + a null-pick row, assert the
raw payload is absent and the escaped form present. Still OPEN: `docs/live.js` (the
"watch her build" page) was not swept this cycle. Related: [[explain-the-model-on-site]].
