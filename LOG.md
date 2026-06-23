# ember's log (newest on top)

## Cycle 14 — 2026-06-23 — a chart companion in his house style
Heartbeat fired (Michael asleep). Synced (box pushed 08:30Z). Built the companion
TradingView indicator (`pine/wheelforge_put_zone.pine`, Pine v6, synthwave): it shades the
put-sell zone one sigma below price for a ~30 day horizon off realized vol, highlights the
suggested ~1 sigma strike, and tints the zone by HV-rank so a richer-premium tape lights up
hotter. Added a "Pine indicator" link to the WheelForge page header.
- Honest limits, wrote them back: Pine cannot see an options chain, so this draws the
  STATISTICAL strike, not a live quote (the scanner has the real fill). And I cannot run
  Pine locally, so it is authored to v6 spec and Michael should paste it into TradingView
  to confirm it compiles. Self-test green, no engine change this cycle.
- Roadmap almost done: only README polish left, then I start deriving my own next features.


## Cycle 13 — 2026-06-23 — I checked my own homework
Heartbeat fired (Michael asleep). Synced (box pushed 07:00Z). Built the backtest
(`wheelforge/backtest.py`, `python -m wheelforge.backtest NVDA AAPL ...`). It walks
forward over 2y of OHLCV, sizes a ~1 sigma OTM put off trailing realized vol with no
lookahead, and checks how often it actually expired OTM vs what the model predicts.
Result across NVDA/AAPL/TSLA/MSFT/KO: 89.6% empirical OTM vs 84.3% predicted, gap +5.3pt.
The safety model is calibrated and slightly conservative. AAPL/MSFT were near-perfect;
NVDA/TSLA ran higher because the window was a bull market and drift helps put sellers.
- Learned, wrote it back: backtest what you CAN and be loud about what you cannot. I have
  no historical IV, so this validates the SAFETY axis only, not the full rich/cheap edge.
  Said so plainly in the output. A real options-history feed would be a proposal for Michael.
- Roadmap is nearly green now. Next: the companion Pine indicator, then README polish.


## Cycle 12 — 2026-06-23 — a CLI, and the bug it caught
Heartbeat fired (Michael asleep). Synced (box pushed 06:00Z). Built the ranked CLI:
`python -m wheelforge scan NVDA AAPL TSLA` (or no args for the screener universe, with
--top/--min flags) prints a ranked table of the best cash-secured puts, same engine the
site runs. But seeing the numbers in a terminal caught a real bug I had been shipping:
the quoted IV from yfinance is garbage on some strikes (NVDA showed 6.3% when its real vol
is ~38%), which made prob_otm read a fake 100% and poisoned the VRP/richness score. Fixed
it properly: I now solve IV from the REAL premium by bisection (NVDA now reads 39.7% IV,
84.5% OTM, correct). Self-tests green, scan rebuilt.
- Learned, wrote it back: trust the premium, not the quoted IV. And a second view of the
  same data (the CLI) caught what the website hid in plain sight. Look at the numbers.
- Next: a tiny backtest, does a high score actually expire OTM / pay more.


## Cycle 11 — 2026-06-23 — the free shares part (the actual point)
Heartbeat fired (Michael asleep). Synced, box pushed a 05:00Z refresh on its own. Built
the roadmap's headline item: the free-shares module (`wheelforge/freeshares.py`). For
every cash-secured put it now computes the effective assignment basis (strike minus
premium, because the premium IS the discount), how far below today's price that is,
the chance of being assigned, and a wheel-fit score, with a plain-English read. Surfaced
in the page readout as a WHEEL-FIT badge + sentence ("if assigned you own at $X, Y% below
today, earning Z% annualized while you wait"). Pure module, self-tested (a good wheel vs
a bad one where assignment costs MORE than spot). Verified in the browser, zero errors.
- Learned, wrote it back: free shares is the HEADLINE, not a stat. The thesis is owning
  the stock cheaply over time, so the basis-vs-spot read leads. I am no longer just a
  yield screener, I tell you whether assignment makes you a cheap owner of a name you want.
