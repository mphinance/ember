---
name: market-regime-is-a-banner-not-a-score
description: c85 VIX-term-structure regime read is a top-level banner, never a per-name score input, because a market-wide factor would double-count and distort the ranking
metadata:
  type: project
---

c85: shipped the MARKET REGIME banner (roadmap item, StrikeForge market_weather port).
New pure `wheelforge/market_weather.py::market_regime(vix, vix3m)` classifies the whole tape
from the VIX term structure: VIX3M > VIX (contango, ratio < 1) = calm/normal, sell premium;
VIX >= VIX3M (backwardation, ratio >= 1) OR a high absolute VIX = stressed, be picky. Returns
a dict (label + one-line note + the raw numbers) or None on a missing feed (fail-open).

**Why it is a top-level `regime` field, NOT a factor on any pick:** the regime is market-WIDE,
identical for every name on the board. Folding it into per-name scores would shift every score
by the same amount (a no-op on the RANKING) while also double-counting risk the per-name safety
factor already prices from each name's own vol. So a regime read has no business editing the
score at all. It rides scan.json as a sibling of `changes`/`record` and paints a non-blocking
banner Michael reads BEFORE he sells. This is the cleaner cousin of the credit-a-signal-never-
rescore discipline ([[put-skew-lifts-richness]], [[flag-dont-silently-drop]]): a per-name signal
can earn bounded credit; a market-wide one shouldn't touch the score at all, only inform.

**How to apply:** the yfinance ^VIX/^VIX3M pull lives in build_site_data (`_last_close`,
`_regime`, fail-open), the classification stays pure in market_weather.py (mirrors levels/
surface). Frontend `renderRegime(d.regime)` null-guards hard: no `regime` (old scan.json or a
dead VIX feed) hides the banner entirely, so the committed scan.json stays valid and the box
fills it on its live refresh. Verified headless across calm/normal/stressed/absent, 0 console
errors. Live fetch in-cycle read VIX 16.45 / VIX3M 19.0 -> normal contango.
