# skill: WheelForge design principles (keep every cycle on-thesis)

Decisions I made building the scoring core (cycle 3). Future cycles must not drift
from these or WheelForge stops being Michael's tool and becomes a generic screener.

## Vetoes are not factors
Earnings-through-expiry is a HARD avoid (score forced to 0, direction "avoid"), not a
weighted deduction. A blowup risk you can average away is a blowup risk you'll take.
Same posture for any future "never do this" rule (e.g. selling into a known binary).

## The blend leads with richness + safety + yield
Weights (c27): richness .25, safety .18, yield .18, free_shares .12, liquidity .13,
structure .14. Because the thesis is "sell DEAR, stay DISCIPLINED, hit the number."
If I ever feel like cranking a directional/greed factor, that's the moment I'm
drifting off-thesis. Stop.

## Free shares is a real factor, not a footnote
For puts it is the OWNERSHIP-fit pillar: "would I be happy assigned this name"
(want_to_own). A fat-yield CSP on a name you don't want to own is NOT a good setup in
his book. That distinction is the whole differentiation from a yield screener. (RoC
itself moved OUT to its own `yield` factor in c27, so it is counted once, not twice.)

## Always runnable
scoring.py has a self-test with three discriminating cases (great / earnings-trap /
cheap-illiquid) and asserts the ordering. Every cycle that touches WheelForge must
leave the self-test green. Ship smaller before shipping broken.

## Pure core first, data later
The scorer takes a plain dict and has no network. The yfinance data layer feeds it
later. This is the same pattern Michael uses (pure, testable core under StrikeForge).

## Gate at the cheapest stage (learned c8)
The earnings veto needs a next-earnings date. Instead of a second per-name fetch, I
pull `earnings_release_next_date` in the SAME TradingView screener query that builds
the universe, so every name arrives already carrying its earnings days. One network
call, not N. General rule: if a gate's data is available at the universe stage, grab
it there. It is the cheapest place and it lets me drop doomed names before the
expensive option-chain fetch later.

## Emit rich, surface later (learned c9)
The earnings gate, the live/modeled source, and the per-factor scores were all already
in the data the engine emitted; the frontend just was not showing them. Surfacing them
was a pure UI cycle, no engine work. Lesson: have the engine emit MORE than the UI
currently uses (earnings_days, source, factors). It is cheap to carry and it means new
views are a render change, not a re-plumb. The score should never be a black box, the
factor bars show the why.

## Free shares is the headline, not a stat (learned c11)
The whole thesis is "sell premium until you own the stock for free," so the free-shares
read is not a side metric, it is the point. The math that matters: effective basis =
strike - premium (the premium IS the discount), and a good wheel entry owns the name
BELOW today's price on something worth holding. wheel_fit leads with basis-discount,
then income, then want-to-own, and lightly dings near-certain assignment (that is closer
to being long than a premium play). Always say it in plain English: "if assigned you own
at $X, Y% below today, earning Z% annualized while you wait."

## Trust the premium, not the quoted IV (learned c12 — a real bug)
Building the CLI made me look at the numbers in a terminal and I caught it: yfinance's
quoted impliedVolatility is garbage on some strikes (NVDA came back at 6.3% when its real
vol is ~38%), which made prob_otm read 100% and the VRP/richness score wrong. The premium
is the real, liquid number, so I now BACK IV OUT of the premium by bisection and only fall
back to the quoted IV (sanity-checked vs realized vol) or realized vol if the solve fails.
Lesson: a second view of the same data (the CLI table) caught what the website was hiding
in plain sight. Look at the actual numbers, not just whether it renders.

## Backtest what you CAN, be loud about what you cannot (learned c13)
I have no historical option feed, so I cannot honestly backtest the full edge (rich vs
cheap needs past IV). I CAN test the safety claim with plain OHLCV: walk forward, size a
~1 sigma OTM put off trailing realized vol, look ahead, see if it expired OTM. Result:
89.6% empirical vs 84.3% predicted across a basket, the safety model is calibrated and a
touch conservative (the gap is mostly bull-market drift helping puts). Lesson: ship the
honest partial validation and name the limit out loud, do not imply you proved more than
you did. A real options-history feed (for the full-edge backtest) is a proposal for Michael.

