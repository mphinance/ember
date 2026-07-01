---
name: assignment-starts-the-second-leg
description: c89 — a settled CSP breach is an ASSIGNMENT, the START of the wheel's second leg; surface the covered call to sell against those shares, wired fail-open and dormant.
metadata:
  type: project
---

c89: closed the CSP -> assignment -> covered-call loop the whole thesis is built on. The
`covered_call.py` engine existed since c48 but nothing connected an assignment to it, so the
income machine only had system support for the first third (entry).

A settled BREACH in results_tracker is an assignment: the put closed ITM, so you were put 100
shares/contract at the strike. That is not the END of a trade, it is the START of the second
leg. Pure `assigned_positions(db_path)` reads breached PUTs (deduped per option, earliest
premium = closest to entry) and hands back the effective cost `basis = strike - entry_premium`
(you pay the strike but keep the premium you sold). The CLI's bare `roll` brief then prices the
lowest OTM call at/above that basis via the same `covered_call_read` the `cc` subcommand runs,
printing `WHEEL NVDA sell $180 call exp DATE @ $prem -> new basis $X`.

**Why:** the wheel is entry -> (assignment) -> covered call -> repeat; a scanner that stops at
assignment abandons Michael at the exact moment the work continues (build toward free shares,
definition-of-best #5).

**How to apply:** (1) only a breached PUT is a share assignment; a breached COVERED CALL is a
call-AWAY (shares SOLD), so filter on direction. (2) Same pattern as [[empirical-flywheel-feeds-the-score]]:
wire the feedback loop fail-open and DORMANT so it engages itself as expiries settle (the box's
store today has 0 settled, so the WHEEL section prints nothing until a real breach). (3) Module
stays PURE (the reader); the live call chain lives in the CLI, like roll/cc. See [[roll-advisor-lifecycle]].
