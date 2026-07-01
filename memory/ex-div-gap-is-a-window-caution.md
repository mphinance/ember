---
name: ex-div-gap-is-a-window-caution
description: c90 — an ex-div date inside the option window is a warn chip (gap-down can push a put ITM), not a veto; fail-open pure helper + yfinance wrapper
metadata:
  type: project
---

c90: a name that goes EX-DIVIDEND before the chosen expiry gaps DOWN by the dividend on the
ex-date, which can push a just-OTM put ITM with no real move in the tape (the drop is
mechanical). Three separate risk critics flagged this (06-28, 06-30, 07-01). Shipped as a
`⚠ ex-div in window` amber card chip, the same flag-not-drop discipline as thin-OI /
wide-spread / next-cycle-earnings.

Shape (mirrors the earnings plumbing exactly): pure `_ex_div_in_window(ex_div_date, today,
exp)` (True iff today <= ex <= exp, coerced via `_as_date`, any missing input -> False) +
fail-open `_lookup_ex_div_date(ticker)` reading yfinance `.calendar['Ex-Dividend Date']`
(handles both the dict and the older DataFrame shape; any error -> None). `build_one` bakes
`ex_div_in_window` + `ex_div_date` on the pick; app.js paints the chip with the ex-date in
the tooltip. Self-tested (8 asserts) + headless verified (exactly one chip, ex-date in title,
0 errors). Engine + frontend, no scan.json.

**Why:** the critics framed it as put early-exercise (technically backwards for puts), but the
REAL risk a put seller feels is the mechanical ex-date gap-down turning an OTM strike ITM. On
thesis (an assignment-risk cousin of the earnings blowup gate, def-of-best #4/#5).

**How to apply:** when a hard-gate's input is a date you fetch fail-open, warn with a visible
chip rather than veto — a flaky feed must never blank the board. See
[[unverifiable-hard-gate-warns]], [[flag-dont-silently-drop]]. Verify frontend chips on a
TEMP docs copy with an injected flag, never by touching docs/data/scan.json (the box owns it).
