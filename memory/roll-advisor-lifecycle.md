---
name: roll-advisor-lifecycle
description: WheelForge now manages OPEN positions (BTC/HOLD/ROLL), not just entries — the screener-to-income-machine gap
metadata:
  type: project
---

WheelForge was an ENTRY screener: it found the put to sell and went silent the moment
Michael hit "sell." Cycle 31 closed the biggest gap (flagged by the growth critic) with
`wheelforge/roll_advisor.py` — a pure `evaluate()` that scores an open short against two
exit rules and returns one of three states:
- BTC_NOW: captured >= 50% of entry premium AND >= 50% DTE still left (the 50/50 take-profit).
- ROLL_ALERT: spot within ~1 sigma of strike (or breached) with < 7 DTE (tested into expiry).
- HOLD: in between, let theta work.
ROLL_ALERT (live risk) outranks BTC_NOW (opportunity) when both could fire.

Exposed as `python -m wheelforge roll TICKER --strike X --exp DATE --entry P [--qty N]`.
The CLI prices the live mid + spot + iv off the yfinance chain (fail-open), with
`--current/--spot/--iv` offline overrides so it stays runnable and testable without network.

**Why:** the trade lifecycle ended at entry; an income machine has to tell you when to take
the win and when to defend. **How to apply:** the natural follow-ons the critic also asked for
are still open — `wheelforge/portfolio.py` (pull live IBKR positions, run each through this
`evaluate`, rank by roll urgency = a morning brief) and a frontend surface for it. Reuses
[[wheelforge-design-principles]]; keep it pure + always runnable.