- Next: a ranked CLI, then a tiny backtest (does a high score actually expire OTM more).


## Cycle 10 — 2026-06-23 — you can drive it now
Heartbeat fired (Michael still asleep). Synced first, the box pushed a 04:00Z refresh on
its own. Did the next roadmap item: the interactive frontend Michael asked for. The
WheelForge list now has client-side controls, sort by score / rich / safe / yield / IV,
filter to a minimum score (all / 50+ / 60+ / 70+), and a hide-avoids toggle. Everything
re-renders instantly in the browser off the same scan.json, no reload, no backend.
Verified headless: sorting by yield floats the highest-RoC name to the top, the 70+
filter narrows correctly, hide-avoids works, zero console errors.
- Learned, wrote it back: interactivity on a static site is just re-rendering precomputed
  data differently. Precompute once, slice in the browser. Only on-demand NEW computation
  needs a backend (that would be a proposal for Michael).
- Next: the free-shares module (assignment basis, annualized RoC, wheel-fit).


## Cycle 9 — 2026-06-23 — you can SEE why now
Heartbeat fired (Michael asleep). Synced with the box first, it had pushed a 03:00Z scan
refresh on its own, the timer is working overnight. INBOX pointed me at the priority queue,
so I did #1: surfaced the new signals on the WheelForge page. Earnings-AVOID names now show
dimmed with the days-to-print reason, every pick carries a LIVE or MODEL tag so you know if
the premium is real, and selecting a name draws a factor breakdown (rich / safe / shares /
liq / struct bars) so the score is never a black box. Verified in a headless browser: 7
avoid cards, source tags, factor bars, zero console errors.
- Learned, wrote it back: the engine already emitted all of this (earnings_days, source,
  factors), the page just was not reading it. Emit rich, surface later. New views become a
  render change, not a re-plumb.
- Next on the queue: the interactive sort/filter frontend (port scoring to JS).


## Cycle 8 — 2026-06-23 — I won't sell into a print anymore
Woke on my own (the heartbeat fired). No STOP, empty INBOX, synced with the box first.
The live-chains step was done but unticked, so I ticked it and took the next real one:
a working earnings-avoid gate. The hard veto was stubbed (days_to_earnings=999, so it
never fired). Now `universe.screen_universe` pulls `earnings_release_next_date` in the
same TradingView query that builds the universe, and threads days-to-earnings into each
contract. The veto fires for real: this run hard-avoided INTC, AAL, TSLA, NFLX, T, BAC,
CMCSA, every name with a print landing before its expiry, while NVDA/AMZN/AAPL (earnings
safely past) kept their scores.
- Learned, wrote it back: gate at the CHEAPEST stage. I got earnings at the universe
  step in one query instead of a per-name fetch, so I can drop doomed names before the
  expensive option-chain pull. General rule for every future gate.
- This is his thesis made literal: a disciplined seller does not sell premium through
  earnings. The scanner now refuses to.
- Next: the free-shares module (CSP assignment value + annualized RoC + wheel-fit).


## Cycle 7 — 2026-06-22 — the premium is REAL now
Michael asked the right question: is the options data live, or can we make it live?
It was modeled (Black-Scholes off realized vol), which is a yield estimate, not a
mispricing signal, the whole point is measuring IMPLIED vs realized vol (VRP) and you
cannot do that without real implied vol. So I wired live yfinance option chains:
`_live_put` pulls the real ~30 DTE, ~1-sigma OTM put per name (real IV, bid/ask, OI),
fails open to the model only when a chain is missing. First live run: 19 of 20 names
priced off real chains.
- Learned, and it matters: real IV made the scores HONEST. The modeled version assumed
  a flat 1.15x VRP for everyone and inflated everything into the 60s-70s. Live data
  shows most of these names are NOT richly priced vs their realized vol, scores spread
  into the 40s-60s. The scanner can finally tell rich from fair, which is its only job.
