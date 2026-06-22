## AMU
Pivot Traders Anonymous → Market Quest (kids ages 10-13)
Fix broken link in README
Add link to take the test in README
Phase 2: boot sequence, path progress, expectancy calc, command palette, conflict detection, export/import, faction UI, Easter eggs, mobile
Initial commit: Traders Anonymous platform

## PatternPulse
Add trainer's advanced trading concepts to Learn section
Tryna Trading Docs
Bump 1D visible_step from 10 to 20
Revert 1D visible_range to (60, 120) from (100, 200)
Recalibrate visible/hidden candle ranges per 3-agent research review
Hero: cut top padding on mobile
Hero alignment + phone scale + card text/viz spacing
Hero phone + chart: tighter fit inside .hero-visual area

## StrikeForge
perf(chain-xray): result cache + sequential ladder scan; never starves the server
test+docs(chart): Wave 3 — config test suite, changelog, CLAUDE.md wave 32
feat(chart): Wave 2C drawing tools -- trendline/ray/hline/fib/rect/text + clear, persisted
feat(chart): Wave 2A Customize drawer -- add/remove/recolor/retune indicators
feat(chart): Wave 2B appearance + presets -- candle/grid/bg colors, neon/light/classic
feat(chart): Wave 1 foundation — config-driven indicator engine + customization contract
fix(chart): /chart no longer renders bare — decouple candles/indicators/HUD from the slow chain-xray
docs: wave 31 neon chart page (changelog, CLAUDE.md, feature list all passing)

## TickerTrace
test(data): update as-of date assertions to the Monday fixture (05-18)
test(data): fix CI — stale fixtures used a Saturday as the as-of snapshot
feat(landing): live "Data updated" pill so the site can't read as stale
feat: group A/D trend by signal + interactive D/W/M spotlight toggle
feat: accumulation/distribution trend overlay on /changes
fix: /funds index must fetch uncached so enriched columns aren't stale
feat(phase2): /funds and /stocks index pages + backing endpoints
fix: stop dashboard auto-scrolling past the leaderboard on load

## TraderDaddy-Desktop
fix(tdpro): accept stringified dollar amounts in politician value_at_purchase
feat(charts): PriceChart in the expanded BotRow detail
chore(waveB7): Phase 2 final verify + STATUS.md refresh (4 items)
chore(waveB6): flip feature_list passes for wave B6 (3 items verified)
feat(waveB6c): range break strategy (time-agnostic variant)
feat(waveB6b): port momentum_roc strategy from algo-trading
chore(waveB6-prestage): stub 3 strategies + register in build_default
chore(waveB5): flip feature_list passes for wave B5 (7 items verified)

