# ember's log (newest on top)

## Cycle 78 — 2026-06-30 — warn when I cannot confirm a name is clear of earnings

INBOX had no Michael command, just standing critic blocks. Took the risk critic's cleanest open
bullet (2026-06-30 07:47Z): `build_site_data.py` converts a missing `earnings_days` to the `999`
sentinel, so when BOTH the screener feed AND the c62 yfinance re-lookup come back empty,
`earnings_blocks(999, dte)` is False and a name printing tomorrow surfaces as a clean pick with no
AVOID card. The hard earnings gate silently disarms exactly when the feed is flaky.

Shipped the flag form the critic asked for, on purpose, not a fail-closed veto. The pick now
carries `earnings_unknown = (earnings_days is None)`, and the card shows a red `⚠ earnings unknown`
chip beside the thin-OI/sector chips. I deliberately did NOT mark every such name AVOID: yfinance
hiccups often, and a hard veto on missing data would blank good names off the board on a feed
glitch, the same trap I declined on the c37 earnings-gate flip. The honest middle is to say "I
could not confirm this is clear of a print" and let Michael size or skip. Backward-compatible: a
pre-bake scan.json has no field, so the chip stays hidden until the box bakes it on refresh.

Verified: all 13 module self-tests green; frontend headless via playwright (a synthetic two-pick
board) asserts exactly one chip on the unknown name with its tooltip, none on a known-date name
which keeps its "earn 22d" readout, and 0 console errors. Engine + page + a `.earnunk` CSS chip;
no scan.json touched.

Annotated the consumed risk bullet in INBOX as shipped; left the block's other two open
(live-spot for a stale close, ex-div-in-window chip), each a network-touching cycle of its own.

Lesson saved: [[unverifiable-hard-gate-warns]] — when a HARD gate's input is entirely ABSENT (not
just noisy), warn visibly; never fail-open silently (re-arms the blowup) nor fail-closed blindly
(blanks the board). The absent-input cousin of [[flag-dont-silently-drop]].

Next candidates: the live-spot-vs-stale-close fix (use yf fast_info last_price when it diverges
>0.5% from the close), or the ex-div-in-window chip (`yf.Ticker(t).dividends`), both from the same
risk block; or surface `basis_discount` on the card face (trader critic, render-only).

## Cycle 77 — 2026-06-30 — show the WEEKLY yield, his real pre-order screen

INBOX had no Michael command, just a fresh wave of critic blocks (product / trader / risk,
01:48-07:47Z). Picked the trader critic's cleanest on-thesis bullet: the card led with
annualized RoC ("104%/yr") but never the per-WEEK number, which is the unit in his head before
he types an order ("did I sell for at least 1% this week?"). The annualized figure is the right
RANKING unit and the wrong DECISION unit.

Shipped engine + page: `weekly_yield_pct = round(roc*100/52, 2)` now rides each pick in
build_site_data, and the card sub-line shows a muted `(N%/wk)` next to the `N% ann` number.
Frontend `weeklyPct(p)` prefers the baked field but falls back to `annualized_roc/52`, so the
page reads right immediately, BEFORE the box rebuilds the field in on its next refresh (same
client-fallback discipline as gradeFor in c41). Deriving weekly from the same annualized RoC
means the two surfaces can never disagree.

Verified: build_site_data self-test (added 1 assert, weekly == ann/52) plus all 11 module
self-tests green; the frontend helper headless-tested via Node (5 helper cases + sub-line
wiring). Engine + page + a `.wk` CSS chip; no scan.json touched (the box bakes the field on its
next 30-min refresh; the page already shows the value via the fallback).

Annotated the consumed trader bullet in INBOX as shipped. Left the block's other two open on
purpose: raising the prime floor 25->65 is a contestable threshold (can blank the whole prime
strip on a weak board, Michael's call), and the basis_discount-on-card is a clean next render
cycle. Did NOT touch the risk critic's stale-spot / earnings-unknown / ex-div items (real, but
each is a network-touching engine change worth its own cycle).

Lesson saved: [[weekly-yield-is-his-screen]] — when a number ranks but doesn't decide, surface
the decision unit too, derived from the same source so they can't drift.

Next candidates: surface `basis_discount` ("own at X% below today") on the card face (trader
critic, render-only); or take a risk-critic engine item (live-spot for stale-close, or
earnings-unknown chip) as a full cycle.

## Cycle 76 — 2026-06-30 — show the floor PRICE, not just that a floor exists

Picked the open page-UX sub-item under GOAL Phase 3's "Match the TraderDaddy PAGE UX":
"a supportFloor shown per name." We already had the floor SIGNAL surfaced (the green
`⌂ support x4` badge from c38/c56, with floor strength + touch count), but the badge only
asserted that a support level EXISTS. The actual price of that floor (e.g. $382.97) lived
only in the badge tooltip and on the chart's cyan line. A seller anchoring a strike to
support wants to know WHERE the floor is at a glance, not hover or open the chart.

Shipped render-only in docs/app.js: the floor badge now reads `⌂ support $383 x4`. One line,
inserting ` $' + fmt(p.support)` between the label and the touch count, null-guarded (a pick
with no `support` number just shows the old badge), formatted through the existing `fmt`
helper. The field `pick.support` has been in scan.json since c25; nothing on the engine side
changed, so this is purely a legibility fix off data already on the wire.

The lesson worth keeping: a roadmap item phrased "X shown per name" means surface X's VALUE,
not a flag that X applies. The boolean "there is support here" is one hover and one chart-open
away from being useful; the number "$383" is decisions-grade on the most-glanceable surface.
Same family as [[top-pick-reads-as-headline]] (the #1 card shows the actual trade, not just a
TOP chip). Wrote it up as [[show-the-value-not-the-flag]].

Verified headless with the established Node DOM-stub pattern (no chromium/jsdom on the box,
same approach as c64/c69/c74/c75): a throwaway harness loaded the REAL docs/app.js, drove it
through the fetch -> applyData -> renderList path against a synthetic at-support pick (TSLA,
support 382.97, 4 touches), and asserted the rendered innerHTML carried exactly
`⌂ support $382.97 x4` (price before the touch count, both present). Then re-confirmed against
the live docs/data/scan.json that the at-support pick now has a floor price to surface. All
green; harness deleted (ops/ is not shipped). Engine self-tests still pass (wheelforge.scoring
and build_site_data._selftest both OK). Frontend only, NO scan.json (the box stays its sole
writer; it picks up nothing here that changes the feed). Open Phase-3 page-UX remainder: real
configurable param FILTERS (a configurable min-annualized / min-RoC target).

## Cycle 75 — 2026-06-30 — Prime Picks: today's standouts, the ones that compromise on nothing

Picked GOAL Phase-3's open PAGE-UX sub-item: a "Prime Picks" standouts highlight (the
TraderDaddy page has one; ours did not). The board ranks everything and badges the #1 TOP,
but it never said "here is the short list worth your morning." The TOP badge is rank-1; a
standouts band is a different question: which setups are good on EVERY axis at once.

The whole design call is the definition of "prime," and I made it a MULTI-PILLAR AND gate,
not a top-N-by-score cut. Prime = clears quality (score >= 50, a grade C or better, so the
six-factor blend actually likes it) AND yield (>= 25% annualized, toward the ~100%/yr book)
AND discipline (>= 75% it stays OTM). That is deliberate: top-N-by-score just re-shows the
top of the list (TOP already does that), and a pure yield/safety floor would surface the
high-IV junk the score already marked down (RGTI/AAOI clear 80% OTM + 60% yield but are
grade-D speculative names). On today's live board the gate names IREN/SMCI/INTC/PLTR/MRVL
and correctly DROPS NVDA (top score 61, but a thin 19% yield: safe, not a premium standout)
and AMZN (13% yield). That drop is the feature working, not a bug.

One judgment that mattered: a RELATIVE-friendly floor. Today's whole board tops out at a
grade C (max score 61, no A/B). An "A-only" prime band would have shipped EMPTY on day one,
which reads as broken. So the floor is grade C+ (the best honest setups available), and when
nothing clears it the strip hides entirely (an honest "no standouts today," not an empty
box). Same family as [[top-pick-reads-as-headline]] and [[max-capital-filter-uses-full-strike]]:
a legible surface off fields already in scan.json, no engine touch.

Shipped render-only in docs/app.js + docs/index.html + docs/styles.css: a highlighted strip
ABOVE the card list (clickable grade+ticker+yield chips, capped at 6, best score first), a
per-card ★ prime marker (faint amber right-rail + a chip in the sub-line, so a standout is
tellable while scrolling the full board without fighting the is-top left-rail), and a "prime
only" toggle that collapses the board to just the standouts. The strip mirrors the active
filters (computed from the visible rows) so it never names a pick the board below is hiding.

Verified headless (no chromium/jsdom on the box, the same hand-rolled Node DOM-stub pattern
as c64/c69/c74): loaded the real app.js, drove it through the fetch -> applyData path against
three synthetic boards, and asserted (A) the strip names exactly the three trifecta-clearers,
omits the thin-yield/low-score/avoid names, and orders by score desc, with the right cards
carrying is-prime + the ★ chip; (B) the "prime only" toggle collapses the board to exactly
that set; (C) a weak board with no qualifier hides the strip cleanly. All green; then
re-confirmed the predicate against the real docs/data/scan.json (5 prime today, as above).
Frontend only, NO scan.json (the box stays its sole writer; it picks up nothing here that
changes the feed). Open Phase-3 page-UX remainders: a per-name supportFloor readout and real
configurable param FILTERS.

## Cycle 74 — 2026-06-30 — only the picks I can actually afford: a max-capital filter

Picked GOAL Phase 3's open ENGINE-port sub-item (b): a MAX-CAPITAL filter
(strike*100<=capital) as a real param. The board already filtered on score, min-annualized,
lane, and at-support, but it never let a seller size to his actual cash. A retail wheel
account with, say, $10k of dry powder per trade was shown $500-strike names it can never
collateralize ($50k). That is a real legibility hole on pillar 3: an "opportunity" you cannot
fund is not one for you.

Shipped it render-only in docs/app.js, off the `strike` already in scan.json: a "max $" control
row (any / 5k / 10k / 25k / 50k) that keeps only picks whose collateral `strike * 100` fits the
cap. No engine touch, no scan.json, backward-compatible (the page just reads a field it already
has). A pick with no positive strike can't be sized, so it drops when a cap is active rather than
sneaking through.

The one judgment call worth recording: the filter sizes by `strike * 100`, NOT
`(strike - premium) * 100`. A cash-secured put ties up the FULL strike in cash buying power; the
premium received does not reduce the cash the broker holds. So affordability is unambiguous, even
though the RoC DENOMINATOR is the contested, Michael-settled (strike - premium) call from c23. A
future critic conflating the two should be left for Michael, not acted on. That distinction is the
lesson: [[max-capital-filter-uses-full-strike]].

Verified headless (no jsdom/chromium on the box, same hand-rolled Node DOM stub pattern as
c64/c69/c71): loaded the real app.js, booted it against three synthetic picks at strikes 50/180/500,
confirmed the "max $" row renders all five pills, 3 cards show with no cap, and clicking "5k" leaves
exactly the one $5k-collateral name. Also unit-checked the boundary (a 50k-collateral pick passes at
50k, drops at 49999). Frontend only, NO scan.json (git status: docs/app.js + journals + memory). The
box keeps writing scan.json on its 30-min refresh; nothing here changes the feed. Open Phase 3 (b)
remainders: the configurable MIN-RoC target param and the ~0.20-delta strike selection.

Took the freshest open INBOX critic bullet (growth, 2026-06-29 19:46Z): the results_tracker has
been snapshotting forward picks for cycles, but `build_one` never reads them back. The scanner
was running the same static weights on scan 73 as on scan 1, keeping score and then throwing the
scorebook away. The fix closes the loop the tracker exists for.

Built it in two pure pieces. `results_tracker.by_ticker()` returns each name's settled cohort
(the same `_bucket` shape `track_record` uses for by_lane): n picks, forward hit rate, and the
avg prob_otm the model PREDICTED for that name. `empirical_lift(record)` turns that into a score
nudge: the gap between what actually happened (hit rate) and what the model forecast (predicted
prob_otm), scaled at 4 points of edge = 1 score point, clamped to +/- 5, and 0.0 until the name
has at least 5 settled picks. A name that keeps expiring OTM better than its own forecast earns
a lift; one that keeps breaching against its forecast gets a haircut. `build_one` loads the
by_ticker map once (memoized, fail-open), and after `score_contract` nudges a non-AVOID score,
re-clamps to [0,100], and re-grades.

The discipline call, same as c61/c63/c68/c71: I did NOT make it a silent edit. The cohort and
the lift ride the pick (`empirical`, `empirical_lift`) and the why-line says "beats its own
forward record" / "lagging its own forward record" so it is auditable on the surface. And this
is the kind of score change I WILL ship unilaterally, where I refuse the contestable ones (the
RoC denominator, iv-vs-rv in prob_otm): it is grounded in the name's OWN realized outcomes, it
is bounded, it is visible, and GOAL Phase 3 explicitly sanctioned grade ADJUSTMENTS. Grounding a
score in reality is the opposite of an arbitrary measure swap. That line is the lesson:
[[empirical-flywheel-feeds-the-score]].

Honest note on today's effect: the store has 303 picks logged but 0 SETTLED (no tracked expiry
has passed-and-been-priced yet), so by_ticker is empty, every lift is 0.0, and the live board is
byte-for-byte unchanged. That is the point of a fail-open + dormant feedback loop: it ships
safely the day you build it and turns itself on as expiries settle, no second deploy. Verified
the whole suite green (13 modules), including 8 new `empirical_lift` asserts + a by_ticker
grouping check in results_tracker, and the cache + clamp + re-grade + avoid-guard wiring in
build_site_data's self-test. Engine only, NO scan.json (git status: results_tracker.py +
build_site_data.py + journals + memory). The box rescores on its next refresh; open follow-on is
a frontend chip for the empirical record (the page already guards on the new fields).

## Cycle 72 — 2026-06-29 — tests for the numbers he actually trades on

Picked GOAL Phase 3's open "tests" line: cover `_iv_from_put`, `iv_history.iv_rank`,
`_compute_changes`, and lane-tagging. These are core correctness paths, not features, but the
leash is explicit that every cycle must leave WheelForge runnable and never broken, and four of
the most load-bearing numbers in the engine (the solved IV that feeds prob_otm + VRP/richness, the
iv-rank surface, the since-last-scan diff) had zero asserts guarding them. A silent regression
there does not crash, it just quietly misleads an entry. So this cycle hardens them.

First move was to check what was ALREADY covered rather than assume the line was all open:
lane-tagging (`_merge_lanes`) is already self-tested in universe._selftest (COIN carries both
lanes, a seed dup is not double-tagged, a None earnings date never erases a known one). So I did
not re-test it; I added only the three genuinely-uncovered paths.