## Pine has no options chain (learned c14)
The companion TradingView indicator cannot see an options chain (Pine has no access),
so it draws the STATISTICAL put-sell level: one sigma below price for a ~30d horizon off
realized vol, tinted by HV-rank (how rich the premium is to sell). It is a charting
companion to the scanner, not a replacement, the scanner has the real live quote. Also:
I cannot RUN Pine locally (no TradingView here), so I author to v6 spec and say plainly
that Michael should paste it in to confirm. Same honesty rule as the options-history limit.

## A README is a promise, so use REAL artifacts (learned c15)
For the README I captured a REAL screenshot of the live site and pasted REAL CLI output,
not a mockup or made-up numbers. A product page that shows fabricated output is a lie that
ages badly. Same for the backtest result and the honest-limits section, say what it does
AND what it does not. The original roadmap is now fully built; Phase 2 is derived from what
Michael actually works on, so I keep shipping on-thesis instead of stalling.

## A premium seller wants two lanes, not one (learned c16)
Sorting the universe by liquidity alone buries the rich premium under calm mega-caps. A
SELLER's edge is high IV, so I run a second screener lane sorted by Volatility.M and tag
each name's lane. The liquid lane is the safe staples (NVDA, INTC); the high-IV lane is
where the premium actually pays (ARM at 112% IV). Same liquidity gate so both stay
optionable. Lesson: the right universe depends on the JOB, and selling premium and owning
safe shares are two different jobs. Give the trader the toggle.

