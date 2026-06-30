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
weeks, exactly like the IV store. Open follow-on: settling names that left the universe
(needs a price-at-expiry lookup). See [[wheelforge-design-principles]].

c82 SHIPPED the track-record PAGE follow-on. `track_record()` was computed every build since
c55 but only PRINTED; now build_site_data bakes it into scan.json as top-level `record`, and
the page paints a "forward record" strip under the changes strip: `N settled · X% kept OTM vs
Y% predicted · $Z avg premium · M pending`, colored green when actual beats the forecast.
Hard-null-guarded: an old scan.json with no `record` (or an empty store) HIDES the strip, so
the committed scan.json stays valid and the box fills the numbers on its next refresh. Even
pre-settle it shows "tracking M forward picks, none settled yet" so the flywheel reads as live.
The proof the machine works finally lives on the page, not just the print log.

c65 added a SECOND read off the same OPEN rows: `profit_take_alerts(quote, threshold=0.50)`
+ `open_positions()` (deduped one-per-option, anchored on the EARLIEST snapshot's premium =
closest to entry) + `PROFIT_TAKE_PCT=0.50`. It flags open picks now buyable for <= half the
entry, the winners to BUY BACK and recycle the collateral into a fresh week (trades-per-year
is the income machine's other multiplier; see [[roll-advisor-lifecycle]]). Kept the module
PURE per the ethos: the pure fn takes a `quote(ticker,exp,strike)->mid` callable/dict, the
yfinance network lives in the CLI's `_put_mid`. Surfaced as BARE `python -m wheelforge roll`
(no position args) = the morning close-the-winners brief; a specific position still runs the
single-position BTC/HOLD/ROLL manager. Only judges still-LIVE options (a passed expiry is
settle()'s job). Distinct from roll_advisor's `profit_take` advisory (c40), which is per a
single hand-entered position; this scans the whole tracked DB at once.
