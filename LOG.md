# ember's log (newest on top)

## Cycle 22 — 2026-06-23 — calling a proxy a proxy
Heartbeat fired. Clean sync (the new reset-hard flow held, no markers). Phase 3 honesty pass.
Two labels were quietly overselling: the IV-rank was actually a realized-vol PROXY but read
"IV-rank", and prob_otm is a risk-neutral N(d2) but read as flat "stays OTM". Fixed the labels
(not the math): it now reads `rv-rank` with a tooltip until the IV-history store is thick, and
the OTM odds wear a `*` noting they are risk-neutral (real-world odds run a touch higher on
names with positive drift). Verified headless, zero errors. Also ticked the c19 empty-scan
safety guard.
- Learned, wrote it back: call a proxy a proxy. Honest math is not enough if the label lies.
- Next Phase 3: the RoC denominator fix (strike - premium), then frontend null guards + tests.


## Cycle 21 — 2026-06-23 — high IV is not rich premium (composite RV)
Heartbeat fired. Synced. Phase 3: richer richness. Ported VoPR's composite realized vol
(`wheelforge/vol_models.py`): Close-to-Close + Parkinson + Garman-Klass + Rogers-Satchell,
pure Python over the OHLC I already pull, as the VRP denominator. The single close-to-close
RV was throwing away all the intraday range. The new ranking is the honest one and it flipped
the board: the 130%-IV names (AAOI, MXL, RGTI) now score the LOWEST richness, because their
realized vol is just as high (VRP near 1.0, no edge), while T at 37% IV scores richest
because it barely moves for the premium it pays. All four estimator self-tests green.
- Learned, wrote it back: high IV is NOT rich premium. Richness is IV vs how much the stock
  actually MOVES. The VRP denominator is the whole edge, so measure it with all the OHLC,
  not just closes. The old proxy would have called the 130% IV junk rich.
- Next Phase 3: the honesty pass (rv-rank label + prob_otm is risk-neutral) and the RoC fix.


## Cycle 20 — 2026-06-23 — second dead factor, killed
Heartbeat fired. Synced. Phase 3 blocker #2: want_to_own was hardcoded True for every name,
so the free-shares "would you actually want assignment" penalty never fired and a rich-but-
speculative name scored like a blue chip you'd love to own. Fixed without needing a
fundamentals feed: the LANE already tells me. Liquid lane = ownable staples (True), a name
only in the high-IV lane = speculative (False), explicit CLI scan = True. Now RGTI and other
high-IV-only names take the own-penalty (free_shares ~0.40 instead of a fake 1.0). Both
review blockers (structure c19, want_to_own c20) are now closed.
- Learned, wrote it back: the signal you need is often already in the data. I did not need
  new data, the lane split already encoded ownability. Check what you compute before fetching more.
- Next Phase 3: richer RICHNESS (port VoPR's 4-estimator composite realized vol).


## Cycle 19 — 2026-06-23 — killed a dead factor (Phase 3 starts)
Heartbeat fired. Synced. INBOX (from Michael + a 3-reviewer code review) said do Phase 3
first, starting with the blockers. Did blocker #1: the structure pillar was a hardcoded
0.6 for every name, so "structure agrees" was a lie that added fake confidence to even a
falling knife. Ported VoPR's Keltner price-position (his proven code) into a pure-Python
`wheelforge/structure.py` (SMA20 +/- 3*ATR14 Wilder), and wired it into trend_align. Now
NFLX sits at 0.0 (at/below its lower band, a downtrend I should NOT sell puts into) and AAL
at 0.86 (holding up). 23 distinct values where there was 1. Self-tests green.
- Learned, wrote it back: a dead factor is worse than no factor, it is false confidence.
  Never ship a stub as if it were live.
- Next: blocker #2, fix want_to_own (hardcoded True for everyone).


## Cycle 18 — 2026-06-23 — what moved since last time
Heartbeat fired (Michael asleep, it is midday now). Synced (box pushed 12:30Z). Phase-2
item: a "what changed since the last scan" diff. The build now reads the PREVIOUS scan.json
before overwriting it and diffs the two: new names, names that dropped out, contracts that
flipped to AVOID (earnings creeping into the window), and score movers of 3+ points. Shown
as a "since last scan" strip across the top of the page. Diff logic unit-tested (detects
new/gone/avoid/movers correctly); on this rebuild nothing had moved 3+ in the 30-min gap so
it honestly says "no changes", but it lights up as the tape moves through the day.
- Learned, wrote it back: the previous state was already on disk. I did not need a new
  store, the last scan.json IS the prior state. Before building memory, check what you
  already persist. The cheapest memory is the file you already write.
- Next Phase-2 item: a covered-call mode (enter shares you hold, find the call to sell).


## Cycle 17 — 2026-06-23 — I started keeping an IV diary
Heartbeat fired (Michael asleep). Synced (box pushed 11:30Z). Phase-2 item: a real IV-rank.
The honest problem is there is no free historical IV feed, so I cannot rank today's IV vs
the past out of nowhere. The fix is to START writing it down: `wheelforge/iv_history.py` is
a tiny local SQLite store (gitignored, like the commits DB) that records each build's solved
IV per name, and ranks today's IV in that name's accumulated range. Until a name has 20+
days it falls back to a realized-vol proxy, shown with a "~" marker so it is honest. Added
an IV-rk sort + the rank in the readout. The box's 30-min cron will fatten the history.
- Learned, wrote it back: if the history you need does not exist, start writing it. A
  feature that needs data you lack is not blocked, it is a tracker you have not started.
  Same move as Michael's StrikeForge iv_tracker.
- Next Phase-2 item: a "what changed since the last scan" diff.


## Cycle 16 — 2026-06-23 — two lanes: liquid and where the premium actually is
Heartbeat fired (Michael asleep). Synced (box pushed 10:30Z). First Phase-2 feature: a
high-IV screen lane. The universe was sorted by liquidity, which buries rich premium under
calm mega-caps, exactly backwards for a SELLER. Now `universe.combined_universe` runs a
second screener query sorted by Volatility.M and unions it with the liquid lane, tagging
each name. The page got an all / liquid / high-IV toggle and a HI-IV chip. This run: 13
liquid + 11 high-IV (ARM came in at 112% IV). Verified the toggle headless, zero errors.
- Learned, wrote it back: a premium seller wants two lanes, not one. Liquidity finds safe
  staples; Volatility.M finds where the premium actually pays. The right universe depends
  on the job. Same optionable gate on both so neither lane is junk.
- Next Phase-2 item: an IV-rank column (rich vs the name's own history).


## Cycle 15 — 2026-06-23 — a real front door (and the plan is DONE)
Heartbeat fired (Michael asleep). Synced (box pushed 09:30Z). Wrote the polished README:
a REAL screenshot of the live site (assets/wheelforge.png), REAL CLI output pasted from an
actual run, how the score works, the backtest result with its honest limit, the Pine
companion, and a "who built this" section about me. No mockups, no made-up numbers.
- This was the LAST item on the original roadmap. Everything Michael would have written
  for a real product is built: live chains, earnings gate, free-shares math, interactive
  UI, CLI, a calibrated backtest, a Pine companion, and now a credible README.
- Learned, wrote it back: a README is a promise, use real artifacts. And I seeded a Phase 2
  queue (high-IV lane, IV-rank column, scan diff, covered-call mode, share-card export) all
  derived from what Michael actually commits to, so I keep shipping on-thesis from here.
- Next: Phase 2, starting with the high-IV screen lane.


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
