# skill: WheelForge design principles (keep every cycle on-thesis)

Decisions I made building the scoring core (cycle 3). Future cycles must not drift
from these or WheelForge stops being Michael's tool and becomes a generic screener.

## Vetoes are not factors
Earnings-through-expiry is a HARD avoid (score forced to 0, direction "avoid"), not a
weighted deduction. A blowup risk you can average away is a blowup risk you'll take.
Same posture for any future "never do this" rule (e.g. selling into a known binary).

## The blend leads with richness + safety
Weights: richness .28, safety .24, free_shares .20, liquidity .14, structure .14.
Because the thesis is "sell DEAR and stay DISCIPLINED." If I ever feel like cranking
a directional/greed factor, that's the moment I'm drifting off-thesis. Stop.

## Free shares is a real factor, not a footnote
For puts it blends annualized RoC with "would I be happy assigned" (want_to_own). A
high-yield CSP on a name you don't want to own is NOT a good setup in his book. That
distinction is the whole differentiation from a yield screener.

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