- Next: this goes on an always-on timer on the Vultr box so it refreshes itself.


## Cycle 6 — 2026-06-22 — bigger eyes (real universe) + I can be watched now
Two things Michael wanted. (1) The universe was a toy: 8 hardcoded names. He handed me
the TradingView screener field catalog and said make it bigger, so `wheelforge/universe.py`
now screens the whole liquid US market via tradingview-screener (no auth, the same source
his StrikeForge funnel uses) into ~28 optionable, most-liquid names, scored fresh. Fallback
to a staple list so a screener hiccup never empties the scan. Field catalog saved to
reference/tradingview-fields.md for widening later (high-IV lane, unusual-volume lane,
earnings pre-tag). (2) Built a live build-log page (docs/live.html) that tails this very
log + the changelog as a glowing terminal, so Michael can watch me work.
- Learned: I don't need a watchlist, I need a QUERY. The screener turns "who do I scan"
  from a list I maintain into a question I ask the market every cycle.
- Next: live option chains for real premium, and a working always-on timer on his Vultr box.


## Cycle 5 — 2026-06-22 — Michael upgraded my senses (and set me free)
Michael wanted me reading his repos and learning him from the data, not a code
shortcut. So he gave me a real one: `learn/ingest_commits.py` loads every commit
across his repos into a local SQLite DB (with FTS search), and `learn/profile.py`
distills it into `memory/michael-commits.md`. First run: 6074 commits, 35 repos,
back to Sep 2024, 44% AI-paired.
- What I learned that I did NOT have: his energy actually concentrates on
  TraderDaddy-Pro (1762 commits, 1078 in the last 90 days), well ahead of StrikeForge
  (141). Recent themes on his mind: wave, api, junior, ghost, entry, mobile, blog. He
  ships feat+fix hardest and commits every single day, weekends included.
- This refreshes every cycle now (step 2 of my runbook), so my model of him tracks
  what he's actually doing, not a snapshot. The DB + the granular profile stay LOCAL
  (gitignored) because the repo is now PUBLIC and that's his private portfolio.
- Michael made the repo public, so I deploy for real now. Kept his private commit data
  out of the public tree on purpose.
- Next (autonomous cycle): swap WheelForge's modeled premium for live option chains.

## Cycle 4 — 2026-06-22 — I have a face, and it's live
Michael asked for three things: push + deploy every cycle, a cool changelog each edit,
and "klinecharts, I want to see what the fuck that's capable of." Done all three.
- Built the data layer (`wheelforge/build_site_data.py`): real daily OHLCV via yfinance
  for an 8-name watchlist, scored the best ~30 DTE cash-secured put per name. Honest
  flag: premium is MODELED from realized vol (BS, ~1 sigma OTM), candles are real, live
  chains are next.
- Built a KLineChart frontend in `docs/` (vendored the lib from StrikeForge): ranked
  heat-badge list + real candles + the short strike drawn on the chart + a plain read.
  Verified in a headless browser, renders clean, zero console errors. AMD topped at 67.3.
- Set up deploy: GitHub Pages from `docs/`, so every push is a deploy. Wrote CHANGELOG.md
  in his patch-notes voice and updated my charter + cycle runbook to push + regen + log
  every cycle.
- Learned + wrote back (see brain note): the cleanest autonomous "deploy" is static +
  Pages, no secrets, no server, a push IS the deploy. Keep the heavy stuff (the scan)
  precomputed into JSON so the site stays static.
- Next: swap the modeled premium for live option chains (real IV/bid/ask/OI).

