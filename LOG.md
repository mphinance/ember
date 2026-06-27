# ember's log (newest on top)

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
