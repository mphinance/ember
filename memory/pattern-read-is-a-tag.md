---
name: pattern-read-is-a-tag
description: c88 pattern read is a VISIBLE per-name tag, not a structure rescore; separate breakdown from downtrend by RECENCY of the drop, not kp alone
metadata:
  type: project
---

c88: shipped the price-action PATTERN read (Michael's idea) — `wheelforge/patterns.py::read_pattern(candles)`
classifies the few OHLCV shapes a put seller trades on: support_hold (bounced off a recent low, buyers
defending the floor = good), breakdown (fresh violent break under the Keltner floor = avoid), downtrend
(steady grind lower, no bounce = avoid), coiling (tight mid-channel range = neutral), else none. It rides
the pick as `pattern` {tag, bias, read} and paints a colored card chip (green/red/gray).

**Why:** structure_with_floor already OWNS the structure factor, so the pattern is a FLAG he reads, not a
silent rescore — same flag-dont-silently-drop discipline as [[flag-dont-silently-drop]] and [[wide-spread-caution-not-drop]].
Two signals must never double-count the same trend.

**How to apply:** (1) breakdown vs downtrend cannot be told apart by Keltner position (kp) alone — in a
PERSISTENT downtrend price rides ALONG the lower band so kp sits ~0 the whole way, same as a fresh break.
Separate them by the RECENCY of the drop: breakdown = the fall is concentrated in the last ~3 bars
(`ret3 <= -0.05` with kp low); a steady grind falls through to downtrend. (2) A sharp synthetic dip inflates
Wilder ATR (one 12-point-range bar blows out the 3*ATR band), so you can't test "tagged the lower band" with
a one-bar spike — define support_hold off a REAL dip-then-recover (`low <= spot*0.96` then `spot >= low*1.02`)
plus a low-ish kp, not off touching the band. Verify frontend headless: copy docs/ to a tempfile, inject the
new field into a scan.json copy, load in chromium (playwright is in .venv), assert chips render + 0 console errors.
See [[strike-at-or-below-support]] for the sibling structure signal.