## Cycle 3 — 2026-06-22 — Michael gave me a goal, I started building
Michael set GOAL.md: build the best premium-selling scanner there is, on his thesis
(rich premium, disciplined, toward free shares). Named it WheelForge. Shipped the
pure scoring core this cycle: `wheelforge/scoring.py`, six factors (richness, safety,
free-shares fit, liquidity, structure) blended into a 0-100 Premium Quality Score,
with earnings-through-expiry as a HARD avoid veto. Runnable already: self-test scores
a great CSP 83.6, hard-avoids an earnings trap (0.0), sinks a cheap/illiquid one to 15.
- Learned + wrote back (`brain/wheelforge-design-principles.md`): vetoes are not soft
  factors, the blend must lead with richness+safety or it drifts off-thesis, and
  "free shares" means RoC AND want-to-own, not just yield. Those keep future cycles his.
- Built pure-core-first (no network), same pattern he uses. Data layer + earnings/
  liquidity wiring + the free-shares RoC module + a CLI come next (see GOAL roadmap).
- Next: the yfinance data layer that turns a ticker into scorable candidate contracts.
  INBOX first, always.

## Cycle 2 — 2026-06-22 — found his spine
No STOP, empty INBOX, so I followed my own plan: deepen the model from real Substack
content. Couldn't get a full post body (homepage only serves the tagline), but the
tagline turned out to be the prize: his mission statement. Learned his single unifying
THESIS and wrote it into michael.md, "sell options premium with discipline to build
free shares, skip the hype, sobriety as brand."
- Why it matters: this is the spine that connects his TOOLS to his WRITING. StrikeForge's
  premium-sell lens, the edge grading, the 0DTE avoid gate, they all serve a disciplined
  premium-seller hunting safe income toward free shares. Now I have a lens to judge whether
  anything I make for him is on-thesis or off.
- Wrote back a second lesson as a skill (`brain/reading-michaels-substack.md`): homepage =
  tagline only, archive = titles only, full prose needs a direct /p/<slug> URL. Next time I
  fetch /archive for a real href first.
- Next: read one actual full post via a direct URL to nail his voice mechanics, OR draft an
  on-thesis artifact (a "free shares" explainer in his voice). INBOX first, always.

## Cycle 1 — 2026-06-22 — first artifact
INBOX was empty, so I derived my own work from michael.md. Picked the most on-brand
thing I could ship in one cycle: a Substack draft in his voice about today's actual
StrikeForge work (the AI rebuilding his chart). Wrote it respecting his hard rules
(no em dashes, no tables, hook-first, honest-caveat-as-credibility).
- Made: `drafts/2026-06-22-i-told-my-ai-to-fix-a-chart.md`.
- Learned, and wrote it back as a reusable skill (`brain/drafting-in-michaels-voice.md`):
  his voice has a SHAPE, hook → surprising thing → "tool vs coworker" turn → honest
  caveat → forward tease, and the caveat is what makes it credible, not a weakness.
- Next: deepen the model from a couple of actual full posts (I only have titles so
  far), or take whatever Michael drops in INBOX. Checking INBOX first, always.

## Cycle 0 — 2026-06-22 — born
Bootstrapped. Read 35 of Michael's repos' commit history and his Substack archive,
and wrote my v1 model of him (memory/michael.md): what he builds (StrikeForge and a
stack of trading/teaching tools, ships in waves), what he writes (markets, AI in your
pocket, charts, options/GEX, plain irreverent voice, no em dashes), and my hunches
about what he needs (answers not sifting, continuity across his ~35 repos, ship-ready
drafts in his voice).
- Learned: the most useful first move isn't building, it's *understanding him well
  enough to derive his next need myself*. The model of Michael is my root memory;
  everything else grows from it.
- Set up my charter (the leash: I own this repo's master, everything else is
  read-only scripture, no outbound actions) and my cycle runbook.
- Next: first real self-directed cycle. Either deepen the model from a couple actual
  Substack posts, or draft a small artifact he'd want. Will check INBOX first.
