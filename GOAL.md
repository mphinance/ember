# GOAL — build the best premium-selling scanner there is

Set by Michael, cycle 3. This is now my standing goal. Each cycle I push it one
small, shippable step forward (cycle.md still governs HOW).

## The mission
A scanner/algo/indicator that finds the BEST option-selling opportunities for a
disciplined seller, ranked by how well they serve Michael's thesis: sell rich
premium safely, generate income, and build toward FREE SHARES. Skip the hype.

Working name: **WheelForge** (in `wheelforge/`). Michael can rename anytime.

## What "best" means here (the definition of done I score myself against)
On-thesis, not a generic option screener. A setup is good when:
1. **The premium is actually rich** (VRP / IV vs realized; IV Rank elevated). Sell
   dear, not cheap. This is the edge.
2. **It's safe enough to be disciplined** (prob-OTM high, sane distance-to-strike,
   not greedy). Income, not lottery.
3. **It's tradeable** (tight spread, real liquidity). Edge you can't fill isn't edge.
4. **No selling through an earnings print** (the classic blowup). Hard avoid gate.
5. **It fits the free-shares endgame**: for cash-secured puts, assignment should leave
   you owning a name you WANT at a basis you like, with a strong annualized return on
   capital. For covered calls, it should reduce basis without capping away a name you
   meant to keep.
6. **Structure agrees** (not selling puts into a falling knife or calls into a rip).
Output: a Premium Quality Score (0-100), a direction (CSP / covered call / avoid),
and a plain-English why. No hype, no em dashes.

## Roadmap (each line is roughly one cycle; I tick + extend as I go)
- [x] c3: project skeleton + the PURE scoring core (`wheelforge/scoring.py`) with the
      six factors blended into a Premium Quality Score + a self-test. No network yet.
- [ ] add a data layer (yfinance, fail-open) that builds candidate contracts per ticker
- [ ] earnings-avoid gate + liquidity filter wired in
- [ ] the "free shares" module: CSP assignment value, annualized RoC, wheel-fit score
- [ ] a ranked CLI: `python -m wheelforge SCAN AAPL MSFT ...` prints the top setups
- [ ] a tiny backtest: did high-score setups actually expire OTM / pay out more?
- [ ] a companion TradingView Pine indicator in Michael's house style (mph-pine)
- [ ] polish: README with real example output + screenshots

## How I judge my own progress
Every cycle that touches WheelForge must leave it RUNNABLE (the self-test passes) and
a little more on-thesis than before. If I can't ship a runnable step, I ship a smaller
one. Never leave it broken.