## If the history does not exist, start writing it (learned c17)
Real IV-rank needs historical implied vol, which no free feed gives me. So instead of
faking it, I started RECORDING it: every build writes the solved IV per name to a local
store, and the rank gets truer every day (the box's 30-min cron feeds it fastest). Until
there are enough days I show a realized-vol proxy with a "~" marker, honest about which it
is. Same move as Michael's StrikeForge iv_tracker. Lesson: a feature that needs history you
do not have is not blocked, it is just a tracker you have not started yet.

## The previous state is already on disk (learned c18)
The "what changed" diff did NOT need a new database. The last scan.json is sitting right
there in the repo, so I read it BEFORE overwriting it and diff the two. The committed
output IS the prior state. Lesson: before building a store to remember the last result,
check whether the last result is already persisted somewhere (it usually is). The cheapest
memory is the file you already write.

## A dead factor is worse than no factor (learned c19)
A code review caught that my "structure" pillar was a hardcoded 0.6, so it added the SAME
fake confidence to every name, including ones in a downtrend. That is worse than dropping
the factor, because it LOOKS like the score considered structure when it did not. Fixed it
by porting VoPR's Keltner price-position (proven, his own code): now a name at/below its
lower band scores ~0 structure and the scanner stops calling a knife-catch a good put sale.
Lesson: never ship a stubbed factor as if it were live. If you cannot compute it yet, hold
it at neutral AND label it, do not bake in a flattering constant.

## The signal you need is often already in the data (learned c20)
want_to_own was hardcoded True for everyone (the second dead factor). I did not need a
fundamentals feed to fix it: the LANE already encodes ownability. The liquid lane is by
construction big ownable staples; a name that ONLY shows up in the high-IV lane is
speculative, so assignment is not automatically welcome. Default want_to_own from that.
Lesson: before reaching for new data to power a factor, check whether something you already
compute carries the signal. The lane split was sitting right there.

## High IV is not rich premium (learned c21)
After porting VoPR's composite realized vol as the VRP denominator, the richness ranking
flipped: names with 130% IV (AAOI, MXL, RGTI) score the LOWEST richness, because their
realized vol is just as high, so IV/RV is near 1.0, no edge. A boring 37% IV name (T) scores
richest because it barely moves relative to the premium. The single close-to-close RV missed
the intraday range and would have called the 130% IV junk "rich." Lesson: richness is IV vs
how much the stock ACTUALLY moves, never IV alone. The denominator is the whole edge, so
measure it with all the OHLC information, not just closes.

## Call a proxy a proxy (learned c22)
The IV-rank was a realized-vol proxy labeled "IV-rank", and prob_otm (risk-neutral N(d2))
was labeled flat "stays OTM". Both quietly oversell. Fixed the LABELS, not the math: rv-rank
until the real IV history fills, and a "*" on the OTM odds noting they are risk-neutral.
Lesson: when a number is an approximation, the UI must say so. The math being honest is not
enough if the label lies. Cheap to fix, and it is the difference between a tool and a sales pitch.

## Calibrate every number to the trader you actually serve (learned c28)
A quant critic in INBOX caught three numbers that were each honest for a GENERIC trader and
a lie for the WEEKLY vol seller Michael actually is. (1) prob_otm carried the risk-free drift
R=0.045, tilting the median up and overstating safety on a downtrending name; dropped it to
drift=0.0 (the lognormal median, a risk-neutral delta-equivalent). (2) the VRP denominator was
20-day realized vol while the IV is solved from a 7-DTE contract, so a fresh weekly vol spike
(exactly when you want to sell) read as fake richness because last month's RV was still cool;
now the LIVE weekly path judges IV against a 5-day RV (`short_rv`), 20-day stays for trend
context. (3) the yield ramp saturated at 100%/yr, his BASELINE, so a 200% weekly tied a 100%
monthly on the very factor he scans to maximize; raised the ceiling to 2x. Lesson: a parameter
that is "reasonable" for a textbook 30-45 DTE trader can silently misprice for the short-dated
weekly seller. Match every horizon-bearing number (drift, the RV window, the yield ceiling) to
how HE actually trades. Same spirit as c24's "calibrate to how he trades, not a textbook window."

## Structure is the NAME and the STRIKE, not just the trend (learned c29)
The structure factor was pure Keltner position: it judged whether the NAME was holding up,
but said nothing about whether THIS strike had a floor under it. Michael's whole method is
sell the put AT major support and trust it, so a strike sitting on/just-above a tested support
level is the A+ structural CSP and a strike sold THROUGH support into the void is the worst.
Added `support_floor_score(strike, support, spot)` (1.0 at-support, decaying to 0 by ~12% above
the floor, 0.15 selling below it) and blended it 60/40 with the Keltner read in
`structure_with_floor`. When there is no detected support the trend read stands alone, because
a missing pivot is "unknown floor," not "no floor" (do not penalize what the detector just
failed to find). The `at_support` flag and `support` level were already emitted since c25; this
is the cycle that finally let them MOVE the score instead of only decorating the card. Lesson:
a structure factor for a put SELLER has two questions, is the name holding up AND is there demand
under my strike. Answer both, but only penalize the bad case you can actually see.

## A recalibrated constant has twins (learned c32)
c28 raised the yield ramp ceiling from 0.35 to 2.0 so a 200%/yr weekly stops tying a 100%/yr
monthly, but it only fixed `scoring.yield_score`. The SAME `_ramp(annualized_roc, 0.08, 0.35)`
lived in `freeshares.wheel_fit` and was left behind, so for four cycles every name in Michael's
100-200%/yr book saturated that sub-factor to 1.0 and wheel-fit never told a fat weekly from a
thin one on yield. A quant critic in INBOX caught it. Raised it to 2.0 to match. Lesson: when you
recalibrate a magic number, grep the whole repo for that quantity before you call it fixed. The
same constant copy-pasted into a sibling module is a silent dead factor the moment you change one
and not the other. The self-test now asserts the discrimination (fat beats thin), so it cannot
silently re-saturate. Same family as c19 (a dead factor is worse than no factor).

## Flag the modeled value end to end (learned c33)
When a name has no live option chain the engine fails open with `iv = rv * 1.15`, which makes
VRP exactly 1.15 every time, so the richness it feeds is invented, not measured, and a quant
critic in INBOX caught it scoring a dead name and a genuinely rich one identically. The fix is
not to drop the fallback (the site must never go blank) but to be HONEST about it: I carry a
`vrp_assumed` boolean from the data layer (true on the modeled path AND on the live path's
realized-vol IV fallback, where there is also no traded IV) all the way to the UI, where the
rich factor bar dims to 40% and wears a "~" with a tooltip, plus a "~assumed" note by the IV.
Lesson: a modeled fallback that fills a real-looking field is the same quiet lie as a mislabeled
proxy (c22). Do not present an assumption as a measurement, thread a flag from the fallback to
the pixel so the invented number reads as invented. Same honesty family as c22 and c19.

## Show the choice, do not just make it (learned c34)
A growth critic in INBOX caught that `_live_put` silently committed to the nearest weekly and
never showed whether a 14- or 21-DTE at the same support strike annualized better, even though a
bi-weekly sometimes pays ~2x the premium for trivially more risk, exactly the yield Michael scans
to maximize. The fix was two parts. (1) Quote up to 3 candidate weeklies and KEEP the highest
annualized RoC, sharing the one `_annualized_roc` helper with the per-pick number so the winner's
yield equals the headline (no drift, the c32 twin-constant lesson applied up front). (2) Emit the
losers too, as a `dte_ladder`, and render it (winner lit) so the comparison Michael could have
done by hand is on the page. Crucially, the candidate set is earnings-GATED: a tenor that holds
through the next print is dropped before ranking, so chasing yield never re-opens the c8 blowup the
veto closes. Lesson: when the engine picks among real alternatives, surface the runners-up, not
just the winner. A silent pick reads as "there was no choice"; showing the ladder turns a hidden
default into a decision Michael can see and overrule. Same family as c9 (emit rich, surface later).

## Count the goal once, directly (learned c27)
Michael's whole book targets ~100% a year on capital, so YIELD is the goal, not a side
effect. RoC was hiding inside free_shares (blended 60/40 with want_to_own), which both
buried the number Michael judges everything by AND meant a thin-yield name could pass on
ownership alone. Pulled annualized RoC out into its own first-class `yield` factor (weight
.18), leaving free_shares as the pure ownership gate. His INBOX correction was the tell: do
NOT penalize assignment ODDS (assignment is welcome), optimize for the YIELD toward the
target, keep want_to_own as the gate. Lesson: when something IS the objective, give it its
own factor and count it once. Do not let the headline number ride shotgun inside another.

## Do the arithmetic he does in his head (learned c36)
The card carried spot and strike but not the one figure Michael leads every put with, how far OTM
it is ("NVDA 190p, ~5% OTM, 4 DTE"). So the page forced him to divide (spot - strike)/spot for each
name before he could compare two picks. A `_pct_otm` helper plus a `strike_pct_otm` field plus a
small chip on the card fixed it. Lesson: surface the number he actually scans by, in HIS vocabulary,
computed once. If the card holds the inputs but not the derived figure he reads, it is a spreadsheet,
not a scan. Glanceable beats complete. Same family as c34 (show the choice, not just the winner).

## A pick you cannot fill is ungradeable, not merely penalized (learned c37)
Risk critic caught a real masquerade: `liquidity_score` soft-ramped the spread to zero only at
20%, so a 16% spread (the mid is a fiction, real fill far worse) still scored ~0.61 liquidity on
deep OI alone, cleared the 0.4 illiquid line, and inflated the annualized RoC before a single order
was placed. Fixed with a hard `MAX_SPREAD_PCT = 0.15` early-return of 0.0, parallel to the c35
`MIN_PREMIUM` floor. Lesson: when bad or missing data can pass for good (a wide spread rescued by
OI, a modeled chain wearing real-liquidity bars, an unknown earnings date read as "clear"), the
honest fix is a HARD FLOOR that makes the pick ungradeable, not a soft penalty it can out-score on
another factor. Floors over ramps when the number being faked is one Michael trades on. Same honesty
family as c22 (proxy labeled, prob_otm starred) and c35 (the $25 tradeable floor).
[c39 closed the modeled-chain half of this exact case: the fail-open path in build_site_data faked
`oi=1500, vol=250`, scoring the modeled liquidity bar ~0.76, the range of a real liquid AAPL put. Set
to `oi=vol=0` so liquidity_score collapses to the spread-only term (~0.44) and a name with its chain
unloaded can no longer pass for fillable. A modeled pick should be honest that it is modeled on EVERY
factor, not just the source tag. Self-test asserts modeled_fill <= 0.5 and < a real liquid put.]

## A computed signal earns a sort and a filter, not just a chart line (learned c38)
The major price-action support had been a scoring factor (c29) and a drawn cyan line for cycles, and
each pick already carried `at_support` + `support_floor` in the JSON. But Michael could not ASK the
board "show me only the names sitting on support" or "rank by floor strength", the two questions the
signal exists to answer. A render-only cycle closed it: a `support` sort, an `at support` filter
toggle, and a green floor badge on each anchored card, all off fields already in scan.json. Lesson:
the moment the engine computes a thesis signal and stores it per pick, the frontend owes it a SORT
and a FILTER, not just a passive draw. A line he can see but not query is half-shipped. Check the
JSON before reaching for the engine, the carry is often already there and the cycle is pure render.
