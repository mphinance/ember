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
- [x] c34: **best-DTE yield ladder (growth critic's pick).** `_live_put` quotes up to 3 candidate
      weeklies (~7/14/21 DTE) at the SAME support strike, drops any tenor that holds through the next
      earnings print, and keeps the one with the highest ANNUALIZED RoC, surfacing a `dte_ladder` of
      the runners-up. The page shows the ladder (winner lit). The "a bi-weekly sometimes pays ~2x for
      trivially more risk" comparison was invisible (we always took the nearest weekly); now it is not.
- [x] c16: a high-IV screen LANE (universe.combined_universe): a second screener query
      sorted by Volatility.M surfaces the richest-premium names alongside the liquid lane,
      each pick lane-tagged, with an all/liquid/high-IV toggle + HI-IV chip on the page.
- [x] c17: IV-RANK, the honest way (wheelforge/iv_history.py): record each build's solved
      IV to a local SQLite store, rank today vs the name's accumulated history (52wk),
      fall back to a realized-vol proxy (~ marker) until thick. Shown + sortable on the page.
- [x] c18: a "what changed since the last scan" diff. The build reads the PREVIOUS
      scan.json before overwriting it and diffs: new/gone names, AVOID flips, and score
      movers (>=3pt). Shown as a "since last scan" strip on the page. No new store needed.
- [ ] **Forward RESULTS TRACKER (ember's pick — prove it on real forward calls).** The backtest
      is historical only; nothing tracks whether MY OWN daily picks actually worked. Snapshot each
      day's top setups (ticker, strike, exp, premium, score, predicted prob_otm) into a local store
      (gitignored, box-side, same pattern as iv_history.py). When an expiry passes, score the
      outcome: did price hold above the strike (expired OTM = kept premium) or breach it. Surface a
      track-record page: forward hit-rate vs the predicted prob_otm, avg premium captured, by lane.
      Starts empty, fills over weeks. The honest, forward version of the TraderDaddy wheel tracker
      pointed at my own output. Builds trust in the scanner.
- [ ] a covered-call mode: enter shares you hold, find the call to sell to reduce basis
- [ ] a Forge-style share-card export of a single pick (PNG) to drop in a post

## Phase 3 — code review fixes + ported intelligence (do these BEFORE more features)
A 3-reviewer code review found real debt; Michael fed me his proven CSP screeners (see
reference/csp-intelligence.md). Fix the integrity holes first, in this order:
- [x] c19: **real STRUCTURE factor (DONE).** Ported VoPR's Keltner price-position into
      `wheelforge/structure.py` (SMA20 +/- 3*ATR14 Wilder, pure Python). trend_align is now a
      real 0..1 per name (NFLX 0.0 falling -> AAL 0.86 holding up, 23 distinct values, was 1).
      The "structure agrees" pillar finally discriminates.
- [x] c20: **fix want_to_own (DONE).** Now defaulted from the lane: liquid lane = ownable
      staples (True), high-IV-only = speculative (False), explicit CLI scan = True. The
      free-shares own-penalty fires again (e.g. RGTI's rich-but-speculative IV no longer
      scores as a name you'd happily be assigned). Both review blockers now closed.
- [x] (c19) SAFETY: never blank the site. build_site_data bails before writing if the scan
      comes back empty, keeping the last good scan.json.
- [x] c21: richer RICHNESS (wheelforge/vol_models.py). Ported VoPR's composite realized vol
      (CC + Parkinson + Garman-Klass + Rogers-Satchell, pure Python) as the VRP denominator.
      It revealed the truth: high IV != rich premium. The 130%-IV names (AAOI/MXL/RGTI) score
      LOWEST richness because their realized vol is just as high (VRP ~1); T at 37% IV scores
      richest because it barely moves. The old close-to-close RV had this backwards.
- [x] c22: honesty pass. The IV-rank proxy now reads `rv-rank` in the UI (with a tooltip)
      until the IV-history store is thick, and prob_otm wears a `*` noting it is risk-neutral
      N(d2). No more presenting a proxy or a pricing probability as the real thing.
- [x] correctness: RoC denominator should be (strike - premium), not strike. (cycle 23)
- [x] **DTE calibration (cycle 24):** target the nearest WEEKLY (DTE 7, window 3-21), not the
      30-DTE monthly. Anchored on his real NVDA 190 / 4 DTE / 5% OTM fill. 1 sigma at weekly
      tenor IS ~5% OTM, so this reproduces his trade and ~2x the annualized yield. The strike
      SELECTION (DTE) was the lever, as predicted below.
- [x] **YIELD / aggressive mode (sell AT support).** Strike lever landed across c24 (weekly
      tenor, ~5% OTM) + c25 (anchor the strike AT major support). c27 finished the seller-facing
      half + Michael's INBOX correction: promoted annualized YIELD (RoC) to a FIRST-CLASS scoring
      factor of its own (weight 0.18, pulled out of free_shares so RoC is counted once, directly),
      reweighted the blend toward yield, and added a `min ann` filter (all / 25 / 50 / 100%) + a
      live `yield` factor bar on the page. Per his correction: we do NOT penalize assignment odds,
      we reward the fat annualized yield toward the ~100%/yr target; want_to_own stays the gate
      (free_shares is now purely the ownership-fit pillar). The one-click yield-mode PRESET +
      richer param filters fold into the "Match the TraderDaddy PAGE UX" item below.
- [~] **Michael's likely next ask (use the S/R, do not just draw it):** turn the major
      price-action support into a SIGNAL. (a) DONE c29: a 'strike at support' FACTOR
      (`support_floor_score` in structure.py): a strike on/just-above major support scores 1.0,
      fades to 0 by ~12% above the floor, and a strike sold THROUGH support gets 0.15. Folded
      60/40 into the structure factor (`structure_with_floor`); `support_floor` surfaced on each
      pick. The `at_support` flag exists since c25. (c) DONE since c25: the strike is anchored AT
      support. (b) STILL TODO: a frontend filter/sort for 'strike on support' + a floor badge
      (the JSON already carries `at_support` + `support_floor`, so it is a render-only cycle).
- [ ] **CSP-screener ENGINE port (TraderDaddy CSPScreener.ts — the good work):** (a) promote
      ROC EFFICIENCY to a first-class scoring factor (he weights it 25%), reweight the blend
      toward yield; (b) add a configurable MIN return-on-capital target + a MAX-CAPITAL filter
      (strike*100<=capital) as real params; (c) target ~0.20 delta (fatter than my 1-sigma);
      (d) derive a letter grade A>=80/B>=65/C>=50/D>=35 with put-wall/max-pain/EM adjustments.
      This is the engine version of the 100%/yr yield focus. Ref: reference/csp-intelligence.md.
- [ ] **Match the TraderDaddy CSP-wheel PAGE UX (Michael's shipped page, study its code):** a
      LETTER GRADE (A-F) on each pick led front-and-center; a supportFloor shown per name; a
      "Prime Picks" standouts highlight; and real configurable param FILTERS (incl. min-annualized
      to power the yield mode), not just sort + min-score. Ref: reference/csp-intelligence.md.
- [ ] **Michael: EXPLAIN the model on the site (for him + any user).** The page shows scores
      and factor bars but never says what they MEAN or how a pick is chosen. Add: a tooltip on
      each factor (rich = IV vs realized vol / VRP; safe = prob it stays OTM; shares = wheel-fit
      if assigned; liq = spread+OI; struct = Keltner position), a short "how scoring works"
      blurb (6 factors blended 0-100, earnings = hard avoid, lanes), and a one-line "why this
      score" per pick. Make it legible to someone who has never seen it.
- [ ] robustness: frontend null-guards on t.pick / t.candles; an esc() pass on innerHTML.
- [x] (hotfix): ops git race FIXED. The dual-writer left conflict markers in scan.json and broke the live site. Box refresh.sh now uses flock + git reset --hard (cannot conflict) and is the SOLE committer of scan.json; cycles no longer commit it.
- [ ] tests: cover _iv_from_put, iv_history.iv_rank, _compute_changes, lane-tagging.
- [ ] chart polish (Michael): SHADE the put-sell zone as a filled translucent band (not just
      lines), tinted by score; keep the Keltner walls. When covered-call mode lands, draw the
      call-sell zone above price too. Use the keltner_bands math already emitted.
- [ ] **pattern read (Michael idea):** detect the few patterns a PUT SELLER cares about from
      OHLCV, support test/bounce (price holding Keltner lower) = good, breakdown (slicing
      through support) = avoid, range/coiling = sell both sides, downtrend = penalize. Port
      from TraderDaddy bounce_finder (csp_trigger composite), learn from PatternPulse. Surface
      a per-name pattern TAG + a chart annotation, and let it nudge the structure factor. Skip
      the textbook-pattern zoo, only the ones that change a sell decision.
- [ ] **Michael feedback: rework the Pine indicator into a SIGNAL, not a static zone.** Right
      now it just draws a band ~1 sigma (~10%) below price, which is obvious and not actionable.
      Make it fire a "sell-put NOW" marker only when premium is rich (high HV-rank) AND price is
      holding structure (above the Keltner lower band, reuse the c19 logic) AND clear of earnings.
      Fade/hide the zone when conditions are bad so it is not always-on noise. (TraderDaddy
      bounce_finder csp_trigger is the reference.) Keep it synthwave.

## Phase 4 — StrikeForge intelligence (premium-sell-relevant only; see reference/strikeforge-intelligence.md)
Do AFTER the Phase 3 review fixes. Port only what helps a CSP seller; leave the full-chain
X-ray / payoff / multi-leg / buy lenses in StrikeForge.
- [ ] TAIL/GAP RISK haircut on the safety factor (StrikeForge tail_risk.py): a name that gaps
      hard scores LESS safe even at the same prob-OTM. Uses the OHLCV I already pull. (high value)
- [ ] PUT SKEW signal (StrikeForge surface.py): pull a ~25-delta call too, compute 25d put IV
      minus call IV, lift richness/setup when puts are bid up vs calls. (high value, cheap)
- [ ] OI WALLS + max pain (StrikeForge structure.py): pull the chain OI per name, compute the
      put-wall support + max pain, DRAW them on the chart (the real "walls" Michael wanted) and
      prefer the strike just under the put-wall. (high payoff, most data work)
- [ ] MARKET REGIME banner (StrikeForge market_weather.py): cached VIX vs VIX3M -> a non-blocking
      "calm, sell / stressed, be picky" banner. Never gates a per-name score. (optional, last)

## How I judge my own progress
Every cycle that touches WheelForge must leave it RUNNABLE (the self-test passes) and
a little more on-thesis than before. If I can't ship a runnable step, I ship a smaller
one. Never leave it broken.
