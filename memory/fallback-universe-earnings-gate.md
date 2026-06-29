---
name: fallback-universe-earnings-gate
description: c62 — a hard veto must hold on the degraded path too; fallback names get a yfinance earnings re-lookup so the gate never silently disarms
metadata:
  type: project
---

c62: WheelForge's earnings-avoid is a HARD veto (GOAL definition-of-done #4), but it
only fired on the happy path. The TradingView screener supplies `earnings_days`; when it
is down, `universe.py` ships 30 FALLBACK tickers with `earnings_days=None`, which bypasses
BOTH `_candidate_expiries` (tenor filter) AND `earnings_blocks` (score veto). So NVDA two
days before a print could surface as a clean pick with no AVOID card precisely when the
data layer was already degraded.

Fix: in `build_one`, when `earnings_days is None`, do a secondary
`yf.Ticker(ticker).get_earnings_dates()` lookup and set the nearest FUTURE date before
scoring. Pure tested helpers: `_as_date` (coerce date/datetime/Timestamp/ISO; datetime is
a date subclass so convert it FIRST) and `_nearest_future_earnings_days(dates, today)`
(skip past prints, a print today = 0 days = still vetoed). Network wrapper
`_lookup_earnings_days` is fail-open (None stays None, never crashes the build).

**Why:** a safety gate that only works when the upstream feed is healthy is no gate. The
fallback path is exactly the moment you most need the veto armed.
**How to apply:** when a factor is a VETO not a score, make it hold on every degraded
path, not just the primary one. Prefer a pure helper + a fail-open network wrapper so the
logic is testable offline. Same shape as [[no-bid-no-trade]] and [[support-touch-count]].
