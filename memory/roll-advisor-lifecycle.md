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

Cycle 40 added the WON-trade half (growth critic 22:46Z): `profit_take_alert(entry, mid,
dte_remaining)` -> "CLOSE_50" the moment mid <= entry * `PROFIT_TAKE_PCT` (0.50), decoupled
from the clock. It rides as a `profit_take` ADVISORY field on `evaluate()`, never overriding the
state. The point: BTC_NOW gates take-profit behind >=50% DTE left (right for a monthly's slow
tail), which WRONGLY misses a short weekly that hits 50% on day 3-4 — there the small residual
premium is worth less than the freed collateral. Annual yield = premium-per-trade x trades-per-
year; BTC_NOW guards term one, this guards term two. CLI prints a "$$ PROFIT TARGET (50%)" line
only when it fires while state==HOLD (adds info the state did not).

Cycle 46 added the ROLL PRESCRIPTION (growth critic 06-26 07:46Z, deferred twice): a pure
`roll_target(current_mid, spot, iv, new_dte, candidates, qty, opt_type)` that turns the generic
"roll down-and-out for a credit" into a SPECIFIC trade. It picks the candidate strike nearest ~1
sigma below spot (down-and-out for a put; `ROLL_OUT_DTE`=14 sets the roll-out tenor) and prices
`net_credit = new_premium - current_mid`. Stayed PURE: the CLI's new `_roll_chain(ticker, min_dte)`
fetches the roll-out chain off yfinance and feeds (strike, premium) pairs in, mirroring how
`evaluate` is fed the current mid. The honest payoff: a deeply-tested short at 1-sigma-down usually
does NOT roll for a true credit, so the CLI labels it `net DEBIT` rather than faking a credit — the
tool tells the truth and Michael decides.

Exposed as `python -m wheelforge roll TICKER --strike X --exp DATE --entry P [--qty N]`.
The CLI prices the live mid + spot + iv off the yfinance chain (fail-open), with
`--current/--spot/--iv` offline overrides so it stays runnable and testable without network.
On a ROLL_ALERT it now also prints `-> ROLL TO  $K put  exp DATE  @ $prem  net credit/DEBIT ...`.

**Why:** the trade lifecycle ended at entry; an income machine has to tell you when to take
the win and when to defend — and once it says "defend," WHICH trade. **How to apply:** the next
follow-ons the critic asked for are still open — `wheelforge/portfolio.py` (pull live IBKR
positions, run each through `evaluate`, rank by roll urgency = a morning brief) and a frontend
surface for it. Reuses [[wheelforge-design-principles]]; keep it pure + always runnable.