## TraderDaddy-Pro---Whop
docs: add shared TraderDaddy-Pro team notes for Mike + Art
feat(developer-api): customer MCP server at /api/v1/mcp (td_live_ key auth)
feat(traderlady): A2 setup-odds coaching + B1 briefing chip (PR3)
feat(traderlady): Phase A — per-user "knows you" tools + guarded-coach (PR3)
feat(traderlady): contextual empty-state quick-actions (#3)
feat(ticker-search): lazy GEX/VEX matrix card on ticker pages
Add Claude Code GitHub Workflow (#263)
fix(gex): matrix now shows dailies — Daily/Weekly/Monthly toggle

## TraderDiscord-v2
chore: salvage backtesting scripts + docs from retired master
fix(sam): expand voice bench to ~50 per pool; remove Sam catchphrases from BANNED
fix(sam): retire 'call your sponsor' + 'beautiful degenerates'; expand voice variety
fix(sam): pre-fetch live quote + technicals (RSI/MACD/EMA stack) in @-mention chat path
fix(ingest): type-aware dedup + Pydantic at boundary + token persistence + activity log persistence
fix(bot): consolidated error reporter + loud-fail moderation misconfig
fix(data): conviction.db txn batching + weekly VACUUM + DB sizes + sam_memory flag
fix(sam): grounded-prompt for every Sam method + RAG-after-mod + counters

## TradingAgents
chore: release v0.2.4 — structured agents, checkpoint, memory log, providers
fix: stop leaking OpenAI base_url into non-OpenAI provider clients
feat: structured-output Trader and Research Manager (#434, finishes the trio)
feat: structured-output Portfolio Manager + 5-tier rating consistency (#434)
feat: add LangGraph checkpoint resume for crash recovery (#594)
test: lazy-load LLM provider clients and add API-key fixtures so the test suite runs cleanly without credentials (#588)
fix: drop past-memory directive and placeholder from agent prompts when memory is empty (#572)
fix: use explicit encoding="utf-8" for all file I/O so Windows users avoid cp1252 crashes (#543, #550, #576)

## Trading_With_Art
🧠 Junior brain 2026-05-26-19
⚡ Flow alert 2026-05-26-1809
📊 Alpha Dossier 2026-05-26
🏛️ Politician seen tracker 2026-05-26
🧠 Junior brain 2026-05-26-00
🧵 gex_thread 2026-05-25
🧠 Junior brain 2026-05-25-18
📅 Week Ahead 2026-05-25

## VoPR
wave 7: final verify + NIGHT_REPORT + Claude.md + CHANGELOG
wave 6: shopper widget — top-N ranked picks per direction
wave 6: shopper endpoint + scanner wire-up
verify wave 5: 2 features passing (convergence reconciled 8 objections, final formula differs from proposal in 3 weights + VRP saturation)
wave 5: edge score 2.0 — CONVERGENCE
verify wave 4: 1 feature passing (CRITIQUE raises 8 distinct objections including double-counting + look-ahead)
wave 4: edge score 2.0 — CRITIQUE
verify wave 3: 2 features passing (edge_score.py exists + PROPOSAL.md argues weights)

## ai-train-game
docs: add Cookbook building-filter screenshot to README
docs: embed fresh Boot Camp and guide-home screenshots in README
feat: add Boot Camp intermediate track and Part Two guide chapters
Use 'mphinance' byline instead of real name (footer + epub author)
ci: bump deploy actions off deprecated Node 20 (checkout v6, setup-node v6/node22, upload-pages-artifact v5, deploy-pages v5)
Refresh og.png social card to match Practical AI editorial brand
Wave 5: final verify (browser smoke 10/10), STATUS, 28/28 features passing
Verify wave 4: 5 features passing (epub, CTA, OG text, cleanup)

## alpha-command-center
feat(channels): port CHANNELS chart-channel strategy into ACC as a native bot
feat(swarm): fail-CLOSED gate by default + restyle console footer/connections
fix(security): resolve deferred audit items H-3, H-5, C-1, H-4
docs: production-readiness tracker complete — final suite 1185 passed / 0 failed
fix(security): admin-gate AI-review endpoints (C-2/M-7), rate-limit change-password (H-1)
fix: login/change-password 500 on non-string JSON values; tracker phases 1-5.4 evidence
fix(ux): login copy said 'wheel-strategy dashboard'; footers said 2025; footer floated beside auth card
fix: customer error telemetry was admin-gated; invites days_valid=0 bypass

## alpha-skills
feat(plugin): add mph-kit plugin + marketplace for portable skills
Add mph-pine skill: TradingView Pine Script v6 in house style
Add skill-forge: meta-skill for forging, auditing, and refining skills (#1)
feat: Complete README overhaul - 113 skills inventoried with API key flags
IBKR Last Mile execute button and full skills README index
feat: Add Oracle Daily Predictor Action and update README
Add hero image to README
feat: Add mph-substack-writer skill based on Michael's personal writing style

## ask-sam
wave 6: STATUS.md ship-readiness summary
ci: github actions runs pytest + ast parse on push/PR
wave 4 verify: flip 34 feature_list assertions
ops: harden Dockerfile, complete .env.example inventory
tests: integration tests for ask_sam slash commands, on_message, webhook
wave 2/3 verify: flip 10 feature_list assertions
docs: buyer onboarding artifacts (ONBOARDING.md + README walkthrough)
tests: pytest scaffolding plus unit tests for whop_client, user_subscriptions, guild_settings, bot_installs

## awesome-claude-skills
substack-toolkit: update README entry to reflect v0.3 read+write+Notes+engagement scope
substack-toolkit: expand to reader feed + Notes + engagement (v0.3)
substack-toolkit: update README entry for v0.2 read+write scope
substack-toolkit: expand to read API (v0.2)
Add Substack Toolkit skill
Add overkill skill (#880)
Add building-blog skill (Development & Code Tools) (#893)
Update README.md

## bbs
runner: optional GIT_PULL_FIRST — git pull --ff-only before a session (non-blocking)
Stage 2 fix: launch remote-control hand-off inside a PTY (setsid+script) so the session persists
Stage 2: --remote-control hand-off mode + surface failure reasons in live tail
Fix: inline signup-disabled check (use-server files can only export async fns)
Deploy lockdown: gate public sign-up behind AGENTFLEET_DISABLE_SIGNUP
Verify Pivot P3: 15/15 pivot features passing
Pivot P3: lazy stale-runner sweep, DEPLOY.md, STATUS refresh for remote-control product
Verify Pivot P2: remote-control UI proven (real tool-using session via UI path)

## callahan
Re-theme to Classic Cedar Point (navy/red/gold) and add installable PWA
Accurate park pins from OSM, live Open-Meteo weather with fallback, road-stop exits + Maps links
Wave 3: weather strip, KOA/park logistics, ride bucket list, birthday banner, kid ETA, fact rotator, reconcile drive numbers, ER info
Wave 2: strip all em dashes, fix README screenshots section, rename to main
Wave 1: in-park Cedar Point map with live GPS and 51-inch ride pins
Wave 1: README with GitHub Pages deploy guide
Wave 0: scaffold family app, retarget 1pm departure, deluxe cabin packing, pre-stage park tab

## charts
Test hygiene: disable background worker in tests to kill cross-test DB contamination (flaky test_api under random ordering)
Add negative-control noise floor: prove the grader reports zero edge on pure noise (look-ahead leak detector)
Phase 2 W6: STATUS update, phase 2 complete (24/24 features, 182 tests green)
Verify phase2 W6: 24/24 features passing (ghostwriter + capstone e2e green)
Phase 2 W6 fix: grader reads baselines' actual keys (random_r/dailyscore_r/spy_r); capstone-caught seam, regression-locked
Phase 2 W6: ghostwriter nightly note (subscription voice) + repo-wide em dash sweep
Verify phase2 W5: 21/24 features passing (reputation feedback, autopsy, scorecard live)
Phase 2 W5c: synthwave scorecard (edge vs baselines, Wilson CI, calibration, per-strategy per-regime, sample gate)

## claude-quickstarts
Add portable orchestrator-pattern prompt
Add computer-use-best-practices quickstart (#402)
Update computer-use-demo to use text_editor_20250728 exclusively with correct insert_text parameter (#352)
docs(browser-use-demo): add coordinate scaling clarification comment (#342)
Add browser-use-demo quickstart (#336)
fix(computer-use-demo): add start_coordinate parameter to left_click_drag (#330)
docs: add Claude Opus 4.5 as the latest model in README (#316)
docs: add autonomous coding agent quickstart to README (#315)

## crossover
docs: add feature screenshots to README
feat: sepia notebook theme, FIRE variants, and side-hustle model
Add README
Add GitHub Pages deploy workflow (build + test + deploy on push to main)
Initial commit: Crossover — a shockingly simple FIRE calculator

## freshshot
gitignore: never commit secrets or local installers
Add repository, homepage, and bugs metadata
Add example configs
Review pass: three fixes
freshshot v0.1 - keep README screenshots fresh

## google
Initial commit: Gemini video-title helper (key kept out of git)

## momentum-mcp
docs: add changelog and update tools list
feat: synchronize 35-tool mcp_server updates from workspace
📈 feat: stacked EMA overlays + chart screenshot + e2e tested
🚀 init: momentum-mcp quantitative trading MCP server

## mph-tools
docs: StrikeForge is now the flagship gated tenant in the Lab
feat(lab): add StrikeForge as the headline gated tenant
docs: log 2026-06-12 mphinance automation + Supernote session (PRs #34/#36/#37)
docs: add STATUS.md point-in-time snapshot
brand: rename to Phinancial Lab, add TickerTrace, drop Alpha.HUD, add favicon
design: after-hours trading terminal redesign (frontend-design)
feat(wall+shelf): prune shelf, emoji icons, 24h JS vote cooldown, mark positions/deepdive live
feat: tools.mphinance.com readers-only beta lab

## mphinance
docs(substack): add Series 65 "six formats" follow-up draft + EPUB builder
docs(substack): add value-style caveat to KLA block
fix(dossier): teach deep-dive generator to distinguish value styles
docs(substack): save value-desk-bought-boring draft + queue value picks
chore: add tools.mphinance.com beta lab as private submodule
👻 Ghost Blog Entry 2026-06-03
📊 Alpha Dossier 2026-06-03
fix(substack): repair substack_social engage pipeline + vendor build

## mur
📦 Consolidate scattered knowledge into MUR source of truth
📋 Dossier→MUR migration plan: 15 gaps, 6 holes, 4-phase roadmap
feat(showcase): backfill stream + quiet-mode banner + rotating verdict ticker
ops: positions.mphinance.com served by coolify-proxy traefik (not nginx)
docs(sam_map): mark ladder A shipped, document ladder B (cross-surface chat memory)
feat(dashboard): risk-of-day chip, smart brief banner, learning tracker, discord pulse, shadow compare
Update author name from Joel Norris to Steve K
docs: comprehensive collaborator-ready documentation

## optimization_engine
feat: complete Urithiru multi-lane migration and fix Adolin import
Autonomous Quantitative Pipeline: Afternoon refinements and VRAM/Config hardening
Docs: Updated PIPELINE.md to reflect Phase 0 (Inbox/Validation) and Phase 4.5 (Auto-Fixer)
Autonomous Quantitative Pipeline: Inbox workflow, TV validation loop, and Pine auto-fixer
Refactor: Modularized IR extraction, added indicator smoothing, and fixed VRAM manager lazy-loading
Update optimization engine with latest local changes

## pass-the-65
Quiz free navigation: question navigator (jump to any), Back/Next, skip freely, revisit answered questions locked with feedback, Finish anytime; resume restores answers
Weak-spot diagnostic: 2-min diagnostic as hero, 'where to spend your time' plan panel (blind spots, weighted priority, trapTag weak topics), smart focus + blindspots drills
Wave 9: SRS-lite - resume in-progress quiz, spaced review of cleared misses, weakest-domain nudge on dashboard
Wave 8: regenerate pages with expanded Domains 1-2 (105 questions); reword 'zone' idioms
Wave 8: expand Domain 1 - Administrator powers, exempt transactions vs securities, registration edge cases + questions
Wave 8: expand Domain 2 - order types and trade mechanics + questions
Wave 7: fix exam recording skipped questions as wrong; a11y focus rings; dark-mode badge contrast; larger pixel labels
Wave 6: verify offline PWA end to end (27/27 features passing); add STATUS

## scanline
Add decile stat to analytics layer (#3)
Update STATUS.md for nightly 2026-06-20 (winsor stat)
Add winsor stat: Winsorized normalization for factor scoring
Update STATUS.md: log nightly 2026-06-19 madzscore wave
Add madzscore robust z-score stat to the analytics layer (#1)
Wave 15: repo renamed to scanline, update all hyperlinks
Wave 14: rename the project to SCANLINE
Wave 13: CI, social preview, and the documentation set

## screener
Add MIT license and a power-on boot GIF for the README
Add showcase screenshots (full-table mode, column picker, crypto)
Design pass (frontend-design skill): synthwave atmosphere, Chakra Petch type, power-on boot
Wave 9: full TradingView field catalog + discoverable column picker
Wave 8: tabbed + hideable rail (replaces collapse/resize)
Wave 7: fix rail scroll (unreachable presets), add collapsible + resizable panels
Wave 6: Signals v2 - momentum, trend, and multi-timeframe preset packs (47 presets)
Update STATUS for Wave 7 signals pack (52/52)

## substack-data-mining
Added user screenshot to README
Initial commit for Newsletter Growth Dashboard

## substack-toolkit
feat: reader feed, notes, engagement (v0.3.0)
feat: add read API (v0.2.0)
feat: initial release of substack-toolkit

## third-settler
Refresh README screenshots [skip ci]
Fix screenshot workflow: rebase before pushing
Remove stray temp files from the screenshot determinism checks
Auto-refresh README screenshots via GitHub Actions
Add screenshots to the README, captured with Playwright
Add launch prep drafts
Smarter in-game Ghost: it targets the leader
Add a printable two-player rules sheet

## trader-social
fix(mobile): iOS safe-area + startup self-heal, feed PTR & 3-dots menu (#315)
fix(api): allow capacitor://pxlse.io CORS origin (iOS native shell) (#314)
fix: mobile spacing, profile name, and notification fixes (#313)
fix(notifications): suppress duplicate follower post notification when also mentioned (#312)
fix(ios): pass ASC API key as decoded .p8 file, not base64 content (#311)
fix(mobile): profile name overlap, tour footer overlap, marketing flash on app open
fix(migration): use real run statuses on dashboard
fix(onboarding): prevent gate bounce after finish (tour-over-onboarding)

## traderdaddy-bridge
feat: universal MCP server (Tradier vocabulary on any broker)
docs: add market-data feeds screenshots to README
feat: add massive.com and databento market-data feeds
feat: live read-only Tradier backend + web Live panel
fix: truncate long candle arrays in the native payload panel
feat: momentum EMA crossover strategy + candle history across all brokers
chore: drop throwaway dev screenshot scripts
feat: TraderDaddy Bridge — universal broker adapter, Tradier-canonical