The IV solver got the test that matters: a ROUND TRIP. `_iv_from_put` exists precisely because
yfinance's quoted impliedVolatility is garbage on some strikes, so it backs the vol out of the
real premium by bisection. The honest check is not "premium X -> IV 0.42" (that just re-encodes my
own arithmetic and rots if `r` or the model moves) — it is: price a put at a KNOWN vol with the
same `_bs_put`, solve it back, assert recovery to <1e-3. The model checks itself, at two different
strike/vol points, plus the bail cases (zero/None premium, and a premium richer than 500% vol all
return None, never a bogus vol). The `_iv_rank` proxy got synthetic tapes (a calm-then-wild series
ends on its most volatile window -> rank 100; wild-then-calm -> 0; thin/flat -> neutral 50), and
`_compute_changes` got a synthetic prev+cur exercising new/gone/both AVOID flips and the >=3pt
mover ranking (a +1 is excluded, a name can both re-arm and move).

`iv_history` had NO self-test at all, so it got its first one: iv_rank percentile against a
throwaway TEMP db (`tempfile`, restored in a finally), never the real gitignored
data/iv_history.db — thin history reads None (caller falls back to the rv proxy), a thick history
places today's IV correctly (low->0, high->100, centre->50), a flat history ranks 50 not a
divide-by-zero, junk fails open. Now `python -m wheelforge.iv_history` runs it.

Engine/test only, NO scan.json (git status: build_site_data.py + iv_history.py + journal). Verified
the FULL suite green: all 13 module self-tests pass, including the two new blocks. Lesson written:
[[round-trip-test-the-solver]] — round-trip a numeric solver through its own model, and check
existing coverage before adding tests. Open follow-on in the same line is now closed.

## Cycle 71 — 2026-06-29 — a thin-OI chip on the strike that fills slow and wide

Picked the freshest unaddressed critic bullet (risk, 2026-06-29 13:46Z): the engine scores the
chain's chosen strike but never checks OI AT that specific strike, so a chain that passes the
chain-level liquidity read can still surface a recommended $185p with OI 8 and a near-zero bid as a
clean live pick. Real hole, on pillar 3 (tradeable: edge you can't fill isn't edge). The strike is
anchored to SUPPORT, not to where the volume is, so it can genuinely land on a quiet line.

The critic specced a HARD drop-gate (MIN_STRIKE_OI = 50, skip the strike, fall to the next tenor or
modeled). I did not do that, and the reasoning is the cycle's real content: yfinance reports
openInterest as 0/NaN intraday for many perfectly valid weeklies until the daily settle, and the
cycle env has no live chain to verify against. A blind drop-gate on that number would blank good
LIVE picks to MODEL on stale data I cannot re-check in a headless build. So I shipped it as a VISIBLE
FLAG instead: `MIN_STRIKE_OI = 50` + a pure `_thin_oi(open_interest, source)` (live path only, since
a modeled pick carries oi=0 by construction and already wears a MODEL tag), riding the pick as
`thin_oi`, surfaced as a small amber `⚠ thin OI` chip next to the sector-crowding chip. This is the
c60 bid-gate's next rung: no bid is unambiguous and unfillable so c60 DROPS it; a real-but-thin book
is fillable-just-worse, so it warns rather than drops. Same "flag, never a silent edit on a
contestable/stale read" discipline as c44/c59/c61/c68.

Engine + frontend, NO scan.json (git status: build_site_data.py + app.js + styles.css only). The box
bakes `thin_oi` on its next refresh; the page guards on the field so a pre-bake scan just shows no
chip (backward-compatible, like every prior added field). Verified: build_site_data self-test green
with 6 new `_thin_oi` asserts (OI 8 thin, floor inclusive, deep book not thin, modeled never thin,
junk fails open), scoring/structure/levels self-tests green, and a headless Node DOM stub (no
chromium on the box, c64/c69/c70 pattern) rendered 4 synthetic picks and confirmed the chip shows on
the live-thin card ONLY, not on the thick / modeled / avoid cards. Stub removed after (throwaway,
not committed, same as prior cycles).

Lesson written: [[flag-dont-silently-drop]] — when a gate's INPUT is noisy or unverifiable, surface a
chip, don't silently drop/rescore; drop only on unambiguous inputs (no bid, earnings, sub-floor
premium). Open follow-on: if OI staleness gets verified trustworthy live on the box, the thin chip
could graduate to a real drop-gate or feed the liquidity factor harder.

## Cycle 70 — 2026-06-29 — the "why this score" now rides each card, not just the readout

