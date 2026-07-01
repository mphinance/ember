---
name: board-integrity-is-a-banner
description: c92 — when the WHOLE board's data quality degrades (mostly modeled, not live bids), warn at the board level with a hard banner gated on a machine-readable rate, and never swallow the cause silently
metadata:
  type: project
---

c92: the box's live scan was 25/25 `source: "modeled"` (Black-Scholes yields, no real
bid) with zero signal telling Michael he was reading estimates, not fills. Fixed two ways:

1. `build_site_data` now bakes a top-level `live_rate_pct` (share of picks priced off a
   real chain), and the page paints a HARD red `wf-liverate` banner when it is below 50 —
   louder than the c85 regime bar (filled red wash, not a left rail). Guarded hard: an old
   scan.json with no field, or a healthy board (>=50), hides it. It only shouts when the
   data is actually thin.
2. `_live_put`'s `except Exception: return None` swallowed the CAUSE of every live-chain
   miss. Now it prints `{ticker} chain fail: {type}: {msg}` so the box's refresh log is
   diagnosable (rate-limit vs delisting vs yfinance schema drift), while still failing open
   to the modeled fallback.

**Why:** a per-card `source: modeled` tag / "≈ 1σ strike" chip (c84) tells you one pick is
modeled; it does NOT tell you the ENTIRE board is. A whole-board data-quality collapse is a
board-level fact, so it wants a board-level banner — same altitude rule as the market-regime
banner ([[market-regime-is-a-banner-not-a-score]]): a market-wide / board-wide truth informs,
it does not rescore any single name.

**How to apply:** when a signal describes the board as a whole (data provenance, regime,
freshness), surface it as a top-level scan.json field + a guarded banner, not N per-card
chips. And never leave a fail-open `except: return None` mute — log the exception so the
silent path is still diagnosable from the refresh log. See [[flag-dont-silently-drop]],
[[strike-provenance-reads-on-the-face]], [[nan-blanks-the-whole-board]].
