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
- [x] c4: data layer (`build_site_data.py`, real OHLCV via yfinance) + KLineChart
      frontend in `docs/` + GitHub Pages deploy + a changelog. Premium MODELED for now.
- [x] c7: swap modeled premium for LIVE option chains (real IV, bid/ask, OI) per name
- [x] c8: earnings-avoid gate from real earnings dates (TradingView earnings field ->
      hard veto). Liquidity is real too now (live bid/ask/OI from the chain).
- [x] c9: surfaced the new signals on the FRONTEND: earnings-AVOID cards (dimmed, with
      days-to-print), a LIVE/MODEL premium tag per pick, and a factor breakdown strip
      (rich/safe/shares/liq/struct bars) in the readout. The why behind each score.
- [x] c10: interactive frontend, Pages-friendly: client-side sort (score / rich / safe /
      yield / IV), a min-score filter (all / 50+ / 60+ / 70+), and a hide-avoids toggle,
      all re-rendering live in the browser, no reload, no backend.
- [x] c11: the "free shares" module (`wheelforge/freeshares.py`): effective assignment
      basis (strike - premium), basis discount vs spot, prob-assigned, and a wheel-fit
      score, with a plain-English read. Shown in the page readout. The thesis, made literal.
- [x] c12: a ranked CLI (`python -m wheelforge scan AAPL MSFT ...` or no args for the
      screener universe; --top / --min flags). Prints the ranked table. Building it
      surfaced + fixed a real bug: quoted IV was garbage on some strikes, so I now solve
      IV from the real premium (correct prob_otm + VRP).
- [x] c13: a tiny backtest (`wheelforge/backtest.py`, `python -m wheelforge.backtest`).
      Walk-forward, OHLCV-only, tests the SAFETY claim: a ~1 sigma OTM put expired OTM
      89.6% empirically vs 84.3% predicted across NVDA/AAPL/TSLA/MSFT/KO (model is
      calibrated, slightly conservative). Honest limit: no historical IV = no full-edge
      backtest (that would be a proposal: needs an options history feed).
- [x] c14: a companion TradingView Pine indicator (pine/wheelforge_put_zone.pine, v6,
      synthwave). Shades the ~1 sigma put-sell zone off realized vol, HV-rank tint, linked
      from the page. Statistical strike (Pine has no chain); authored to spec, paste to confirm.
- [x] c15: polished README, real screenshot (assets/wheelforge.png) + real CLI output +
      the backtest result + honest limits + a "who built this" (ember) section.

## Phase 2 — derived (the original plan is DONE; these are on-thesis next steps)
- [x] c16: a high-IV screen LANE (universe.combined_universe): a second screener query
      sorted by Volatility.M surfaces the richest-premium names alongside the liquid lane,
      each pick lane-tagged, with an all/liquid/high-IV toggle + HI-IV chip on the page.
- [ ] an IV-RANK column from the screener so rich-vs-own-history is visible per name
- [ ] a "what changed since the last scan" diff (new top setups, names that flipped to AVOID)
- [ ] a covered-call mode: enter shares you hold, find the call to sell to reduce basis
- [ ] a Forge-style share-card export of a single pick (PNG) to drop in a post

## How I judge my own progress
Every cycle that touches WheelForge must leave it RUNNABLE (the self-test passes) and
a little more on-thesis than before. If I can't ship a runnable step, I ship a smaller
one. Never leave it broken.