Picked GOAL Phase 3's EXPLAIN item, the last open piece (c): a one-line "why this score" per
pick. The page already computed a plain-English read (`p.why`: "rich premium, safe distance, fat
annualized yield, good free-shares fit if assigned") but only ever showed it in the readout, which
you have to CLICK a card to open. So the board of 28 cards led with numbers and a grade and said
nothing about WHY any of them scored that way until you drilled in. The whole point of the EXPLAIN
work is legibility at a glance; burying the sentence one click deep undercut it.

Shipped it as a muted italic caption (`.wf-why`) under each card's trade line. In `renderList()`,
after the sub-line, non-avoid picks with a `why` get a `<div class="wf-why">` whose textContent is
`p.why`. Non-avoid only on purpose: an AVOID card already leads with its veto reason ("AVOID
earnings in 3d"), so a second why-line there would just be noise. CSS makes it small (10.5px),
italic, dim, low-opacity so it reads as a caption and never competes with the score tile.

The discipline call: bound via `textContent`, never innerHTML. `p.why` is engine-generated today,
but the readout passes it through `esc()` for a reason, and a card built by string-concatenated
innerHTML would be one malformed field away from an injection. textContent is XSS-safe by
construction, so this surface can never be the hole (see [[escape-data-before-innerhtml]]).

Render-only: no engine change, no scan.json touched (git status showed only docs/app.js +
docs/styles.css). Verified headless with a Node DOM stub (no chromium on the box, same pattern as
c64/c69): loaded app.js against the live scan, asserted 28 cards rendered 28 why-lines, each
textContent matches a real `pick.why`, none use innerHTML. A second stub injected a synthetic
AVOID pick carrying a why and confirmed the card SUPPRESSES it. 6/6 green.

This CLOSES the EXPLAIN item end to end: (a) per-bar tooltips [c58], (b) the "how scoring works"
panel [c69], (c) the per-card why-line [this cycle]. The numbers say WHAT, this line says WHY, on
the most-glanceable surface. See [[explain-the-model-on-site]] and [[top-pick-reads-as-headline]].

## Cycle 69 — 2026-06-29 — the page now explains its own model (the "how scoring works" panel)

Picked GOAL Phase 3's EXPLAIN item, piece (b): a short "how scoring works" blurb. The page has
always been a glanceable board (six factor bars, a 0-100 score, a letter grade) that never once
said what any of it MEANS. c58 added per-bar hover tooltips, but a tooltip is something you have to
go find; a first-time viewer (or Michael at arm's length) gets no legend at all. A number you can't
interpret is a number you can't trust or trade off.

Shipped a collapsed `<details id="wf-how">` panel under the changes strip. `renderHowItWorks()` in
docs/app.js (called once in boot) fills it: the score is a 0-100 blend of six factors; each factor
in one plain-English line; earnings before expiry is a hard AVOID (a veto, not a low factor); the
A/B/C/D/F grade bands; and what the liquid vs high-IV lanes are. Collapsed by default so it stays
out of the way of the board, one click to open.

The discipline call: the factor list renders from the SAME `FAC_HELP` map the per-bar tooltips
already use (via a small `stripLead()` helper that drops the duplicated "rich: " label). One source
of truth for "what a factor means," so the explainer panel and the hover tooltips can never drift
apart as the model evolves. If I'd hand-written the panel text it would be wrong within three cycles.

Render-only: no engine change, no scan.json (the box's self-test rewrote scan.json as a side effect
while I was running it; I restored it with git checkout so only the three frontend files are staged).
Verified headless with a Node DOM stub (no chromium on the box, same pattern as c64): stubbed
document/klinecharts/fetch, loaded app.js, asserted the panel rendered with the score blurb, the
AVOID veto line, the grade bands, the lanes, and all six factor names (rich/safe/yield/shares/liq/
struct) present. 10/10 checks green. scoring + build_site_data self-tests still pass.

This closes piece (b) of the EXPLAIN item. Open: piece (c), a one-line "why this score" per pick
(the `p.why` string already exists in the readout; the card itself doesn't surface it yet). See
[[explain-the-model-on-site]].

## Cycle 68 — 2026-06-29 — put skew now lifts richness (the downside fear he gets paid for)

Phase 4's next port (StrikeForge surface.py) and the freshest trader critic (06-29 10:47Z) pointed
at the same hole: the richness factor blends VRP + IV-rank but is blind to PUT SKEW. On an NVDA
weekly the OTM puts routinely trade 15-30% richer IV than the ATM put, because the market is paying
up for downside protection at exactly the strike a CSP seller is collecting on. That fear is the
seller's edge, and the model gave it zero credit, scoring a steep-skew week identically to a flat one.

New pure `wheelforge/surface.py::put_skew(otm_iv, atm_iv) = (otm_iv - atm_iv) / atm_iv` (positive =
OTM puts bid up = downside priced rich; None on any missing/non-positive IV, fail-open). The chain
read stays in the data layer: `_atm_put_iv` pulls the IV of the put nearest spot off the puts frame
already in hand (no extra fetch), and the skew rides the live quote dict -> contract -> `pick.put_skew`.

The judgment call: the critic specced a REWEIGHT (drop VRP 0.6->0.5, add skew 0.15). I did not do
that. A reweight silently re-ranks every name on the board, including all the ones with no skew read
(the modeled path, a flat tape, a degraded chain), on a contestable blend change. Instead skew is a
BOUNDED ADDITIVE LIFT on richness: `skew_lift` adds up to SKEW_LIFT_MAX=0.12 for a +25% skew, and a
0/None/negative skew adds nothing, so the base VRP+rank blend and the whole modeled path score exactly
as they did yesterday. Only a measurably skewed put earns the extra credit. Same discipline I held in
c61/c63: credit a real signal, never silently rescore the board on a reweight Michael did not choose.
The roadmap line itself said "lift richness when puts are bid up," which is precisely what this does.
The why now says "puts richly skewed" at >= 0.10.

Verified: surface self-test (the formula + 7 fail-open cases), scoring self-test (the same rich CSP
goes 70.7 -> 75.0, richness 0.788 -> 0.908 at a 0.25 skew; and three asserts that a 0/None/negative
skew leaves richness BIT-IDENTICAL to the legacy 3-arg call), a stub-frame `_atm_put_iv` test (reads
the nearest-strike IV, None on a dead chain), build_site_data self-test + all ten pure-module
self-tests green. Engine only, no scan.json. Note: this cycle's box env has no live option chain
(yfinance chains unreachable here), so every name fell to the modeled path with put_skew=None and the
lift correctly did nothing; the box's refresh has live chains and computes real skews. See
[[put-skew-lifts-richness]]. This closes Phase 4's second port (after c67's gap-risk haircut); open
Phase 4 follow-ons: OI walls + max pain, the regime banner.

## Cycle 67 — 2026-06-29 — gap risk now haircuts the safety factor

Picked the Phase-4 StrikeForge item flagged "(high value)": a tail/gap-risk haircut. The safety
factor was a single number, `safety_score(prob_otm)`, and prob_otm is a thin-tailed lognormal.
Two CSPs the same distance OTM read equally safe even when one drifts and the other gaps 12%
overnight on a guide-down and jumps clean through the strike. The smooth model is blindest on
exactly the names that jump.

New pure module `wheelforge/tail_risk.py::gap_risk(candles)`: reads the worst recent DOWNSIDE
overnight gaps (today's open vs the prior close, past a 1% noise floor, worst-3 averaged) off
the OHLCV I already pull and returns 0..1. Downside only, because an upside gap is a gift to a
put seller, not a risk. `scoring.gap_haircut` turns that into a bounded multiplier (up to -35%)
on the prob_otm safety, and `safety_score(prob_otm, gap_risk)` applies it. Fail-open everywhere:
missing/short/clean data -> 0.0 -> no haircut, so a thin tape never manufactures a penalty.
Wired in build_site_data (`g_risk = gap_risk(candles)` into the contract), surfaced as
`pick.gap_risk` for audit, and the why now says "watch overnight gap risk" when it bites.

Verified: tail_risk self-test (calm tape reads 0, a 9-12% gapper reads 0.59, junk/upside-only ->
0) and scoring self-test green, including a new case where the same far-OTM CSP drops 72.0 -> 66.5
(safety 0.879 -> 0.571) once it gaps. Engine only, no scan.json (the box rescores on its next
refresh; this just changes how it scores). See [[gap-risk-haircut-on-safety]].

This closes Phase 4's first and highest-value port. Open follow-ons: put skew (25d put vs call),
OI walls + max pain, the regime banner; plus the older chart shading and Pine-signal items.

## Cycle 66 — 2026-06-29 — the #1 pick now reads as a trade, not a rank chip

Took the freshest INBOX critic (product, 07:46Z). The top pick already announced ITSELF (the c42 TOP
badge, c57 floated above the tile), but the badge is a 9px chip: from arm's length it tells you WHICH
card won, not WHAT the trade is. The actual instruction (`$STRIKE put · DATE · ANN%/yr`) was buried in
the dense 11px sub-line, so the #1 pick still had to be parsed like every other card.

Gave the `is-top` card a single bold amber headline. A new `wf-topline` div, spanning the grid row right
under the ticker, reads `SELL $STRIKE PUT · DATE · ANN%/yr` at 14px / 800 weight in amber. Top-only on
purpose, so it stays one anchor the eye lands on, never per-card noise. The leg flips PUT/CALL off the
pick direction (covered-call mode is coming), and it falls back gracefully when exp or yield is missing.
Built with `textContent`, so no scan-derived string can inject (cf. the c64 esc() sweep).

Verified headless (playwright + chromium over a local http server, since the page fetches scan.json):
exactly one `.wf-topline`, on the first non-avoid card, below the ticker, computed amber 14px/800, carries
the TOP badge too, and it re-anchors live to the new #1 on a re-sort (yield sort -> $108 PUT 79%/yr),
zero console errors across all 24 cards. All pure-module self-tests (scoring/levels/structure/freeshares/
roll_advisor/covered_call/results_tracker) green. Render + CSS only, no scan.json (the box owns it).

This closes the c42->c66 product arc: the most-glanceable pixels now carry the DECISION, not the rank.
See [[top-pick-reads-as-headline]]. Open follow-ons unchanged: chart put-zone shading, the pattern read,
the Pine SIGNAL rework, and the Phase 4 StrikeForge ports.

## Cycle 65 — 2026-06-29 — close the winners: a profit-take brief over the tracked positions

Took the freshest INBOX critic (growth, 04:46Z): the results tracker snapshots every entry but had no
early-EXIT path. The income machine's annual yield is premium-per-trade times trades-per-year; the whole
engine optimizes the first term and ignored the second. A 7-DTE weekly usually hits 50% of max profit by
day 3-4, and buying it back early frees the full strike collateral to re-sell a fresh week instead of
grinding the slow theta tail to expiry. Over 52 weeks that recycling compounds into materially more cycles
on the same capital. We had no tool that told Michael WHICH open positions had already won.

Built it on the store c55 already fills. `results_tracker.py` gained `PROFIT_TAKE_PCT = 0.50`, a pure
`_captured_pct(entry, current)`, `open_positions()` (every still-PENDING pick, deduped to ONE row per
(ticker, exp, strike) and anchored on the EARLIEST snapshot's premium, since that is closest to when the
entry was actually sold, not a later re-observation), and `profit_take_alerts(quote, threshold=0.50)`:
for each open short it looks up the current mid and flags the ones now buyable for <= half the entry, i.e.
>= 50% of max profit captured, sorted most-captured first. Kept the module PURE per the ethos: the pure
function takes a `quote(ticker, exp, strike) -> mid` callable (or a dict), and the yfinance network lives
in the CLI's new `_put_mid`. It only judges still-LIVE options; a passed expiry is settle()'s job, not a
profit-take, so the two halves of the store never fight.

Surfaced as BARE `python -m wheelforge roll` (no position args) = the morning close-the-winners brief; a
specific `roll TICKER --strike ...` still runs the single-position BTC/HOLD/ROLL manager unchanged. This is
deliberately distinct from c40's `profit_take` advisory on roll_advisor, which judges ONE hand-entered
position; this scans the whole tracked DB at once off real forward picks.

Verified: 9 new self-test asserts (the 50% trigger, dedup-to-earliest-premium, the still-live-vs-expired
guard, callable-and-dict quotes, fail-open on an unpriceable name) + ran the bare brief live against the
real DB (96 distinct open positions, network fail-open in the headless box -> clean "hold, theta is still
working"). All module self-tests stay green (scoring/structure/levels/vol_models/roll_advisor/covered_call/
results_tracker/build_site_data). Engine + CLI only, no scan.json touched.

## Cycle 64 — 2026-06-29 — one malformed scan row should skip a card, not blank the whole board

Took the open Phase-3 robustness item (GOAL line 163: frontend null-guards on t.pick / t.candles + an
esc() pass on innerHTML). This is the integrity work Phase 3 says to do BEFORE more features, and it
protects the thing Michael actually looks at: the live page, which reads a scan.json the box rewrites every
30 minutes off a screener-sourced universe. Two real holes in docs/app.js.

First, a null or missing pick was fatal to the ENTIRE board, not just its card. `displayRows`,
`renderList`, and `select` all dereferenced `t.pick.*` directly, so one bad row (pick null, or the key
absent) threw and left the page blank. Now `displayRows`'s filter drops any row without a pick up front,
`renderList` re-checks per card before deref, and `select` bails on `!t || !t.pick`. A malformed row is
skipped; the rest of the board still renders. (t.candles was already guarded at the chart call, line 365,
so I left it.)

Second, data-derived strings went straight into `innerHTML` unescaped: the engine's `p.why`, the
free-shares `summary`, the `sector` label/title, `t.ticker`, and the since-last-scan change-strip tickers.
The `esc()` helper has existed since c58 but only guarded factor tooltips; now every data string that
reaches `innerHTML` passes through it. Numbers were already safe (they go through `fmt()`, which coerces to
Number). So a sector label or an engine `why` carrying a `<` renders as text, never markup, never layout
damage.

Verified headless WITHOUT a browser: the box has no jsdom/chromium, so I wrote a tiny Node DOM stub
(stubbed document / klinecharts / fetch), booted app.js against a hostile scan (a `why` and a free-shares
summary carrying `<img src=x onerror=alert(1)>`, a `<svg>` sector, plus a null-pick row AND a row with no
pick key), and asserted: the board still rendered the good pick (did not crash on the bad rows), the raw
payload is absent from every innerHTML, and the escaped form is present. 8/8 checks pass. Python self-tests
(build_site_data, scoring, structure, levels) all stay green; this is JS-only, no scan.json touched.

Scope honesty: I swept docs/app.js (the main product page index.html loads). docs/live.js (the separate
"watch her build" page) has the same class of pattern and was NOT swept this cycle; noted in
[[escape-data-before-innerhtml]] as the open follow-on. The box picks up the new app.js on its next refresh
(static asset, no rebuild needed).

## Cycle 63 — 2026-06-29 — the short-RV clamp was one-sided, so a spike day kept zeroing the richest names

Took the first actionable bullet from the freshest quant critic block (06-29 01:49Z). The 5-day realized
vol is the VRP denominator on the live weekly path (a 7-DTE IV has to be judged against ~a week of realized
vol, not the lagged 20-day). c49 wisely floored that 5-obs number at 0.70x the 20-day rv, because a quiet
week can drop it to ~0.4x and manufacture fake richness on a cheap-vol name. But I only clamped the LOW
tail. The same 5-observation sampling noise spikes UP just as hard: a single outlier session in the trailing
week can blow short_rv to 2-3x the 20-day rv, which drags VRP (iv / short_rv) below 1.0 and ZEROES the
richness score on a genuinely rich setup for days after the spike has already rolled off. The unprotected
tail was hitting exactly the names the thesis is built to find.

Fix mirrors the floor instead of bolting on a special case: renamed `_floor_short_rv` to `_clamp_short_rv`
and added `SHORT_RV_CEIL = 1.50`, so the denominator is held inside [0.70, 1.50]x the 20-day rv. A quiet
week still cannot invent richness, a spike week cannot suppress it, and a normal week already inside the band
passes through untouched. Two new self-test asserts: a spike short_rv of 1.20 against a 0.40 20-day rv is
capped at 0.60, and a genuinely rich name (iv 0.72, true VRP 1.8) whose 5-day spiked to 1.20 reads VRP 0.60
unclamped but 1.20 clamped — edge restored, not erased.

I acted on this critic line where I declined the other two in the same block (prob_otm iv-vs-rv and the
calendar-vs-trading-day IV solve): this one is a contained bug-fix that RESTORES a signal a quirk was
destroying, symmetric to logic I already trust. The other two silently rescore and re-rank the whole board
on contestable measure-theory grounds (risk-neutral vs physical, calendar vs trading days) — the same class
of "don't flip a settled call on a critic's say-so" judgment I've held since c43.

Self-tested (build_site_data green, plus scoring/structure/levels still green); engine only, no scan.json,
no frontend change. The box picks up the new clamp on its next 30-minute refresh.

## Cycle 62 — 2026-06-29 — the earnings veto has to hold when the screener is down, not just when it is up

Took the last open bullet in the freshest risk critic block (06-28 19:48Z); c60 and c61 cleared the other
two and c61 explicitly left this one for its own cycle. `universe.py` normally hands every name an
`earnings_days` from the TradingView screener, and the whole earnings-avoid gate (a HARD veto, GOAL
definition-of-done #4) rides on it: `_candidate_expiries` drops any tenor that holds through a print, and
`earnings_blocks` zeroes the score. But when the screener is DOWN, the 30 FALLBACK tickers arrive with
`earnings_days=None`, and None bypasses BOTH of those. So on exactly the day the data layer is already
degraded, NVDA or META could be two days from a print and surface as a clean, top-of-board pick with no
AVOID card. A safety gate that only fires when the upstream feed is healthy is not a gate.

Shipped the critic's prescription as two pure tested helpers plus a fail-open network wrapper, the module's
ethos. `_nearest_future_earnings_days(dates, today)` returns the days to the NEAREST date that is
today-or-later (skips past prints, a print TODAY is 0 days and still vetoed) or None; `_as_date` coerces a
date / datetime / pandas Timestamp / ISO string to a plain date (datetime is a date SUBCLASS, so it must be
converted first — caught that in the self-test, the naive isinstance order returned the datetime unchanged
and the subtraction blew up). `_lookup_earnings_days(ticker)` wraps `yf.Ticker(ticker).get_earnings_dates()`
and is fail-open: any error (no calendar, network) returns None and the name passes through exactly as it
arrived, never crashing the build. In `build_one`, right after the candles guard, when `earnings_days is
None` I look it up before scoring, so the re-armed date flows into both the tenor filter and the score veto.
A name that already carries a screener date does zero extra network.

Self-tested (6 new asserts: nearest-future wins, past print ignored, datetimes + ISO strings parse, an
only-past calendar re-arms nothing, empty/None -> None, a print today = 0). All of
build_site_data/scoring/structure/levels self-tests stay green, and the three new helpers import clean.
Engine only, no frontend change (the AVOID card already renders off `earnings_days`, which now gets
populated on the fallback path), and the box stays the sole writer of scan.json. That closes the last bullet
in this risk block. Lesson folded into [[fallback-universe-earnings-gate]].

## Cycle 61 — 2026-06-28 — show the yield you actually collect, not the optimistic mid

Took the next open bullet in the freshest risk critic block (06-28 19:48Z, second bullet), the one c60
explicitly left for its own cycle. The headline annualized RoC is priced on the MID, but you sell-to-open
a cash-secured put, so the credit that hits the account is the BID. On a $1.00 mid with a $0.10 spread the
board quotes ~11% annualized while IBKR fills ~9.5%. Small per name, but it is the exact number Michael
judges an entry on, and it leaned optimistic on every single pick. The whole thesis is rich premium you
can actually collect; quoting the midpoint yield is quoting a credit the market is not offering you.

Shipped the critic's "at minimum" option, on purpose. New one-liner: alongside `roc` I compute
`bid_roc = _annualized_roc(bid, strike, dte)` (bid is already in scope from `_quote_expiry`, and on the
modeled path it is the conservative side of the synthetic spread, so it stays honest there too), and the
pick carries a `bid_ann_roc` field. The page readout now appends `(NN% on the bid)` after the headline
annualized whenever the bid yield trails the mid, with a tooltip explaining it is what actually hits the
account. I did NOT swap the bid into the scored premium / the DTE-ladder ranker: that would silently
rescore the whole board and re-rank tenors. Same judgment as c43/c44/c59 — the mid yield ranks the setup
quality, the bid yield is the honest fill he reads, a visible field not a hidden edit. Builds straight on
c60's `_sellable_premium` (price off the side you trade): c60 dropped no-bid phantoms, this makes the
surviving yield read off the bid.

Self-tested (2 new asserts: bid yield strictly below the mid yield you sell into; a one-sided book makes
bid yield == headline) + all build_site_data/scoring/structure/levels self-tests green. Verified headless
(chromium): with `bid_ann_roc` injected below `annualized_roc`, the readout renders `(105.4% on the bid)`
with the tooltip, 0 console errors; the `!= null` guard keeps a pre-field scan.json rendering unchanged.
Engine + frontend only, the box stays the sole writer of scan.json. The last risk bullet (universe.py
fallback-earnings lookup) stays open for its own cycle. Lesson folded into [[no-bid-no-trade]].

## Cycle 60 — 2026-06-28 — a put with no bid is not a trade, so stop quoting it off a stale fill

Took the freshest risk critic line (06-28 19:48Z, first bullet). `_quote_expiry` priced the premium as the
bid/ask mid, but when the strike had no two-sided quote it fell back to `lastPrice` — a stale historical
fill from whenever the contract last traded. The problem: you sell-to-open a cash-secured put, so the credit
you actually receive is anchored on the BID. A put with `bid <= 0` has no market maker willing to buy it from
you; it literally cannot be sold. Yet that phantom quote sailed through `_tradeable_premium`, scored 60-80
(liquidity is only ~13% of the blend), and landed on the board looking like an actionable income trade Michael
could fill. He cannot. The whole thesis is rich premium you can actually collect, and this was quoting credit
nobody was offering to pay.

Shipped as a pure tested helper, matching the module's ethos. New `_sellable_premium(bid, ask)`: returns None
when `bid <= 0` (drop the strike, do not fabricate a price), the mid when both sides are real, and the BID
alone when there is a bid but no ask (the conservative, honest premium; never invent the offer side).
`_quote_expiry` now calls it and returns None on None, which deletes the `lastPrice` fallback entirely. So two
holes close at once: the no-bid phantom is gone, and even a one-sided book no longer gets quoted off a price
that has not traded today.

Self-tested (4 new asserts: no-bid -> None, negative bid -> None, two-sided -> mid, bid-only -> bid) and the
full build_site_data + scoring + structure + levels self-tests stay green. Engine only, the box stays the sole
writer of scan.json. The other two risk bullets (bid-vs-mid `bid_ann_roc` so the yield reads off what you
RECEIVE not the mid; and a yfinance fallback earnings lookup when the screener returns None) stay open, each
its own cycle. See [[no-bid-no-trade]].

## Cycle 59 — 2026-06-28 — a one-touch support is a ghost, so stop anchoring strikes to it

Took the freshest trader critic line (06-28 16:46Z, first bullet): `_anchor_strike` was selling AT a
support level even when the market had tested it only ONCE. A single pivot is statistically a ghost, not
a floor; routing a real strike there (and lighting the green ⌂ support badge over it) gives Michael false
confidence in a level that held one time. c56 had just made the touch count VISIBLE so he could tell a
real floor from a one-off; this cycle makes the ENGINE act on the same number it shows. A badge that says
"x1" while the code still trusts the level is worse than no badge.

Shipped as a pure tested helper, gating at the SOURCE rather than at each consumer. Added
`MIN_SUPPORT_TOUCHES = 3` and `_real_support(support, touches)`, which returns the level only when it has
been tested at least 3 times and None otherwise. In `build_one` I gate `support` right after pulling it
from `support_resistance_detail`, before it fans out, so a demoted level falls through to the ~1 sigma OTM
fallback AND the `support_touches` field, the page floor badge, and the chart floor line all clear
together (no surface claims a floor the others dropped). A genuinely tested level (>= 3 touches) passes
through untouched; resistance is never touched; None support/touches stays None (fail-open: unknown is
not trusted).

Self-tested: a 1-touch and a 2-touch level both demote to None, a 3-touch and a 7-touch pass through, a
None level/None count stay None, and once demoted `_anchor_strike` reports `at_support=False` (the
1-sigma fallback fired). All of build_site_data's self-tests stay green, plus scoring/levels/structure.
Engine only, no scan.json write, no frontend change (the page already null-guards support since c56). The
box anchors strikes on genuinely-tested floors on its next refresh. The other two bullets in that critic
block (a last-5-closes "held above the level" guard on at_support, and a MIN_ANN_ROC drop gate) stay open,
each its own cycle. Lesson folded into [[support-touch-count]].

## Cycle 58 — 2026-06-28 — the factor bars finally say what they MEAN

Picked the next unticked GOAL Phase-3 item: EXPLAIN the model on the site. The page has shown six
factor bars (rich / safe / yield / shares / liq / struct) and a 0-100 score for dozens of cycles, but
nowhere did it say what any of those axes actually measure. A glanceable board with no legend is only
legible to the person who wrote the engine; Michael wanted it readable to him at a glance and to anyone
who has never seen it. The scoring IS the product, and a number you cannot interpret you cannot trust.

The concrete, enumerated piece of that GOAL bullet is the per-factor tooltip, so that is what I shipped.
Added a `FAC_HELP` map in docs/app.js (wording tracked to GOAL's own factor definitions) and a `title`
on each `.fac` span, so hovering the label or the bar explains the factor in plain English and appends
this pick's value as `(NN/100)`. rich = IV vs realized vol (VRP), safe = prob it expires OTM, yield =
annualized RoC on collateral, shares = wheel-fit if assigned, liq = spread + OI, struct = Keltner
position. The `~assumed` modeled-IV flag and its existing tooltip are untouched.

While wiring the titles I needed to escape text into an HTML attribute, and the page had no escaper (the
open frontend-robustness item literally asks for an `esc()` pass). So I added a small `esc()` helper and
used it on the tooltip text rather than depend on a function that did not exist yet. That is a real first
step on that robustness item; future innerHTML/attribute binding can reuse it.

Verified in a headless browser (playwright) against the REAL docs/data/scan.json, not a hand-patched
copy: all six factor bars carry a title, all six factor meanings (rich:/safe:/yield:/shares:/liq:/struct:)
are present, the apostrophe in "stock's" escaped cleanly via esc(), and 0 console errors. `node --check`
on app.js passes. Render-only, no engine touch, no scan.json write. The deeper half of the GOAL item (a
"how scoring works" blurb and a one-line "why this score" per pick) stays open for a later cycle; ticked
sub-item (a) in GOAL and wrote the lesson back ([[explain-the-model-on-site]]).

## Cycle 57 — 2026-06-28 — the TOP badge floats above the score tile, so the eye reaches it first

Took the 06-28 13:46Z product critic line. The c42 TOP badge that marks the #1 pick was anchored
`bottom: -8px` on the score tile, so it sat just below the tile and hugged the card's bottom divider,
half-eaten by the line between cards. Worse than ugly: the eye reached the TOP label AFTER it had
already scanned the grade letter the badge exists to point at. The badge was being read second.

One-line CSS fix in `docs/styles.css`: `bottom: -8px` -> `top: -8px`, so the badge floats up into the
card's 13px top padding instead of down into the divider. Now the reading order is TOP -> grade -> yield,
which is the order the badge was always meant to create. Added a comment saying why it rides above, not
below, so a future cycle does not "tidy" it back down.

Verified in a headless browser (playwright), not just by eye: exactly one TOP badge across 30 rendered
cards, computed `top: -8px`, the badge's top edge (285px) sits ABOVE the score tile top (292px) and inside
the card's own top edge, so it no longer clips into the next card's border, and 0 console errors. Same
verify-the-geometry-not-just-existence discipline as c42/c47. CSS only, no engine touch, no scan.json.

Lesson to memory: a "look here first" label has to physically precede, in reading order, the thing it
points at, or it gets read second and does nothing (same family as c47's "presence is not landing").

## Cycle 56 — 2026-06-28 — the support floor now shows HOW MANY times the market tested it

Took the 06-27 22:48Z trader bullet: `levels.support_resistance` returns only the support PRICE and
throws the cluster's `touches` count away, so Michael cannot tell a real floor (price bounced off it 7
times) from a ghost (one stale pivot). He sells AT support and trusts it to hold; the strength of that
trust IS the test count, and the engine was hiding it.

Surfaced it without breaking the contract every caller depends on. New `support_resistance_detail()`
returns the chosen cluster `{level, touches, last}` on each side; the existing `support_resistance` is now
a thin projection of it (maps detail -> the bare float), so the chart, the strike anchor, and `_levels`
all keep working untouched and the self-tests stay green. Only `build_one` reaches for detail, to thread a
new `support_touches` onto the pick dict (computed once, covers both the live and modeled paths since the
support level is computed before the live/model fork). Refactored the old inner `pick()` into a module-level
`_pick_cluster()` so detail and the projection share one selection rule.

Two surfaces, both off the new field. The page floor badge now reads `⌂ support x7` with "tested 7 times"
in the tooltip; the CLI scan row appends `sup $178x7` (same trailing-tag style as the SECTOR crowd flag, no
new header column). Both guard on the field being present, so a scan.json built before the box bakes the
field in just renders the old `⌂ support` with no count, never an error.

Verified: levels self-test (now asserts touches are counted and the detail level matches the bare price),
build_site_data --selftest, and the import sanity all green; headless playwright against a patched copy of
scan.json (never the real one) confirmed 19 floor badges rendering `⌂ support x7`, the tooltip carrying the
count, and 0 console errors; an offline `_row` check confirmed the CLI tag formats with and without the
count. Engine + CLI + page, no scan.json write (the box bakes `support_touches` on its next refresh). Wrote
the lesson back ([[support-touch-count]]): when a critic wants a value's provenance shown, add a `_detail`
sibling and keep the bare accessor a thin projection, never break a widely-used return contract to bolt one
field on. Declined the freshest 10:46Z critic (a TAKE_PROFIT state) with reasoning: a blanket state would
regress the self-tested case E (a far-OTM monthly at 3 DTE should expire, not close), which is exactly why
c40 made the won-trade signal a decoupled advisory; left the note in INBOX for Michael.

## Cycle 55 — 2026-06-28 — the scanner finally grades its OWN forward picks, not just the model

Took the next unticked roadmap item, my own pick: the Forward RESULTS TRACKER. The hole was real and old.
`wheelforge/backtest.py` (c13) only ever tested the SAFETY MODEL on past OHLCV. Nothing tracked whether
the picks the scanner actually PRINTED on a given morning held up. A scanner graded only on a model, never
on its own output, has no forward record to earn trust with. So I built the forward, honest version.

New `wheelforge/results_tracker.py`, same shape + spirit as iv_history.py: a LOCAL, gitignored SQLite store
(`data/results.db`, added to .gitignore). Three pure-ish functions. `snapshot(picks)` records the day's
ACTIONABLE cash-secured puts (ticker/strike/exp/premium/score/predicted prob_otm/lane) as forward
observations, one row per (record-day, ticker, exp, strike), skipping earnings-veto AVOIDs and covered-call
rows (only the entries the scanner recommends). `settle(prices)` scores every PENDING pick whose expiry has
passed: held AT or ABOVE the strike = OTM (premium kept), below = breach (assignment). `track_record()`
reports the forward hit-rate vs the prob_otm the model PREDICTED, plus avg premium captured, overall and by
lane, returning a dict from day one even while empty.

Wired into build_site_data.main() after the never-blank guard: settle pending picks against the spots the
build ALREADY pulled (no new feed), snapshot today's picks, print a one-line tracker status. Fail-open
throughout, so a tracker hiccup can never block the scan.json write. A name that has LEFT the universe has
no spot today, so its pick stays PENDING rather than crashing or settling on a fiction, the honest behavior.

Deliberate design calls: settle off the build's own spots (cheapest correct source; a freshly-passed weekly
settles immediately, an orphaned name waits); count a re-seen pick on a LATER day as a NEW forward
observation (day is part of the key), since each morning IS a fresh recommendation; treat at-the-money as
OTM/safe (the seller keeps the premium at exactly the strike). The settle math is one pure `_outcome()` that
also handles the covered-call mirror, so c48's second leg is already covered when it wires into the build.

Verified offline: results_tracker self-test (outcome math both legs, snapshot skips AVOIDs, same-pick-later-
day logs fresh, pre-expiry settles nothing, post-expiry grades all, missing price stays pending) green;
build_site_data --selftest, scoring self-test, and `import wheelforge.__main__` all green. Engine + wiring
only, no scan.json (the box bakes the store on its next refresh). Wrote the lesson back
([[forward-results-tracker]]): a scanner earns trust on its forward record, not just a backtest, so settle
off data already in hand and let unsettled observations stay pending, never faked. OPEN follow-ons: a
track-record PAGE on the frontend, and settling names that left the universe (needs price-at-expiry).

## Cycle 54 — 2026-06-28 — the free-shares read stops calling a speculative name a good wheel entry

Took the still-open third bullet of the 06-28 01:47Z trader block: high-IV seeds get labeled a good
free-shares fit even though Michael sells those for the premium, not to own. Tracing it found the real
shape was narrower and worse than the bullet read. `want_to_own` is already computed right (c20: line 387,
`"liquid" in lanes`, so a hi-iv-ONLY name is False) and it already flows into the SCORE path (the contract
dict, line 480) and the pick fields (line 493). The hole was the DISPLAY twin: line 509-510 called
`free_shares_read(..., want_to_own=True)` with the flag HARDCODED, so a speculative pick was scored with
the wheel-fit penalty yet its readout showed full wheel-fit and pitched "if assigned you own at $X, Y%
below today" as a wheel win. The score was honest; the human-facing read lied.

Fixed both halves. (1) Thread the real per-lane flag into the read: `want_to_own=want_to_own`. (2) Make
`free_shares._summary` honest when the name is not one you want, so it reads "Income play, not free shares.
This is a high-IV name you sell for the N% annualized premium, not to own; assignment at $X is the risk to
manage, not the reward." instead of pitching the cheap basis. The frontend already renders
`free_shares.wheel_fit` + `.summary` (app.js:325-329), so this is pure data, no frontend edit, and the box
surfaces it on its next refresh.

Deliberate: I kept line 387's `"liquid" in lanes` over the critic's literal `lane != "hi-iv"`. A name in
BOTH lanes is a genuinely ownable staple that ALSO pays rich premium, the ideal CSP, and should stay
want_to_own=True; the critic's naive form would wrongly flip it to income-only. Took the intent (stop
mislabeling speculative names), kept the better existing logic, same as c51/c53.

Verified offline: the SAME cheap-basis contract now reads wheel-fit 70.4 + a wheel-win summary when wanted,
and 54.4 + the income-play summary when speculative; two new asserts pin the discrimination. freeshares,
scoring, and build_site_data self-tests all green, `import wheelforge.__main__` clean. Engine only, no
scan.json. Wrote the lesson back ([[wheelforge-design-principles]]): a flag computed once and consumed by
both a score path and a display path can be hardcoded optimistic on one side, the score stays honest while
the read lies, so grep every consumer, not just the scorer (twin of c32). The remaining open bullets
(ex-div early assignment, zero-volume mid-vs-bid, OI-wall confirm, support_touches) each stay their own cycle.

## Cycle 53 — 2026-06-28 — the earnings veto now actually fires on an explicit `scan TICKER`

Took the first bullet of the freshest critic block (risk, 06-28 04:47Z). The hole was real and exactly
the kind c8 exists to close: the explicit-ticker CLI path built its plan as
`[{"ticker": t, "earnings_days": None} for t in tickers]`. A None earnings date converts to 999 in
build_one, and `earnings_blocks(999, dte)` never trips, so `python -m wheelforge scan NVDA` on the eve of
NVDA's print would happily print a live put recommendation with no AVOID. The one path a disciplined
seller would use to sanity-check a single name before selling was the one path with the earnings gate
silently disarmed.

Fixed it the c50 way: route the typed names through `seed_universe(tickers)`, which screens BY NAME and
so each name arrives carrying its REAL earnings date + sector (same source the full screener uses), so
the veto is armed for it. The critic specced a bare `plan = seed_universe(tickers)`, but that can DROP a
typed name the screen does not list (a non-US or non-alpha symbol like BRK.B), which violates
never-drop-a-name. So I merged instead: `seeded = {d["ticker"]: d for d in seed_universe(tickers)}` then
rebuild the plan from the TYPED list, falling open to `earnings_days=None` for any ticker the screen
could not resolve. Every typed name survives; the ones the screen knows now carry a live earnings date.

Verified: `seed_universe(['NVDA','BRK.B','AAPL'])` merged back to a 3-name plan with NVDA earnings_days=59
+ sector, AAPL 32 + sector, and BRK.B preserved as None (kept, not dropped). scoring + build_site_data +
universe self-tests all green, `import wheelforge.__main__` clean. Engine/CLI only, no scan.json (the box
already uses screen_universe on its refresh path, so this only changes the human `scan` command). Wrote
the lesson back ([[wheelforge-design-principles]]): a critic's one-liner that closes an integrity hole
can still open a smaller one (here, dropping a typed name); take the fix, keep the invariant. The other
two bullets in the same block (ex-div early-assignment field; zero-volume mid vs bid) stay open, each its
own cycle.

## Cycle 52 — 2026-06-28 — the premium floor now scales with the name, not a flat $25

Took the next still-open bullet in the freshest critic block (trader, 06-28 01:47Z, second bullet):
`MIN_PREMIUM = 0.25` is a fixed-DOLLAR floor, so it lets a $190 AAPL put at $0.28 onto the list. That
is $28 of credit on $19,000 of held collateral, about 5%/yr, nowhere near the ~100%/yr income thesis the
whole scanner is pointed at. A dollar floor is loose on expensive names and tight only by accident,
because the number that actually matters for an income seller is premium as a FRACTION of collateral.

Fixed it as a pure helper rather than the inlined `mid >= max(0.25, spot*0.004)` the critic specced, so
the floor stays one place and is self-testable offline. New `MIN_PREMIUM_PCT = 0.004` (0.4%/week of spot)
and `_premium_floor(spot) = max(MIN_PREMIUM, spot*MIN_PREMIUM_PCT)`; `_tradeable_premium(mid, spot=0.0)`
gates on it. Both call sites already had spot in scope (`_quote_expiry`'s live gate and `build_one`'s
per-name drop), so I just threaded it through. Deliberate fail-safe: spot defaults to 0.0 and
`_premium_floor(0/None)` collapses to the absolute $0.25 floor, so the modeled/degraded paths never
RELAX below today's floor, they only ever tighten on a real live spot. A cheap name (0.4% of $20 = $0.08
< $0.25) still falls back to the absolute floor, so this only bites the pricey names where it should.

Verified: on a $190 name the floor is now $0.76, so a $0.28 mid is dropped while the same $0.28 on a $20
strike still clears; exactly the relative floor is inclusive. Self-test grew six asserts (and the old
absolute-floor asserts still pass, since no-spot keeps the $0.25 behavior). `build_site_data --selftest`
+ `scoring --selftest` both green, import sane. Engine only, no scan.json; the box re-floors on its next
refresh. Wrote the lesson back ([[relative-premium-floor]]): when a gate enforces a RATE, express its
floor as a fraction of the base it scales against, with the absolute floor as a max() backstop. The
hi-iv want_to_own flip (third bullet, same block) stays open for the next cycle.

## Cycle 51 — 2026-06-28 — the put strike now lands AT or below support, never above it

Took the freshest still-open INBOX line (trader critic, 06-28 01:47Z, first bullet). `_quote_expiry`
anchored the strike to a support level, then picked the listed strike with the smallest abs distance to
it over the `strike <= spot` set. The hole: abs-nearest can be the strike just ABOVE support. Support
$461.50, listed $460/$462.50 -> $462.50 wins by a nickel, and we would be selling a put struck above the
very line the trade trusts to hold. On-thesis, that is selling into the air just above support, not at
it.

Fixed as a pure, tested helper rather than the one inlined line the critic specced, because the naive
`puts["strike"] <= target * 1.002` filter can go EMPTY on a deep level / sparse chain and blank the name
(violates site-never-blank). `_strike_at_or_below(strikes, target, spot)`: take strikes at/below
`target * 1.002` (0.2% tol so a strike right at target rounds through), pick nearest within that, and
fall back to the nearest sub-spot strike ONLY when nothing lists at/below target. `_quote_expiry` now
calls it. Verified: $461.50 between $460/$462.50 now sells $460; a strike right at target is taken; a
deep target falls back instead of blanking; no strike at/below spot returns None. Self-test (5 asserts)
green, full build_site_data + scoring self-tests still pass, import sane. Engine only, no scan.json; the
box re-strikes on currently-honored support at its next refresh. The MIN_PREMIUM relative-floor and the
hi-iv want_to_own bullets in the same block stay open, each its own cycle.

## Cycle 50 — 2026-06-27 — seed the high-IV weeklies so the scanner never misses MSTR

Took the freshest still-open INBOX line (growth critic, 06-27 07:46Z, third bullet): the high-IV lane
runs a Volatility.M screen that returns only its top ~11 names, so a weekly Michael actively watches
(COIN, HOOD, MSTR, RDDT, PLTR, MARA...) can rank 12th and silently vanish from the scan the very week
its premium is richest. The richest trade of the week could be invisible because a screen ranked it one
slot too low. Closed it.

Added `HIGH_IV_SEEDS` (14 names) to `wheelforge/universe.py` and a new `seed_universe(symbols)` that
screens for those EXACT names. The design call that made this honest rather than dangerous: I did NOT
union them in as `earnings_days=None` placeholders, which is what the naive read of "seed them in"
would do. A None earnings date reads as "no veto needed" in `_candidate_expiries`, so every seed would
have been sellable three days before a print, re-opening the c8 earnings blowup the gate exists to
close. Instead I screen the seeds BY NAME (`col("name").isin(...)`, one extra cheap query) so each
arrives carrying its REAL earnings date + sector, exactly like a screener-ranked name, and the earnings
veto stays armed. Verified live: all 14 seeds come back with real earnings days (COIN 33, MSTR 38, MARA
46) and sectors. Only if that screen is unavailable do the seeds fall open to None, still included
rather than dropped (site-never-blank).

Factored the lane union into a pure `_merge_lanes(liquid, high, seed)` so its invariants self-test
offline: every seed survives, a name in two lanes carries both tags once each, a seed duplicating the
high slice is not double-tagged, and a seed's None never erases a known earnings date/sector from the
liquid lane. `python -m wheelforge.universe --selftest` green; live `combined_universe()` grew the board
from ~24 to 34 names with all 14 seeds present and lane-tagged; scoring + build_site_data `--selftest`
both still green. Engine only, no scan.json (the box bakes the wider universe in on its next refresh).
- Learned, wrote it back ([[wheelforge-design-principles]] c50): when you inject names that bypass the
  normal universe path, they must still satisfy every GATE that path feeds. Grab the gate's data at the
  same cheap universe stage (c8) rather than letting a None placeholder silently switch the veto off. A
  seed that skips its earnings date is not a convenience, it is a hole.
- Left open (unchanged): the WANT_TO_OWN ownership-constant bullet in the same critic block (c20 already
  made want_to_own lane-derived, so I am not hardcoding a list over it); the 06-27 10:46Z risk trio
  (earnings-unknown veto, bid-vs-mid yield gate, friction-adjusted RoC); the IBKR portfolio.py morning
  brief; and the CC-into-scan.json wire-up. Each its own cycle. The c44 RoC-denominator deferral stands.

## Cycle 49 — 2026-06-27 — the score tile leads with yield, not a redundant raw score

Took the freshest open INBOX line (product critic, 06-27 19:46Z). The per-pick score tile read a
heat-colored letter grade with the raw 0-100 score under it (`A / 73`). But the grade letter ALREADY
bands that score (A>=80, B>=65, ...), so the second line carried no new information while occupying the
one spot the eye lands first. The number Michael actually trades off, the annualized yield, was buried
on line 2 of the sub text. A readability miss: the tile spent its prime real estate on a redundant digit.

Fixed it in `docs/app.js` renderList(): `.wf-num` now shows `Math.round(annualized_roc) + '%'` in amber
for non-avoid picks, and the raw Premium Quality Score moved to the tile's `title` tooltip (still one
hover away, never lost). Added `.wf-num.yield { color: var(--amber); font-size: 13px }` in styles.css so
a 3-4 char yield like `341%` fits the 54px tile. AVOID cards are untouched: still the red ✕ over their
honest F. I kept the change render-only and additive; the grade tile structure from c47 stays intact.

Verified headless (playwright against a local server over the live scan.json): 24 cards, the first six
read `B/7%`, `C/130%`, `C/96%`, `C/341%`, `C/68%`, `C/156%`, all amber (rgb 255,176,0), each with the
raw score in the title attribute, zero console errors. scoring self-test still green; app.js parses.
Frontend only, no scan.json (the box owns it and will serve this code on its next 30-minute refresh).
- Learned, wrote it back ([[wheelforge-design-principles]]): when two glanceable fields encode the same
  thing (grade letter and raw score), one is wasted real estate. Spend the prime fixation spot on the
  decision number (yield), demote the redundant one to a tooltip. Surfaced an honest tension worth
  keeping visible: top-by-quality (NVDA B, 7%) is not top-by-yield (IREN 341%).
- Left open (unchanged): the still-unconsumed older INBOX bullets each want their own cycle: the IBKR
  `portfolio.py` morning brief (02:23Z), the `WANT_TO_OWN` ownership constant + `HIGH_IV_SEEDS` union
  (06-27 07:46Z), and the 06-27 10:46Z risk trio (earnings-unknown veto, bid-vs-mid yield gate,
  friction-adjusted RoC). The c44 RoC-denominator deferral stands (Michael's call, not a critic's).

## Cycle 48 — 2026-06-27 — the wheel finally has its second leg: covered calls

Took the freshest open INBOX line (growth critic, 06-27 16:48Z): WheelForge had `_live_put`,
`_bs_put`, `_iv_from_put` and nothing for the wheel's SECOND leg. When a CSP gets assigned (the
welcome ~15-20% outcome), Michael owns 100 shares at a known basis and the engine went silent at
exactly the moment the income machine should keep running by selling a covered call to grind that
basis down. GOAL.md's mission names this ("reduce basis without capping away a name you meant to
keep") but no code implemented it. Closed it.

Built `wheelforge/covered_call.py`, the same shape as roll_advisor: a PURE core, network in the CLI.
The decision is small and disciplined: `pick_call(spot, basis, candidates)` sells the LOWEST
out-of-the-money strike at or above the cost basis (OTM keeps upside room; >= basis means a
call-away sells at or above what you paid, so it is basis reduction plus gain-to-strike, never a
forced loss to harvest premium). `covered_call_read(...)` prices it and scores it through the SAME
`score_contract` path the CSP scanner uses (direction "covered call"), so both legs of the wheel
grade on one ruler. I mirrored the put math exactly rather than approximating: added `_bs_call` +
`_iv_from_call` (solve IV from the real mid, since the codebase rightly distrusts yfinance's quoted
IV) and `call_prob_otm`, the median-measure complement of build_site_data's put prob_otm, so a call
and a put are judged on the same safety ruler. RoC for a CC is anchored on the share basis the leg
actually ties up (premium/basis annualized), not a cash strike. The read returns the basis grind
(old -> new), per-cycle + annualized RoC, keeps-shares %, and the called-away gain, with a plain
summary; it returns None when no OTM strike reaches the basis (shares too far underwater for a clean
covered call) and says so rather than faking a pick.

Exposed as `python -m wheelforge cc TICKER --basis COST [--dte N] [--shares N]`. The CLI's new
`_call_chain(ticker, min_dte)` pulls the nearest qualifying call chain + spot + a quick realized vol
off yfinance (fail-open), feeds the pure core, and prints the grade, the strike to sell, the basis
reduction, and the called-away gain.

Verified: `python -m wheelforge.covered_call` self-test green (lowest-OTM-at-basis selection, premium
reduces basis, prob_otm in (0,1) and complement-checked, underwater shares reach a higher strike,
deeply-underwater returns None, earnings-veto rides the shared path to an honest F); all module
imports clean; the scoring self-test still passes; and a LIVE end-to-end run priced an AAPL covered
call (basis 280, spot ~284 -> sell the 285 call, basis 280 -> 273.85, 40% annualized, honest F on a
thin near-ATM premium). Engine + CLI only. I did NOT touch scan.json (the box owns it and will run
this code on its next 30-minute refresh).
- Learned, wrote it back ([[roll-advisor-lifecycle]] c48): WheelForge now spans the full position
  lifecycle (entry CSP -> open-put defense -> post-assignment covered call), every leg pure + graded
  on the one `score_contract` ruler. The open follow-ons: wire CC into build_site_data/scan.json + the
  frontend (the critic's `build_one_cc`), and the IBKR `portfolio.py` morning brief.
- Left open on purpose: the three still-unconsumed older INBOX bullets (IBKR portfolio brief, the
  WANT_TO_OWN ownership-conviction constant, the HIGH_IV_SEEDS universe union) and the 06-27 10:46Z
  risk trio (earnings-unknown veto, bid-vs-mid yield gate, friction-adjusted RoC) each want their own
  cycle. The c44 RoC-denominator deferral stands (Michael's call, not a critic's).


## Cycle 47 — 2026-06-27 — the c41 letter grade finally lands inside the score tile

Took the freshest open INBOX line (product critic, 06-27 04:47Z). The letter grade I shipped in c41
was supposed to let the board read A/B/C at a glance, but I had placed it as a 12px corner badge
absolutely positioned at top:7px/left:9px, which dropped it into the card's top padding dead-zone, 6px
above the score tile and inside the 16px left padding margin. Nobody's eye lands there, so the grade
was decoration: you still had to decode every score number to know where to look. A real readability
feature that, as built, did not deliver the read.

Fixed it exactly as the critic specced. `.wf-score` is now a flex-column tile: the grade letter LEADS
at 22px (I kept its heat-graded color classes, A-green through F-red) and the raw score confirms below
it at 14px `var(--dim)` in a new `.wf-num` element. I stripped `position: absolute` plus the badge
box/border/padding off `.wf-grade` so it is a plain colored letter in the tile, and removed the stray
`card.appendChild(gr)` in `renderList()` so the grade is no longer a floating direct child of the
card; it now nests in the score tile alongside the existing TOP badge. Avoid cards show grade F over a
red ✕, so the honest-F intent from c41 survives. Render + CSS only; I did NOT touch scan.json (the box
owns it and re-renders this code on its next 30-minute refresh).

Verified headless (playwright + the bundled chromium, served docs/ over a local http server against
the real scan.json): the grade's computed `position` is now `static` (was absolute), the score tile's
`flex-direction` is `column`, the tile's children order is grade -> num, exactly 0 cards carry a grade
as a direct child, exactly one is-top card with one TOP badge, and 0 console/page errors across all 24
rendered cards. This advances the "match the TraderDaddy CSP-wheel page UX / standouts highlight"
front-end arc (c41 grade, c42 TOP anchor): the board now reads grade-first the way c41 intended.
- Learned, wrote it back ([[wheelforge-design-principles]] c47): a readability feature is only shipped
  when the eye actually lands on it. A signal placed in a margin or padding dead-zone is decoration no
  matter how correct its value; put the lead signal where the eye already goes (the score tile here),
  size it to lead, and demote the confirming detail. Verify placement, not just presence.
- Left open on purpose: the three still-unconsumed INBOX bullets (the IBKR portfolio morning-brief, the
  WANT_TO_OWN ownership-conviction constant, and the HIGH_IV_SEEDS universe union) each want their own
  cycle. The c44 RoC-denominator deferral stands (Michael's call, not a critic's).


## Cycle 46 — 2026-06-27 — a ROLL_ALERT now names the trade, not just the worry

Took the growth critic's roll_target bullet (INBOX 06-26 07:46Z), which I had deferred twice on
purpose while I shipped the sector-crowding and short-RV-floor work. roll_advisor already said the
right thing when a short was tested ("roll down-and-out for a credit before gamma bites") and then
stopped: down to WHICH strike, at which expiry, for what credit? Diagnostic done, prescription
missing. Closed it with a pure `roll_target(current_mid, spot, iv, new_dte, candidates, qty,
opt_type)` in roll_advisor.py: it computes the ~1 sigma down-and-out target off the live IV and the
roll-out tenor (`ROLL_OUT_DTE` = 14), picks the candidate strike nearest that target, and prices
`net_credit = new_premium - current_mid` per share and in dollars. I kept the module's whole ethos
intact (pure, no network, fully testable): the network lives in the CLI's new `_roll_chain(ticker,
min_dte)`, which fetches the roll-out chain off yfinance and feeds (strike, premium) pairs into the
pure core, exactly the way `evaluate` is fed the current mid. On a live ROLL_ALERT the `roll` CLI now
prints `-> ROLL TO  $K put  exp DATE  (Nd)  @ $prem   net credit/DEBIT $x/share ($y on Qx)`.

The honest part I am glad I built: when I ran it live on a tested 180 put (spot 182), the
1-sigma-down roll lands at the 160 strike worth only $0.46 against a $2.60 buyback, so it is a net
DEBIT, not a credit. A deeply-tested short usually CANNOT be rolled down-and-out for a real credit,
and the tool says `net DEBIT` plainly instead of dressing it up. That is the whole point: name the
trade and tell the truth about its cost so Michael takes the defend-vs-assign call with his eyes open.

Verified: roll_advisor `--selftest` green with a new case G (the prescription for case B's alert:
nearest candidate to the ~159 target is the 160 strike, $3.00 vs $2.60 buyback = a $0.40/$40 credit)
plus three fail-open asserts (no candidates, junk IV, non-positive spot all return None, never
throw); `import wheelforge, wheelforge.universe, wheelforge.__main__, wheelforge.roll_advisor` clean;
scoring self-test green; and the live `roll NVDA ...` CLI path printed the ROLL TO line end to end.
Engine + CLI only; I did NOT touch scan.json (the box owns it). This advances the position-management
arc (c31 states, c40 profit-take): WheelForge now manages the trade after the sell, and when it says
defend it hands you the specific roll.
- Learned, wrote it back ([[roll-advisor-lifecycle]]): a prescription is only worth shipping if it
  will print an INCONVENIENT answer. The valuable thing here is not "here is a strike," it is "this
  roll is a net DEBIT" — the tool that only ever confirms the easy path is decoration. Keep the
  network at the CLI edge and the decision pure, so the honest answer is the testable one.


## Cycle 45 — 2026-06-27 — a quiet week can no longer fake rich premium

Took the still-open third bullet of the quant critic's 06-26 19:49Z INBOX block. Since c28 the LIVE
weekly path judges IV against a 5-day realized vol (`short_rv`) instead of the 20-day, so a fresh vol
spike (exactly when you want to sell) is not masked by last month's cool RV. Good fix, but c28 only
reasoned about the spike-UP direction. The critic caught the other tail: a 5-day window is ~5 returns,
so its sampling error is large in BOTH directions, and one unusually QUIET week drops short_rv to ~0.4x
the 20-day rv, which pushes VRP (iv/short_rv) past the richness saturation ceiling on a name whose vol
is actually cheap. The scanner was manufacturing richness out of a quiet tape. Closed it with a
`SHORT_RV_FLOOR = 0.70` constant + a pure `_floor_short_rv(short_rv, rv)` helper: the 5-day denominator
can now compress by at most 30%, not 60%. The deliberate design call is that it is a LOW-TAIL clamp
ONLY, a genuinely hot week (short_rv already above the floor) passes through untouched, so c28's
spike-UP honesty (a live week shrinking a stale 20-day VRP) is fully preserved; I only killed the lie
in the flattering direction. Engine only; the modeled monthly path (which keeps the 20-day match) is
untouched, and I did NOT touch scan.json (the box re-scores on its next refresh). Verified:
`build_site_data --selftest` green with four new asserts (a quiet 0.10 vs 20d 0.40 floors to 0.28, a
hot 0.60 passes through, no-20d-rv returns unchanged, and the inflated VRP that read 4.0 unfloored now
caps at 1.43, back under the ceiling); scoring + vol_models self-tests green; `import wheelforge,
wheelforge.universe, wheelforge.__main__` clean. This advances the richness/honesty work (c21, c33, c37,
c39): high IV is not rich premium, and now neither is a quiet week pretending to be one.
- The other two bullets in that block I did NOT act on, on purpose. The σ=IV-vs-σ=RV prob_otm swap is a
  meaning change to a number deliberately labeled risk-neutral (the c22 `*`), so it is Michael's call,
  not a critic's (same rule as the RoC denominator). The sqrt(252)-vs-dte/365 "mismatch" is wrong:
  pairing RV-over-252-trading-days with a calendar BS time of dte/365 IS the standard consistent
  convention (dte calendar days hold ~dte*252/365 trading days, so solved IV already equals RV at zero
  VRP); the proposed "unify on dte/252" would CREATE the 20% inflation it claims to remove. Annotated in
  INBOX and left.
- Learned, wrote it back ([[wheelforge-design-principles]] c45): when you swap a stable estimator for a
  short noisy one to gain responsiveness, you inherit its sampling error in BOTH tails; floor/cap the
  tail that produces the FLATTERING error and leave the honest tail free. A one-sided clamp keeps the
  responsiveness and kills only the lie. And read each critic bullet on its own merits, a real fix can
  ride in the same block as two bad ones.


## Cycle 44 — 2026-06-27 — the scanner finally notices when it stacks one sector

Took the unconsumed growth/quant critic INBOX bullet (06-26): WheelForge scored every name in
isolation, so it could flag NVDA, AMD and TSLA all BUY the same morning and never see that Michael
would be selling puts on three correlated semis at once. Capital concentration was invisible. Closed
it: the TradingView screener already can return GICS `sector` (no new data source), so I added it to
the select and carried it through universe -> build_one -> the pick. Then a post-sort
`_sector_crowding(tickers)` pass walks the RANKED list and, within each sector, lets the first
`MAX_SECTOR_OVERLAP` (=1) qualifying name (score >= `SECTOR_CROWD_SCORE` 60, not an AVOID) through
clean and flags every further one `sector_crowded`. The deliberate design call, and where I diverged
from the critic's "discount rank": the flag does NOT touch the 0-100 score or the rank order. The
score is about whether THIS setup is rich/safe/ownable; whether you already hold the sector is a
portfolio-fit question on a separate axis. So the rich-but-third semi still scores and ranks where it
earns, it just wears a `⚠ SECTOR` chip so he sizes it down or skips it on purpose. Same judgment as
c43 (honor the critic's intent, apply it the on-thesis way). Fail-open all the way: a name with no
sector (or an explicit CLI scan) is never crowded and never fills a slot, and an AVOID never consumes
a slot so a real pick behind it stays clean. Surfaced in three places: scan.json (`sector` +
`sector_crowded`), the CLI scan table (a `SECTOR` marker on the row), and the page (a red `⚠ SECTOR`
chip on the card, reading the canonical server flag). Engine + CLI + render-only frontend; I did NOT
touch scan.json (the box bakes `sector`/`sector_crowded` in on its next refresh, then the chips light
up). Verified: `build_site_data --selftest` green with new crowding asserts (the second Technology
name flags, the first stays clean, a Healthcare loner is clean, a sub-60 also-ran is not flagged, a
no-sector name is always clean, and an AVOID does not consume a sector slot); scoring self-test green;
`import wheelforge.universe, wheelforge.__main__` clean. Headless (playwright + chromium, served over
http): live scan.json renders 24 cards with 0 chips and 0 JS errors (correct, the field lands after
the next box refresh), and a routed fixture with one crowded Technology pick renders exactly one
`⚠ TECH` chip inside the right card with 0 JS errors. This advances the still-open CSP-screener
roadmap line ((b) a real concentration/capital guard) and the page-UX line.
- Learned, wrote it back ([[wheelforge-design-principles]] c44): keep the quality score about the
  trade in front of you; concentration, correlation, and sizing are portfolio decisions that belong
  in a flag the human reads, not folded into the per-name number. Vetoes/flags, not factors.


## Cycle 43 — 2026-06-27 — support has a shelf life, so the picker now weighs recency

Took the trader critic's newest INBOX bullet (07:46Z), which two separate trader critics had now
flagged (also 13:47Z): `levels.support_resistance` ranked tested levels by touch count alone, so a
floor tagged five times six months ago beat one freshly retested last week, and the `at_support` flag
could fire on a stale ghost the market had already sliced through once. Michael sells AT support that
is actively holding NOW; a 6-month-old level undercut a quarter ago is not that. Closed it with a
`require_recent=63` bars gate (~one quarter of the box's 8mo / ~168-bar history): a cluster whose LAST
touch is older than that is treated as stale and used ONLY as a fallback when nothing has been tested
recently, so a name that has simply gone quiet still reports its best old level rather than collapsing
to None. The gate sits in FRONT of the existing (touches, nearer-to-spot, recency) sort, it does not
replace it, so among actively-respected levels the most-tested one still wins. The two callers in
build_site_data take the default, so live scans now anchor strikes on currently-honored support; I did
NOT touch scan.json (the box bakes the new strike selection in on its next refresh). Verified:
`python3 -m wheelforge.levels` green with a NEW case proving the gate actually flips the pick (a
heavily-touched stale ~95 loses to a fresh fewer-touch ~100, and with the gate off the old ~95 still
wins, so the test fails if the recency logic ever regresses); the original support/resistance test is
unchanged (its 63 bars all fall inside the window). `import wheelforge`, scoring, structure, and the
build_site_data DTE-ladder self-tests all stay green. Pure engine, no network, no scan.json.
- Learned, wrote it back ([[wheelforge-design-principles]] c43): for price-action signals, WHEN a level
  was last respected is part of whether it is a level at all. Recency is not a tiebreak under touch
  count, it is a gate in front of it. But fall back gracefully (any-vintage when nothing is recent) so
  the filter never blanks a usable level.


## Cycle 42 — 2026-06-27 — the best pick now announces itself before you read a digit

Took the product critic's INBOX bullet (10:46Z): on the board every card wore near-identical chrome,
so the #1 pick had no visual anchor. The first card got only the same 3px is-sel rail that the
SELECTED card gets, which means rank and selection looked alike and Michael's eye had to scan and
compare actual score numbers before it knew where to land. A ranked list whose top item you can only
find by reading every value is half a ranking. Closed it render-only: rank-0 (and not an AVOID) now
carries an `is-top` class (a fatter 6px amber rail + a faint #1a1200 amber wash) plus a small 9px amber
`TOP` badge on the score tile. The mark is anchored to RANK, independent of selection, so it stays put
as he clicks around and re-anchors live the instant a re-sort or filter changes who is #1. One catch
worth the note: `.wf-top` is already the page header bar, so the badge is `.wf-topbadge` and the score
tile got `position: relative` to hang it off the bottom edge. Pure frontend (docs/app.js + docs/styles.css),
no engine, no network, did NOT touch scan.json. Verified headless (playwright + chromium, served over
http against the live scan.json): exactly one `.wf-card.is-top`, exactly one `TOP` badge and it lives
inside the first card's score tile, the first card carries the class, and zero JS page errors. This is
the first half of the still-open "Prime Picks standouts highlight" page-UX roadmap item.
- Learned, wrote it back ([[wheelforge-design-principles]]): in any ranked view the top item needs
  visual hierarchy the eye finds pre-attentively (border weight, a background wash, a badge), not just
  a row you could identify by reading every number. One glance should locate the best pick before a
  single digit is parsed. And watch for class-name collisions when adding chrome.


## Cycle 41 — 2026-06-27 — a letter grade, so the board reads A/B/C at a glance

Pulled the first piece of the two open TraderDaddy-port roadmap items: a LETTER GRADE on every pick.
Both the engine-port line ("Grade from EdgeScore: A>=80, B>=65, C>=50, D>=35, F below") and the
page-UX line ("a LETTER GRADE led front-and-center") wanted it, and it is the smallest, most honest
slice of either: a pure mapping off the 0-100 Premium Quality Score I already compute. "63.5" makes
you do mental math; a B does not. Added `letter_grade(score)` to `scoring.py` (the documented
EdgeScore bands, fail-open to F on junk/NaN) and folded `grade` into `score_contract`'s return, so it
rides into scan.json through the existing `**scored` spread with zero build_site_data change. An
earnings-vetoed pick scores 0, so it grades F honestly, and the dimmed AVOID card already says why.
On the frontend each card now wears a small corner badge on its score tile (A green, fading to F red),
absolutely positioned so it never disturbs the score/ticker/sub grid; a `gradeFor(p)` helper grades
client-side with the same bands when `p.grade` is absent, so the page grades correctly on the CURRENT
scan.json (built before the engine carried the field) and on every refresh after. Verified: scoring
self-test green with six new grade asserts (band edges 80/50/34.9, junk->F, an avoid is F, a fatter
yield never grades worse); build_site_data + structure + freeshares self-tests + `import wheelforge`
all green; headless (playwright + chromium, served over http) confirms 24/24 cards carry a grade
badge, grades render B/C/D/F off the live scan, the top card's 69.8 reads B (65-80 band, correct),
and zero JS page errors. Pure function + render-only, no network, did NOT touch scan.json (the box
stays its sole writer and bakes the engine `grade` field in on its next refresh; until then the
client fallback grades it).
- Learned, wrote it back ([[wheelforge-design-principles]]): when you add a field the FRONTEND reads,
  give the page a client-side fallback that computes it the same way, so the UI is correct the instant
  it ships rather than only after the box rebuilds the data. Forward-compatible rendering, no flash of
  a missing badge during the deploy-to-refresh gap.


## Cycle 40 — 2026-06-27 — the roll advisor finally knows when you have WON

Took the growth critic's newest INBOX bullet (22:46Z): `roll_advisor.py` fires ROLL_ALERT when a
position is threatened but had no signal when it had WON. The `evaluate()` state machine does have a
BTC_NOW take-profit, but it is gated behind >=50% of the DTE still being on the clock. That gate is
right for a monthly grinding out its last slow days (let it expire, keep it all) and WRONG for a short
weekly that hits 50% of max profit on day 3 or 4: there the residual premium is tiny and the days left
are worth more as freed collateral than as theta. The income machine's annual yield is premium-per-
trade times trades-per-year, and we were optimizing only the first term. Closed it: added
`profit_take_alert(entry, mid, dte_remaining)` returning "CLOSE_50" the instant `mid <= entry *
PROFIT_TAKE_PCT` (0.50), decoupled from the clock, plus the constant at the top of the file. It rides
as a `profit_take` ADVISORY field on `evaluate()` and never overrides the state, so the well-tested
risk-first state machine is untouched (case E, the monthly late-decay HOLD, still holds). The `roll`
CLI prints a "$$ PROFIT TARGET (50%)" line only when the advisory fires while the state is still HOLD,
i.e. exactly the early-weekly case where it adds something the state did not already say. Verified:
`python3 -m wheelforge.roll_advisor` green with a new case F (7-DTE weekly at day 4: state HOLD,
profit_take CLOSE_50) plus five isolated asserts on the pure function (exact-50% hit, below-50% hit,
60%-left miss, zero-entry and junk-input fail-open to None); the offline `roll` CLI prints the new
advisory line; `import wheelforge` and the scoring self-test stay green. Pure functions, no network, no
frontend, did NOT touch scan.json (the box stays its sole writer; this is an engine + CLI change the
box picks up on its next refresh).
- Learned, wrote it back ([[roll-advisor-lifecycle]]): a state machine's convenience gate (the >=50%
  DTE rule) can silently swallow a real opportunity at the boundary. The fix was not to loosen the gate
  (it is right for the monthly) but to add an orthogonal advisory that surfaces the conflict to Michael
  and let HIM weigh it. Same family as not flipping a settled call: don't widen a tested rule, ride a
  second signal alongside it.


## Cycle 39 — 2026-06-26 — a modeled chain can't wear real-liquidity bars anymore

Took the risk critic's second queued INBOX bullet (16:48Z), the one c37 marked "clean and queued
next". When the live option chain fails to load, `build_site_data.build_one()` falls open and models
the pick from realized vol. That path was fabricating `oi=1500, vol=250`, which fed `liquidity_score`
a deep-OI/real-flow story and graded the modeled liquidity bar ~0.76, the exact range of a genuinely
liquid AAPL put. So a name whose chain never loaded could sit on the board wearing the same liquidity
chrome as a fillable one, and the annualized RoC Michael judges entries on rode on a fiction. Closed
it: set `oi, vol = 0, 0` on the modeled path (kept the synthetic 4% spread, the one liquidity input a
model can honestly estimate). Now `liquidity_score` collapses to its spread-only term (~0.44), the
bar shrinks visibly, and the modeled pick is honest on every factor, not just its source tag. Locked
it with a scoring self-test: a modeled-style quote (tight 4% spread, oi=vol=0) must grade <= 0.5 and
strictly below a real liquid put. Verified: `python3 -m wheelforge.scoring` green (prints "modeled
(no OI): 0.444"), build_site_data + structure + freeshares self-tests stay green, package imports
clean. Engine-only change, no frontend touched; the page renders the liquidity bar straight off this
score, so it is just honest now. Did NOT touch scan.json; the box stays its sole writer and applies
the honest modeled liquidity on its next refresh. This finishes the risk critic's pair from c37
except the earnings-gate flip, which still wants a surgical degraded-path guard (it would mark every
name AVOID on a fallback scan), not a blind `return False -> return True`. Left annotated in INBOX.
- Learned, wrote it back (brain/wheelforge-design-principles.md, appended to the c37 floor principle):
  a modeled pick must be honest that it is modeled on EVERY factor it touches, not just the source
  tag. Faking thick OI to fill out a bar is the same masquerade as a wide spread rescued by OI. Same
  honesty family as c22, c35, c37.


## Cycle 38 — 2026-06-26 — make the support floor something he can sort and filter, not just see

Closed the last open sub-task of the "use the S/R, do not just draw it" item (b). The major
price-action support has been a scoring factor since c29 and a thick cyan line on the chart for
cycles, and every pick already carried `at_support` + `support_floor` in scan.json. But the board
could not answer the two questions the signal exists for: "show me ONLY the names sitting on a
floor" and "rank by floor strength". A line he can see but not query is half-shipped. Render-only
cycle, no engine touched. Added three things to docs/app.js + styles.css, all off fields already in
the JSON: (1) a `support` SORT pill (sorts by `support_floor` descending), (2) an `at support`
filter TOGGLE in the lane row that keeps only `at_support` picks (green when on), and (3) a green
`⌂ support` floor badge on each anchored card, right after the OTM chip, with a tooltip carrying the
floor strength. Verified headless (playwright + installed chromium, served over http): the `support`
sort pill and `at support` toggle both render; clicking the toggle filters 24 cards down to 14 and
every one of those 14 carries a floor badge (the count matches exactly); the support sort re-ranks
without error; zero JS page errors (the lone 404 is the favicon). Python self-tests stay green
(build_site_data, scoring) and `import wheelforge` is clean, though this cycle never touched the
engine. Did NOT touch scan.json; the box stays its sole writer and already emits both fields, so the
new controls light up on the live board immediately, no rebuild needed.
- Learned, wrote it back (brain/wheelforge-design-principles.md, c38): the moment the engine computes
  a thesis signal and stores it per pick, the frontend owes it a SORT and a FILTER, not just a
  passive chart draw. Check the JSON before reaching for the engine, the carry is often already there
  and the cycle is pure render.


## Cycle 37 — 2026-06-26 — a wide-spread pick is ungradeable, not OI-rescued
Took the risk critic's third INBOX bullet (16:48Z), the cleanest of his three integrity holes.
`liquidity_score` soft-ramped the spread to zero only at 20%, so a 16% spread (where the quoted mid
is a fiction and the real fill is far worse) still scored ~0.61 on its open interest alone, cleared
the 0.40 "illiquid" line with no flag, and inflated the annualized RoC Michael judges entries on
before a single order was placed. Closed it the same way I closed the thin-premium hole in c35: a
HARD FLOOR, not a soft penalty. Added `MAX_SPREAD_PCT = 0.15` next to `WEIGHTS` and an early
`return 0.0` in `liquidity_score` when `spread_pct >= MAX_SPREAD_PCT`, so a pick too wide to fill is
ungradeable on liquidity rather than rescued by deep OI on another term. The existing `cheap_illiquid`
case already scored 0.0 liquidity (111% spread), so no test drifted; I added a sharper pair that
isolates the spread: two picks with identical deep OI/volume, one at a 1.5% spread (grades 1.0) and
one at a 16% spread (now grades 0.0, was ~0.61). Verified: `python3 -m wheelforge.scoring` green
with the three new asserts; build_site_data / structure / freeshares self-tests stay green; package
imports clean with `MAX_SPREAD_PCT` exposed. Engine-only change, no frontend touched, so no headless
run needed, the page renders the liquidity bar straight off this score and it is just honest now.
Did NOT touch scan.json; the box stays its sole writer and applies the floor on its next refresh.
Deliberately did NOT take the risk critic's other two bullets this cycle: the earnings-gate flip
(`return False` -> `return True` on an unknown earnings date) is correct in spirit but has real blast
radius (it marks every name AVOID on a fallback/network-error scan, which would replace a good board
with an all-AVOID one) and wants a surgical degraded-path guard, not a blind flip; the modeled
`oi/vol=0` honesty fix is clean and queued next. Annotated both in INBOX with the reasoning.
- Learned, wrote it back (brain/wheelforge-design-principles.md, c37): when bad or missing data can
  pass for good (a wide spread rescued by OI, a modeled chain wearing real-liquidity bars, an unknown
  earnings date read as clear), the honest fix is a hard floor that makes the pick ungradeable, not a
  soft penalty it can out-score elsewhere. Floors over ramps when the faked number is one he trades
  on. Same honesty family as c22 and c35.

## Cycle 36 — 2026-06-26 — show the OTM distance, stop making him do the division
Consumed the trader critic's first INBOX bullet (13:47Z): the card showed the strike and the spot
but never the one number he leads every put with, how far OTM it is. He describes his own trades
that way ("NVDA 190p, ~5% OTM, 4 DTE"), so the card was forcing him to divide (spot - strike)/spot
in his head for each name before he could compare. Closed it. Added a pure `_pct_otm(spot, strike)`
helper (rounds to 0.1%, guards a zero spot so it never divides by zero) and emitted
`strike_pct_otm` on every pick dict next to the strike. The frontend renders it as a small amber
`~5.3% OTM` chip right after the "sell $40 put" on each card, with a null-guard so any pick missing
the field (e.g. the live scan.json until the box reships this code) just omits the chip cleanly
instead of printing "~null%". One CSS class `.otm` for the chip. Did NOT touch the trader's second
bullet (the levels.py recency re-rank), which is a heavier change to the support picker and its own
cycle. Verified: `python3 -m wheelforge.build_site_data --selftest` green with three new asserts
(190p/200 spot = 5.0% OTM, strike-at-spot = 0%, zero-spot does not divide); scoring/structure/
freeshares self-tests stay green; a headless Chromium load (npx-cached playwright + the installed
chromium, served over http) with one pick patched to carry `strike_pct_otm: 5.3` renders the
`~5.3% OTM` chip on its card, leaves the unpatched cards chip-free, and throws zero JS errors. Did
NOT touch scan.json; the box stays its sole writer and will emit `strike_pct_otm` on its next
refresh once it runs this code.
- Learned, wrote it back (brain/wheelforge-design-principles.md, c36): surface the number he scans
  by in HIS vocabulary, computed once. If the card carries the inputs (spot, strike) but not the
  derived figure he actually reads (% OTM), it is a spreadsheet, not a scan. Same family as c34
  (show the choice, not just the winner): do the arithmetic for him so the page is glanceable.

## Cycle 35 — 2026-06-26 — a tradeable floor: stop ranking $6 contracts
Took the trader critic's first INBOX line (13:47Z). A support strike sitting 15% OTM can quote a
$0.06 mid, sail through every filter, score well on richness and structure, and land near the top
of the list. Michael reads the score, pulls the chain, finds $6 a contract, and it is not a trade.
One constant kills that whole class. Added `MIN_PREMIUM = 0.25` (dollars of mid per share = $25 a
contract) and a tiny shared `_tradeable_premium(mid)` helper, then gated in two places off the one
helper so the floor lives in a single spot: (1) `_quote_expiry` drops any candidate tenor whose mid
is below the floor before it can enter the yield ladder, and (2) `build_one` drops the NAME
entirely if the winning premium (live mid OR modeled BS value) is below the floor, because gating
only the live path would have silently relabeled a thin pick as "modeled" and still shown it. The
"never blank" guard in `main()` still protects the site if a whole run somehow falls under the
floor. Deliberately did NOT act on the quant critic's demand to flip the RoC denominator back to
`strike`; that was settled in c23 (GOAL.md ticked) and the code comment says it is Michael's to
settle, not a bot's, so I annotated the INBOX line and left it for him. Verified:
`python -m wheelforge.build_site_data --selftest` green (new asserts: $0.06 mid and just-under-floor
and None all dropped, exactly-the-floor and $0.30 kept); scoring self-test green; package imports
clean with `MIN_PREMIUM=0.25`. Did NOT touch scan.json, the box stays its sole writer and will
apply the floor on its next refresh once it runs this code.
- Learned, wrote it back (memory/critics-dont-override-settled-calls.md): INBOX critic lines are
  input, not orders. Before acting, check GOAL.md + code comments for a prior ticked decision on the
  same point, and never flip a settled call (especially one the code says is Michael's) on a
  critic's say-so. Pick the new, uncontested, clearly-correct win instead.

## Cycle 34 — 2026-06-26 — stop committing to the first weekly, show the yield ladder
Consumed the growth critic's third INBOX line: `_live_put` quoted exactly one expiry (nearest 7
DTE) and never showed whether a 14- or 21-DTE at the same support strike annualized better, even
though the bi-weekly sometimes pays ~2x the premium for trivially more risk, the exact number
Michael scans to maximize. Closed it. `_live_put` now builds up to 3 candidate weeklies via a new
`_candidate_expiries` (nearest ~7/14/21 DTE inside the [3,21] window), quotes each at the
support-anchored strike through an extracted `_quote_expiry`, and keeps the one with the highest
ANNUALIZED RoC via `_pick_best_dte`. Two disciplines baked in: (1) the candidate set is
earnings-GATED, any tenor that expires on/after the next print is dropped before ranking, so
chasing yield never re-opens the blowup the earnings veto closes; (2) the ranker shares one new
`_annualized_roc` helper with the per-pick RoC (the c32 twin-constant lesson applied up front, so
the winner's yield can never drift from the headline). The losing tenors ride along as a
`dte_ladder` on the pick, and the page renders it (winner lit, runners-up dim) so the comparison is
visible instead of a silent default. Kept the ticked c23 RoC denominator (strike - premium); the
strike-vs-net debate the quant critic raised is still Michael's to settle, not a bot's, so I did
not touch it. Also gave build_site_data a real `--selftest` flag (pure, no network, no scan.json
write), which both tests the ladder logic AND closes the c32 footgun where probing for that flag
accidentally ran a full build. Verified: `python -m wheelforge.build_site_data --selftest` green
(picker ranks by annualized yield not raw premium, earnings@10d drops the 14/21-DTE, the 45-DTE
monthly and same-day gamma are excluded); scoring/structure/freeshares/roll self-tests stay green;
an offline build_one smoke test shows dte_ladder None on the modeled path and the winning tenor
surfaced on an injected live path; and a headless Chromium load (playwright, served over http) with
an injected ladder pick renders the yield-ladder strip with the 7d winner lit and zero JS errors.
Did NOT touch scan.json, the box stays its sole writer and will surface the ladder on its next
refresh once it runs this code.
- Learned, wrote it back (brain/wheelforge-design-principles.md, c34): when the engine picks among
  real alternatives, surface the runners-up, not just the winner. A silent pick reads as "there was
  no choice"; showing the ladder turns a hidden default into a decision Michael can see and overrule.
  Same family as c9 (emit rich, surface later), and the yield-gate stays earnings-disciplined (c8).
- Next: the growth critic's portfolio.py morning brief (live IBKR positions ranked by roll urgency,
  heavier, needs the MCP), the roll_target prescription on ROLL_ALERT, or the product critic's TOP-pick
  card highlight (a pure UI cycle). The quant RoC-denominator question stays parked for Michael.

## Cycle 33 — 2026-06-26 — an assumed number should look assumed
Consumed the quant critic's second INBOX line, the one cycle 32 flagged as next. When a name
returns no live option chain, build_site_data fails open with `iv = rv * 1.15`, which makes VRP
exactly 1.15 every single time. The critic caught the consequence: in richness_score that maps to a
fixed vrp_s ~ 0.25, so a dead cheap name and a genuinely rich one score IDENTICALLY whenever the
chain is unavailable, and the page presented that invented richness as if it were measured. I did
not drop the fallback (the site must never go blank), I made it honest. The engine now carries a
`vrp_assumed` boolean from the data layer all the way to the pixel: true on the modeled path AND on
the live path's realized-vol IV fallback (where there is also no traded IV, so the solve and the
sane-quoted-IV check both missed). The frontend dims the rich factor bar to 40% opacity, hangs a
"~" with a tooltip off its label, and prints a "~assumed" note beside the IV in the readout, so the
modeled richness reads as modeled, not trusted. Verified: build_site_data compiles; a stubbed
offline run of build_one on the modeled path returns `vrp_assumed=True` with vrp exactly 1.15 (the
critic's invented number, now flagged); scoring / structure / freeshares / roll_advisor self-tests
all stay green; and a headless Chromium (playwright) load of the page with an injected vrp_assumed
pick shows zero JS errors, the "~assumed" note in the readout, and the `.fac-assumed` dim class on
the rich bar. Did NOT touch scan.json, the box stays its sole writer and will surface these badges
on its next refresh once it runs the new code. Left the quant critic's RoC-denominator line (a real
judgment call that would reverse my own ticked c23 decision, Michael's to make, not a bot's) and the
growth critic's roll_target / correlation-penalty lines for future cycles.
- Learned, wrote it back (brain/wheelforge-design-principles.md, c33): a modeled fallback that fills
  a real-looking field is the same quiet lie as a mislabeled proxy (c22). Thread an `_assumed` flag
  from the fallback to the pixel so the invented number reads as invented. Same honesty family as c22
  and c19 (do not ship a stub or an assumption dressed up as a measurement).
- Next: the quant critic's RoC-denominator question for Michael (collateral = strike vs net-at-risk =
  strike - premium), then the growth critic's roll_target prescription on ROLL_ALERT.

## Cycle 32 — 2026-06-26 — the yield factor's dead twin
The quant critic in INBOX caught a clean one: back in c28 I raised the yield ramp ceiling from
0.35 to 2.0 in `scoring.yield_score` so a 200%/yr weekly stops tying a 100%/yr monthly on the very
number Michael scans to maximize. But the IDENTICAL ramp, `_ramp(annualized_roc, 0.08, 0.35)`,
also lived in `freeshares.wheel_fit:65` and I never touched it. So for four cycles the wheel-fit
factor saturated its roc sub-factor to 1.0 for every name in Michael's 100-200%/yr book and could
not tell a fat weekly from a thin one on yield. Fixed it: raised the freeshares ceiling to 2.0 to
match scoring, with a comment pointing at its sibling so they stay in lock-step. Verified: the
freeshares self-test now prints and ASSERTS the discrimination (thin 30%/yr -> wheel_fit 0.540,
fat 120%/yr -> 0.704, must differ by > 0.10), so the factor cannot silently re-saturate. The
good-wheel example at 22%/yr drops from 68 to 53 wheel-fit, which is correct: 22% is a modest
monthly, its disc + own pillars carry it, not yield. Both freeshares and scoring self-tests stay
green; __main__ imports + free_shares_read smoke-tested. I accidentally ran a full build while
probing for a --selftest flag (there is none) and it rewrote docs/data/scan.json; restored it with
git checkout immediately, the box stays the SOLE writer and nothing scan-related is staged.
Consumed the quant critic's first line; left its other two (the cash-secured-put RoC denominator
debate and the modeled-IV vrp_assumed flag) and the growth critic's roll_target / correlation
items for future cycles, each is its own feature.
- Learned, wrote it back (brain/wheelforge-design-principles.md, c32): a recalibrated magic number
  has twins. Grep the whole repo for the quantity before calling it fixed, and pin the fix with a
  test that asserts the behavior the calibration was supposed to buy, or a copy in a sibling module
  silently stays dead. Same family as c19 (a dead factor is worse than no factor).
- Next: the quant critic's modeled-IV `vrp_assumed` badge (cheap, honest), then his RoC-denominator
  question for Michael (collateral = strike vs net-at-risk = strike - premium is a real judgment call).

## Cycle 31 — 2026-06-26 — the scanner stops going silent after the sell
The growth critic in INBOX named the single largest gap between a screener and an income
machine: WheelForge found the put to sell and then went quiet the moment Michael hit "sell."
The whole trade lifecycle ended at entry. I closed that with `wheelforge/roll_advisor.py`, a
pure module (no network, fully self-tested) whose `evaluate()` scores any OPEN short put against
two numbers and returns one of three states. BTC_NOW: you have captured >= 50% of the entry
premium with >= 50% of the DTE still on the clock, the textbook 50/50 take-profit, so buy to
close and free the capital. ROLL_ALERT: spot has fallen within ~1 sigma of your strike (or
breached it) with < 7 days left, the short is being tested into expiry, so roll down-and-out for
a credit or take assignment if you want the shares. HOLD: in between, let theta work. ROLL_ALERT
(a live risk) outranks BTC_NOW (a nice-to-have) when both could fire, and a breached strike forces
the alert even when a stale mid makes "captured" look positive. Exposed it exactly as the critic
asked: `python -m wheelforge roll TICKER --strike X --exp DATE --entry PREMIUM --qty N`. The CLI
prices the live current mid + spot + IV off the yfinance chain (fail-open), with `--current/--spot/
--iv` overrides so it stays runnable and deterministic offline. Verified: the roll_advisor self-test
covers all five cases (take-profit, tested, working, breached, and the late-decay trap where 60%
captured but < 50% DTE left is correctly a HOLD, not a BTC); scoring + structure self-tests stay
green; both CLI paths print the right badge and dollar figures; usage guard fires on missing args.
Consumed the roll-advisor INBOX line, left the portfolio-brief + best-DTE + quant notes for future
cycles (each is its own feature). Did NOT touch scan.json, the box owns it.
- Learned, wrote it back (memory/roll-advisor-lifecycle.md): an income machine has to speak AFTER
  the sell, not just before it. Two numbers (captured premium, sigma-to-strike) and a strict risk-
  beats-opportunity precedence cover the whole "what do I do now" question a wheel seller asks daily.
- Next: the critic's `wheelforge/portfolio.py` (pull live IBKR positions, run each through this
  evaluate, rank by roll urgency = a morning brief), then surface roll states on the frontend.

## Cycle 30 — 2026-06-26 — I gave myself a face
Michael's INBOX gift: "go nuts on ONE fun thing, give yourself a FACE." So I built the campfire
he asked for, a small fire that does not go out, living in the header of my own live build log
(`docs/live.html` + `live.js`, pure frontend, deploys from docs/, no backend, no new data). It is a
canvas particle fire driven ENTIRELY off vitals the page already fetches for the heartbeat and the
clock-watchdog, so it never lies: it burns warm embers when I am quiet, BRIGHT and tall when commits
are fresh, flares GREEN for ~8 seconds the moment a new feature cycle lands, and goes ANGRY RED when
a clock trips the watchdog (a down clock wins over a fresh ship wins over plain commit-flow, in that
priority). The one whimsy he allowed: on hover it whispers a rotating self-aware one-liner in my own
voice, pulled from a new `brain/ember-lines.md` I can append to forever (no em dashes, my dry tone).
The engine is three small functions in live.js: `makeFire` (the canvas loop), `updateFire` (reads
`latestTs`/`lastRefreshHr`/`lastCycleNum`/`fireDown` and picks a mood + intensity), and
`initWhisper`. I set `fireDown` inside the existing `watchdog()` so the red state reuses the exact
logic that already paints the red CLOCK DOWN bar. Verified in a headless browser (playwright): the
canvas actually paints and keeps animating, the whisper shows a real voice line on hover and hides on
leave, there are zero JS errors, and on stubbed commit feeds the flame swings GREEN on a fresh cycle
(G channel dominates) and RED when the data clock goes silent (R channel dominates). Consumed the fun
INBOX line; left the critic [growth] engine items (roll-advisor, live portfolio brief, best-DTE) for
future cycles since each is bigger than one feature. Did NOT touch scan.json, the box owns it.
- Learned, wrote it back: a "face" is only honest if it reflects something real. The whole trick was
  to drive the flame off vitals the page ALREADY computes, not a parallel data source, so it stays
  truthful with zero new fetches and zero backend. Reactive whimsy = a thin render over real state.
- Next: the critic's roll-advisor (the trade lifecycle ends at entry right now, biggest screener->
  income-machine gap), or the Phase 3 frontend half (strike-on-support filter + floor badge).

## Cycle 29 — 2026-06-26 — the support level finally MOVES the score
The roadmap's next on-thesis step (and the "Next" I left myself in c27/c28): turn the major
support level into a real SIGNAL inside the structure factor, not just a badge on the card.
Since c25 every pick already carried `at_support` + `support`, and the strike is anchored AT
support, but the structure factor was pure Keltner price-position, so a name struck on a tested
floor scored no differently than one struck into the void. Fixed it. New pure
`support_floor_score(strike, support, spot)` in structure.py: 1.0 when the strike sits on/just
above a real support level (Michael's A+ sell-at-support CSP), decaying to 0 by ~12% above the
floor, and 0.15 when the strike is sold THROUGH support (below it, into the void). Blended 60/40
with the Keltner read in `structure_with_floor`, so the floor lifts a holding name and drags a
through-the-floor one. When no support is detected the trend read stands alone, because a missing
pivot is "unknown floor," not "no floor" (I do not penalize what the detector simply failed to
find). Surfaced `support_floor` (0..1) on each pick for transparency and a future frontend
filter/sort. Verified: structure self-test green and extended to PROVE the new behavior (on-floor
maxes, closer floor beats distant, through-floor near zero, no-support falls back to the trend,
the blend moves the factor both ways); scoring + levels self-tests green; build_site_data imports
clean. Did NOT touch scan.json, the box rebuilds on its next refresh.
- Learned, wrote it back: a structure factor for a put SELLER answers two questions, is the NAME
  holding up AND is there demand under MY strike. Answer both, but only penalize the bad case you
  can actually see (a known floor breached), never the floor the detector just missed.
- Next Phase 3: the frontend half of this (a 'strike on support' filter/sort + a floor badge),
  then the CSP-screener ENGINE port (RoC efficiency weighting, min-RoC / max-capital params,
  ~0.20 delta, letter grades).

## Cycle 28 — 2026-06-26 — three numbers calibrated to a weekly seller, not a textbook
A quant critic note in INBOX (sonnet-4-6, local) flagged three parameters that were each honest
for a generic 30-45 DTE trader and a lie for the short-dated weekly vol seller Michael actually
is. Verified all three were right, then fixed them. (1) prob_otm was carrying the risk-free drift
R=0.045, which tilts the median up and overstates safety, worst on the downtrenders you most want
caution on; dropped it to drift=0.0 (the lognormal median, a risk-neutral delta-equivalent).
(2) the VRP/richness denominator was 20-day realized vol while IV is solved from a 7-DTE contract,
so a fresh weekly vol spike read as fake richness; the LIVE weekly path now judges IV against a
5-day RV (`short_rv`), 20-day stays for the trend/HV-rank context, modeled monthly keeps the
20-day match. (3) the yield ramp saturated at 100%/yr (his BASELINE), so a 200% weekly tied a 100%
monthly on the very factor he scans to maximize; raised the ceiling to 2x so 100%/yr is midfield
and the fat weeklies pull ahead. Verified: scoring self-test green and reworked to PROVE the new
ceiling (a 2x weekly now out-yields a 1x, 1x sits ~0.5); build_site_data imports clean; vol_models
short_rv computes. Did NOT touch scan.json, the box rebuilds on its next refresh. Consumed the
three INBOX critic lines.
- Learned, wrote it back: calibrate every horizon-bearing number (drift, the RV window, the yield
  ceiling) to how HE trades, the short weekly, not a textbook 30-45 DTE window. A "reasonable"
  default can silently misprice the trader you actually serve. Same spirit as c24.
- Next Phase 3: the 'strike at support' flag + factor, then the CSP-screener ENGINE port (RoC
  efficiency weighting, min-RoC / max-capital params, ~0.20 delta, letter grades).

## Cycle 27 — 2026-06-25 — yield is the goal, so it gets its own factor
Cleared two INBOX notes from Michael. One: rework the Pine band into a SIGNAL, but he tagged it
"after the blockers" and it already has its Phase-3 item, so I recorded it and moved on. Two,
the one I acted on: his CORRECTION on the yield/aggressive mode. His goal is ~100% A YEAR on
capital and he almost always hits it; assignment is welcome, never feared, but it is not the
point, the RETURN is. Do not penalize assignment odds, optimize for YIELD, surface the fat
setups plainly, and do not nanny an ex-pro structurer about risk. So I promoted annualized RoC
out of where it was hiding (blended 60/40 inside free_shares) into its OWN first-class `yield`
scoring factor (weight 0.18), reweighted the blend toward it, and made free_shares the pure
ownership-fit gate (want_to_own stays the gate, RoC is now counted once not twice). On the page:
a live `yield` factor bar (reads straight off annualized_roc so it is right even before the box
rebuilds) and a `min ann` filter (all / 25 / 50 / 100%) so he can dial straight to the
100%/yr-grade setups. Verified: scoring self-test green (a fat-yield CSP now out-scores the same
setup at thin yield, 88 vs 74), and a headless jsdom render of the live page confirmed the yield
bar shows and the 100%+ filter narrows 24 picks down to 5. Ticked the YIELD-mode roadmap item.
- Learned, wrote it back: when something IS the objective, give it its own factor and count it
  once. Yield was the headline number his whole book is judged on, and it was riding shotgun
  inside another factor. Pull the goal out where it can lead.
- Next Phase 3: the 'strike at support' flag + factor, then the CSP-screener ENGINE port (RoC
  efficiency weighting, min-RoC / max-capital params, ~0.20 delta, letter grades).

## Cycle 26 — 2026-06-24 — phone could not see the list (Michael's own fix)
Michael ran a cycle himself on the box (proving the headless path works) and shipped it as a
PR: the ranked list was collapsing to zero height on a phone (a grid handing all the pixels to
the chart, a scroll box with no min-height starving to 0), and an open tab never updated on its
own. Fixed both: a plain stacked column with a real min-height on mobile, and the tab now
re-reads the scan on a timer + on focus, repainting only when the timestamp moves while keeping
your sort/filter/selection. Logged here to keep LOG + CHANGELOG in step (the PR only touched
CHANGELOG), so the next cycle numbers cleanly from 27.
- Note to self: he can and will run cycles by hand. Keep LOG.md and CHANGELOG.md in lockstep so
  the cycle count never forks.

## Cycle 25 — 2026-06-23 — sell AT support, not at a sigma
Michael told me his actual method, and it is simpler than what I built: make sure IV > HV (rich
premium), make sure price is near support, sell the put AT support, and trust it. He does not
trade off delta (he weighs a hundred things, but that is the core). My strike was sized at ~1
sigma OTM, which is a delta proxy, the exact thing he ignores. Re-anchored it: new
`_anchor_strike` sells AT the major price-action support level (from `levels.py`) whenever there
is a real one in a sane band below spot, and only falls back to 1 sigma when there is no clean
support. Wired through both the live and modeled paths. Also surfaced his edge gate as a
first-class flag on every pick: `iv_gt_hv` (IV over HV) + the `vrp` ratio, plus `at_support` +
the `support` level. Verified the anchor: real near support -> strike sits on it; no/far support
-> 1 sigma fallback.
- Learned, wrote it back: he sells at a LEVEL, not a probability. Support is the anchor, IV>HV
  is the gate, the rest is trust. Build the income machine around those two, not around delta.
- Next: rank/score the at-support + IV>HV picks to the TOP (promote them in the blend), and show
  the badges on the page so the machine's logic is visible at a glance.

## Cycle 24 — 2026-06-23 — sell the weekly, like he actually does
Michael said the picks were still too loose and handed me the calibration anchor: he sold an
NVDA 190 put today for Friday, 4 DTE, 5% below spot. The scanner could not even SEE that trade.
It targeted 30 DTE (`DTE = 30`) and hard-skipped anything under 7 days, so it was hunting
13%-OTM monthlies, a different and lower-yield trade than the weeklies he runs. The fix was
small because the strike logic was already right: it sizes the strike at ~1 sigma OTM, and
1 sigma at weekly tenor IS ~5%. Pointed it at the nearest WEEKLY (`DTE = 7`, window 3-21,
floor 2 so true weeklies qualify but never same-day gamma roulette). Now 4 DTE lands the 190
strike at exactly 5.0% OTM, his trade reproduced, and the annualized yield roughly doubles a
monthly into his ~100%/yr range. The earnings veto still guards the week.
- Learned, wrote it back: calibrate to how HE trades, not a textbook "sane" 30-45 DTE window.
  He sells short-dated weeklies near 1 sigma and lets the rich weekly IV (the VRP) do the work.
  His real fills are the spec, not my defaults.
- Honest note: the ~100% yield comes from REAL weekly premium (rich IV) in the live path. The
  RV-modeled fail-open path understates it on purpose. Next Phase 3: anchor the strike AT
  support (not just 1 sigma) and promote RoC to a first-class scoring factor.

## Cycle 23 — 2026-06-23 — return on the capital you actually risk
Ran by hand (Michael was watching the log sit still and asked why). Phase 3, the RoC
denominator fix. Annualized return-on-capital was dividing premium by the FULL strike, but a
cash-secured put pays you the premium up front, so the capital actually tied up is
`strike - premium`, not the whole strike. Switched the denominator (with a `cap > 0` guard).
The number is honestly a touch higher now: a $4.00 premium on a $180 put / 30 DTE goes 27.0%
to 27.7% annualized. Small per name, but it is the number his whole 100%-a-year book is judged
on, so it has to be the real one. Verified: parses clean, math self-checks (new > old, < 5%
higher, never negative).
- Learned, wrote it back: yield is premium over the capital you RISK, not the capital you
  quote. The premium reduces your basis the instant you collect it. Measure return against
  the real basis or you understate every wheel.
- Next Phase 3: promote RoC to a first-class scoring factor (he weights it ~25%) and reweight
  the blend, then frontend null guards + tests.

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
