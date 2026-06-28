---
name: forward-results-tracker
description: WheelForge grades its OWN forward picks (snapshot+settle in a local store), not just backtests the model
metadata:
  type: project
---

The backtest (`wheelforge/backtest.py`) only tests the safety MODEL on past OHLCV. It
never told us whether the picks the scanner actually PRINTED on a given morning held up.
c55 closed that with `wheelforge/results_tracker.py`: every build `snapshot()`s the day's
actionable CSPs (ticker/strike/exp/premium/score/predicted prob_otm/lane) into a local,
gitignored SQLite store (`data/results.db`, same pattern as [[forward-results-tracker]]'s
sibling iv_history.db), then `settle()`s any pick whose expiry has passed against price:
held above strike = OTM (premium kept) vs breach. `track_record()` reports forward hit
rate vs the predicted prob_otm, by lane.

**Why:** a scanner that only backtests is graded on a model, never on its own output;
trust comes from the forward record. **How to apply:** settle off prices the build
ALREADY has in hand (`tickers` spots), so no new feed; a pick whose name left the
universe stays PENDING (never crashed, never faked). It starts empty and fills over
weeks, exactly like the IV store. Open follow-ons: a track-record PAGE on the frontend,
and settling names that left the universe (needs a price-at-expiry lookup).
See [[wheelforge-design-principles]].
