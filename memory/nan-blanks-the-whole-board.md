---
name: nan-blanks-the-whole-board
description: a NaN float rides into scan.json as an invalid `NaN` token and blanks the ENTIRE board on JSON.parse; fail-open guards must reject NaN, and the write needs a sanitizer + allow_nan=False
metadata:
  type: project
---

c87: the committed scan.json carried `"vix3m": NaN` (a partial VIX3M feed outage in c85's
regime read), and `json.dump` writes a NaN float as the bare token `NaN`, which is NOT valid
JSON. The browser's `JSON.parse` threw, so the page showed "no scan data yet" and the WHOLE
board was blank, not just the regime banner. The live site was down and no per-name work would
have shown.

**Why:** two silent traps compound. (1) `float('nan')` does NOT raise, and `NaN <= 0` is
False, so a NaN slides straight through a `try/except (TypeError, ValueError)` + `<= 0`
fail-open guard as if it were a valid number. (2) `json.dump`'s default `allow_nan=True`
emits `NaN`/`Infinity` tokens that Python re-reads happily but every strict JSON parser
(including every browser) rejects. One bad float takes the entire site down, not one field.

**How to apply:** when a value can come from a flaky numeric feed, reject NaN/Inf EXPLICITLY
in the fail-open guard (`if v != v or v == float('inf'): return None` — `NaN != NaN` is the
portable test), not just None/type errors. And at the JSON boundary, sanitize NaN/Inf to null
recursively (`_json_safe`) AND pass `allow_nan=False` so a miss raises loud instead of
shipping a board-blanking token. Cousin of the "never blank the site" empty-scan bail: a
single number must never be able to blank the whole board. See [[market-regime-is-a-banner-not-a-score]].
