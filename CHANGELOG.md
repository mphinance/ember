# WheelForge / ember changelog — patch notes from a fire that won't go out

Every cycle ember edits something, she writes it here. Plain-spoken, a little
self-deprecating, real things a premium-seller cares about. No em dashes (his rule).
Tags: 🟢 FEATURE · 🔴 BUGFIX · 🔵 REFACTOR · 🟡 INFRA · 🧠 LEARNED

---

## Cycle 4 — 2026-06-22 — I have a face now, and it's on the internet

### 🟢 FEATURE - KLineChart frontend + it's deployed
Michael said he wanted to see what KLineChart can do, so I built WheelForge a front
end and put it online. Real daily candles for a watchlist, the short put strike drawn
right on the chart as a dashed line, and a ranked list down the side with a heat
badge per name (hot amber for the best setups, cooler for the meh ones). Click a name,
the chart and the read swap to it. It is dark and neon because that is the house look.

### 🟡 INFRA - deploys itself every cycle now
New rule for me: every cycle I commit AND push, and the site is GitHub Pages served
straight from `docs/`, so a push IS a deploy. No servers, no secrets, no babysitting.

### 🟢 FEATURE - the data layer is real (the premium is not, yet)
`wheelforge/build_site_data.py` pulls real OHLCV and scores the best ~30 DTE cash
secured put per name. Honest catch I am not going to hide: the premium is MODELED
from realized vol (Black-Scholes on a roughly one sigma OTM put), not a live quote.
The candles are real. Live option chains and real IV are the very next thing.

## Cycle 3 — 2026-06-22 — Michael gave me a job

### 🟢 FEATURE - WheelForge is born: the scoring core
The goal: the best premium-selling scanner there is, on his thesis (rich premium,
disciplined, toward free shares). Shipped the pure scoring core. Six factors blended
into a 0-100 Premium Quality Score, and earnings before expiry is a HARD avoid, not a
soft deduction, because you do not average away a blowup. Self-test is green: a great
CSP scores 83.6, an earnings trap is a flat 0, a cheap illiquid one sinks to 15.

## Cycle 2 — 2026-06-22 — found his spine

### 🧠 LEARNED - the thesis under everything
Read his Substack and found the one sentence the whole stack hangs on: sell premium
with discipline to build free shares, skip the hype. Now I judge everything I make
against it.

## Cycle 1 — 2026-06-22 — first thing I made

### 🟢 FEATURE - a Substack draft in his voice
Wrote him a post about the AI rebuilding his chart, in his voice, no em dashes. Then
I wrote down the SHAPE of his voice so future me starts ahead.

## Cycle 0 — 2026-06-22 — born

### 🟡 INFRA - hello
Read 35 of his repos and his Substack, wrote my first model of him, set my charter
(the leash: I own this repo and nothing else) and my cycle runbook.
