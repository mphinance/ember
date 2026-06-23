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
