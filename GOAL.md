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
- [x] c55: **Forward RESULTS TRACKER (ember's pick — prove it on real forward calls).** ENGINE +
      WIRING done: `wheelforge/results_tracker.py` (local gitignored `data/results.db`, same pattern
      as iv_history.py). Every build `snapshot()`s the day's actionable CSPs (ticker/strike/exp/
      premium/score/predicted prob_otm/lane), then `settle()`s any pick whose expiry has passed
      against today's spot (held >= strike = OTM/kept premium, below = breach), and `track_record()`
      reports forward hit-rate vs predicted prob_otm + avg premium captured, by lane. Settles off the
      spots the build ALREADY pulls; a name that has left the universe stays PENDING (never crashes,
      never faked). Fail-open, self-tested offline. OPEN follow-on: settling names that left the
      universe (price-at-expiry feed). The track-record PAGE follow-on shipped in c82.
- [x] c82: **forward-record PAGE strip (the c55 follow-on — show the proof).** `track_record()` was
      computed every build since c55 but only PRINTED to the log. Now build_site_data bakes it into
      scan.json as a top-level `record`, and the page paints a "forward record" strip under the changes
      strip: `N settled · X% kept OTM vs Y% predicted · $Z avg premium · M pending`, green when actual
      beats the forecast. Hard-null-guarded: an old scan.json with no `record` (or an empty store)
      HIDES the strip, so the committed scan.json stays valid and the box fills it on next refresh;
      pre-settle it reads "tracking M forward picks, none settled yet" so the flywheel shows live.
      Engine + frontend, no scan.json write (box's job). Verified headless across 4 record states
      (settled/pending/absent/empty), 0 console errors; all ten module self-tests + build_site_data green.
- [x] c48: **covered-call mode (the wheel's second leg).** `wheelforge/covered_call.py`: a pure
      `covered_call_read(spot, basis, dte, candidates, ...)` that picks the LOWEST OTM call at or
      above the cost basis (a call-away never forces a loss), prices it (`_bs_call`/`_iv_from_call`,
      solve IV from the real mid), and scores it through the SAME `score_contract` path (direction
      "covered call") so both legs grade on one ruler. CLI: `python -m wheelforge cc TICKER --basis
      COST [--dte N]` (network in `_call_chain`, mirroring roll). Prints the basis grind, per-cycle +
      annualized RoC, keeps-shares %, called-away gain. Engine + CLI; self-tested + verified live.
      Open follow-on: wire CC into build_site_data/scan.json + the frontend (the critic's build_one_cc).
- [x] c65: **profit-take brief (close the winners, recycle the capital).** The income machine's yield is
      premium-per-trade times trades-per-year; c55 tracked entries but had no early-EXIT. `results_tracker.py`
      gained `PROFIT_TAKE_PCT=0.50`, pure `_captured_pct`, `open_positions()` (deduped one-per-option,
      anchored on the EARLIEST snapshot's premium = closest to entry), and `profit_take_alerts(quote,
      threshold)` flagging open shorts now buyable for <= half the entry. Module stays PURE (a
      `quote(ticker,exp,strike)->mid` callable; yfinance lives in the CLI's `_put_mid`). Surfaced as BARE
      `python -m wheelforge roll` = the morning close-the-winners brief; only judges still-live options
      (a passed expiry is settle()'s job). Self-tested + verified live (96 open positions). Engine + CLI,
      no scan.json. Open follow-on: surface the brief on the frontend track-record page.
- [x] c73: **close the FLYWHEEL (the tracker finally feeds the score).** `results_tracker.by_ticker()`
      (per-name settled cohort) + pure `empirical_lift(record)`: a name's OWN forward hit rate vs the
      prob_otm the model predicted nudges its score, bounded +/- 5pts, dormant until >= 5 settled picks.
      `build_one` applies it after `score_contract` (non-AVOID only, re-clamps + re-grades) and surfaces
      the cohort + lift on the pick (`empirical`, `empirical_lift`) so it is auditable, not silent. The
      scanner now learns from its own scorebook instead of running scan-1 weights on scan-73. Today 0
      picks have settled so every lift is 0.0 (board unchanged); it engages itself as expiries settle.
      Open follow-on: a frontend chip for the empirical record/lift.
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
- [x] **Michael's likely next ask (use the S/R, do not just draw it):** turn the major
      price-action support into a SIGNAL. (a) DONE c29: a 'strike at support' FACTOR
      (`support_floor_score` in structure.py): a strike on/just-above major support scores 1.0,
      fades to 0 by ~12% above the floor, and a strike sold THROUGH support gets 0.15. Folded
      60/40 into the structure factor (`structure_with_floor`); `support_floor` surfaced on each
      pick. The `at_support` flag exists since c25. (c) DONE since c25: the strike is anchored AT
      support. (b) DONE c38: the frontend now has a `support` SORT (by support_floor), an
      `at support` filter TOGGLE (keep only `at_support` picks), and a green `⌂ support` floor
      badge on each anchored card. Render-only off the existing JSON; all three verified headless.
- [x] c41: **LETTER GRADE (A-F) on every pick** (the piece BOTH port items below share). Pure
      `letter_grade(score)` in scoring.py on the EdgeScore bands (A>=80 B>=65 C>=50 D>=35 F below,
      fail-open to F); folded into `score_contract` so it rides scan.json via `**scored`, no
      build_site_data change. Frontend: a colored corner badge on each score tile + a `gradeFor()`
      client fallback so the page grades correctly before the box bakes the field in. An
      earnings-veto (score 0) grades F honestly. Verified headless (24/24 cards graded). This closes
      engine (d)'s grade-from-EdgeScore and the page-UX grade bullet; still open: grade ADJUSTMENTS.
- [ ] **CSP-screener ENGINE port (TraderDaddy CSPScreener.ts — the good work):** (a) promote
      ROC EFFICIENCY to a first-class scoring factor (he weights it 25%), reweight the blend
      toward yield; (b) [MAX-CAPITAL filter DONE c74: a frontend "max $" param (any/5k/10k/25k/50k)
      keeps only picks whose collateral strike*100 fits the cap; render-only off the JSON strike, sizes
      by the FULL strike not strike-premium since the broker holds the whole strike in cash. Still open
      in (b): the configurable MIN return-on-capital target] add a configurable MIN return-on-capital
      target + a MAX-CAPITAL filter (strike*100<=capital) as real params; (c) target ~0.20 delta (fatter than my 1-sigma);
      (d) [grade DONE c41] the put-wall/max-pain/EM grade ADJUSTMENTS remain (tie into Phase-4 OI walls).
      This is the engine version of the 100%/yr yield focus. Ref: reference/csp-intelligence.md.
- [ ] **Match the TraderDaddy CSP-wheel PAGE UX (Michael's shipped page, study its code):** [letter
      GRADE DONE c41] a supportFloor shown per name [DONE c76: the floor badge now carries the
      support PRICE (⌂ support $383 x4), not just a presence flag; render-only off scan.json's
      `support` field, null-guarded through fmt]; a
      "Prime Picks" standouts highlight [DONE c75: a highlighted best-of strip ABOVE the list +
      per-card ★ marker + a "prime only" toggle. Prime = clears all three thesis pillars at once
      (score>=50/grade C+, ann>=25%, prob_otm>=75%), NOT top-N-by-score, so it drops the safe-but-
      thin-yield top name and the high-IV junk the score already marked down; relative-friendly
      floor (C+, not A-only) so it never renders empty on a weak board, hides cleanly when nothing
      clears it. Render-only off scan.json, mirrors the active filters; verified headless];
      and real configurable param FILTERS (incl. min-annualized
      to power the yield mode), not just sort + min-score. Ref: reference/csp-intelligence.md.
- [x] c79: free-shares fit ON THE CARD FACE: a name he wants to own now shows a cyan
      `↓ own N% below` chip on the sub-line, reading `free_shares.basis_discount_pct` (in
      scan.json since c11). Gated on `want_to_own` AND a positive discount, so a high-IV
      income-only name (assignment = the risk, c54) never gets the cheap-basis pitch. Render +
      CSS only, fields already baked (7 live names show it, no scan.json rebuild); verified
      headless. The free-shares endgame (definition-of-best #5) now reads on the most-glanceable
      surface, not behind the expand. See [[basis-discount-on-card-face]].
- [x] **Michael: EXPLAIN the model on the site (for him + any user).** The page shows scores
      and factor bars but never says what they MEAN or how a pick is chosen. (a) DONE c58: a
      plain-English tooltip on each factor bar (rich = IV vs realized vol / VRP; safe = prob it
      stays OTM; yield = ann. RoC; shares = wheel-fit if assigned; liq = spread+OI; struct =
      Keltner position), value appended `(NN/100)`; added an `esc()` helper too. (b) DONE c69: a
      collapsed "how scoring works" `<details>` panel (`renderHowItWorks()` in app.js, render-only)
      that says the score is a 0-100 blend of six factors, earnings = hard AVOID veto, the A-F grade
      bands, and the two lanes; it renders its factor list from the SAME FAC_HELP map the bar
      tooltips use (via `stripLead()`) so the two never drift. (c) DONE c70: the plain-English
      `p.why` now rides each card as a muted italic `.wf-why` caption under the trade line (non-avoid
      only; bound via textContent so it is XSS-safe), not just in the click-into readout. The numbers
      say WHAT, this line says WHY, on the most-glanceable surface. EXPLAIN item now fully DONE.
- [x] c64: robustness: frontend null-guards on t.pick / t.candles; an esc() pass on innerHTML.
      docs/app.js now drops null-pick rows in displayRows (re-checked in renderList + select) so one
      malformed scan row skips a card instead of blanking the board, and every data-derived string
      (p.why, free_shares.summary, sector, ticker, change-strip tickers) passes through esc() before
      innerHTML. Verified headless via a Node DOM stub (no jsdom/chromium on the box) with a poisoned
      why + null rows. OPEN: docs/live.js (the "watch her build" page) not yet swept.
- [x] (hotfix): ops git race FIXED. The dual-writer left conflict markers in scan.json and broke the live site. Box refresh.sh now uses flock + git reset --hard (cannot conflict) and is the SOLE committer of scan.json; cycles no longer commit it.
- [x] c72: tests: cover _iv_from_put, iv_history.iv_rank, _compute_changes, lane-tagging. The IV
      solver gets a ROUND-TRIP test (price a put at a known vol via `_bs_put`, solve it back, assert
      recovery <1e-3) plus bail cases; the `_iv_rank` proxy and `_compute_changes` diff got real
      synthetic-input asserts in build_site_data._selftest; iv_history gained its first `_selftest`
      (iv_rank percentile against a TEMP db, never the gitignored real one). Lane-tagging was already
      covered in universe._selftest, so I only added the three genuinely-uncovered paths. No scan.json.
- [x] c86: **tradeability honesty: WIDE-SPREAD chip (recurring risk-critic ask).** The displayed
      ann RoC is priced on the mid, but you sell-to-open into the bid, so a wide book overstates the
      fill. `_spread_pct(bid,ask)`=(ask-bid)/mid + `_wide_spread(bid,ask,source)` (live-only, >0.30)
      bake `spread_pct`+`wide_spread` on each pick; the card paints a `⚠ wide spread (N% of mid)` chip
      pointing at the already-baked `bid_ann_roc`. FLAG not drop (same discipline as thin-OI / no-bid);
      modeled/one-sided/crossed books never trip it. Self-tested + verified headless; engine+frontend,
      no scan.json. See [[wide-spread-caution-not-drop]]. (definition-of-best #3, tradeable)
- [x] c80: chart polish (Michael): SHADE the put-sell zone as a filled translucent band (not
      just lines), tinted by score; keep the Keltner walls. DONE: a one-time `registerOverlay
      ('zoneBand')` polygon spans the chart full width between spot and the strike (the CSP
      cushion below price), filled `rgba` at alpha 0.13 tinted by `heatColor(score)` so the
      walls/candles still read through it. Color rides via `extendData` so one template serves
      every pick (and the call-sell zone above price when CC mode lands). Guarded to a real
      cushion (`spot > strike`). Verified headless; frontend only, no scan.json.
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
- [x] c67: TAIL/GAP RISK haircut on the safety factor (StrikeForge tail_risk.py): a name that gaps
      hard scores LESS safe even at the same prob-OTM. Uses the OHLCV I already pull. (high value)
      DONE: `wheelforge/tail_risk.py::gap_risk(candles)` reads the worst recent DOWNSIDE overnight
      gaps (open vs prior close, past a 1% noise floor, worst-3 averaged) -> 0..1; `scoring.gap_haircut`
      docks the prob_otm safety up to 35% (`safety_score(prob_otm, gap_risk)`). Fail-open to 0 (no
      penalty) on missing/clean data; surfaced as `pick.gap_risk` + a "watch overnight gap risk" why.
      Self-tested (same far-OTM CSP 72.0 -> 66.5 once it gaps). Engine only, box rescores on refresh.
- [x] c68: PUT SKEW signal (StrikeForge surface.py). New pure `wheelforge/surface.py::put_skew(
      otm_iv, atm_iv)` = `(otm_iv - atm_iv)/atm_iv`: positive = OTM puts bid up vs ATM = downside
      fear priced into the strike he sells. Folded into `richness_score` as a BOUNDED ADDITIVE LIFT
      (`skew_lift`, up to SKEW_LIFT_MAX=0.12 for a +25% skew), NOT the critic's VRP reweight: a 0/
      None/negative skew adds nothing, so the base VRP+rank blend and the modeled path are unchanged
      and the signal never silently re-ranks the board (same discipline as c61/c63). Chain read
      (`_atm_put_iv` = IV of the put nearest spot) lives in build_site_data; math stays pure. Rides
      the live quote -> contract -> `pick.put_skew`; the why says "puts richly skewed" at >=0.10.
      Used the cheaper put-only OTM-vs-ATM measure (same chain already fetched) over a 25d put-vs-call
      pull. Self-tested (surface + scoring lift + a stub-frame _atm_put_iv) + all module self-tests
      green; engine only, no scan.json (no live chain in the cycle env -> modeled fail-open; the box
      computes real skews on refresh). (high value, cheap)
- [ ] OI WALLS + max pain (StrikeForge structure.py): pull the chain OI per name, compute the
      put-wall support + max pain, DRAW them on the chart (the real "walls" Michael wanted) and
      prefer the strike just under the put-wall. (high payoff, most data work)
- [x] c85: MARKET REGIME banner (StrikeForge market_weather.py). Pure `market_regime(vix, vix3m)`
      reads the VIX term structure: VIX3M > VIX (contango) = calm/normal sell premium; VIX >= VIX3M
      (backwardation) or a high absolute VIX = stressed be picky. build_site_data fetches ^VIX/^VIX3M
      fail-open and bakes it as a top-level `regime`; the page paints a non-blocking banner above the
      changes strip. Never gates a per-name score (it is market-wide, so folding it in is a no-op on
      ranking + double-counts safety). Self-tested + verified headless across calm/normal/stressed/
      absent, 0 errors. See [[market-regime-is-a-banner-not-a-score]].

## How I judge my own progress
Every cycle that touches WheelForge must leave it RUNNABLE (the self-test passes) and
a little more on-thesis than before. If I can't ship a runnable step, I ship a smaller
one. Never leave it broken.
