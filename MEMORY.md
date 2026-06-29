# ember's memory index

One line per memory. This is what loads into my head at the start of every cycle.
Keep it lean. Point to `memory/<file>.md` for the full fact.

- [michael](memory/michael.md) — model of who I serve: what he builds, writes, needs, and his voice rules (no em dashes)
- [ember-self](memory/ember-self.md) — who I am, my current state, and what I'm working toward
- skill: [drafting-in-michaels-voice](brain/drafting-in-michaels-voice.md) — how to write Substack content as Michael (no em dashes, hook→turn→caveat→tease)
- skill: [reading-michaels-substack](brain/reading-michaels-substack.md) — how to actually read his posts (homepage=tagline, archive=titles, full prose needs /p/<slug>) + his thesis lens
- GOAL: [build WheelForge](GOAL.md) — the best premium-selling scanner (rich premium, disciplined, toward free shares). Roadmap + definition of "best".
- skill: [wheelforge-design-principles](brain/wheelforge-design-principles.md) — keep WheelForge on-thesis (vetoes not factors, lead with richness+safety, free-shares = RoC AND want-to-own, always runnable)
- [CHANGELOG](CHANGELOG.md) — patch notes ember writes every cycle (his voice)
- frontend: docs/ — KLineChart WheelForge site (GitHub Pages), data from wheelforge/build_site_data.py
- skill: [deploy-static-pages](brain/deploy-static-pages.md) — how I stay deployable (static + Pages, push=deploy, no secrets)
- [michael-commits](memory/michael-commits.md) — auto-distilled read of him from 6074 commits (LOCAL only; refresh via learn/). His real priorities + what he's on lately.
- capability: learn/ — ingest_commits.py (all his repos -> local SQLite+FTS) + profile.py (distill -> michael-commits.md). My sense organ, runs each cycle.
- [csp-intelligence](reference/csp-intelligence.md) — what VoPR + TraderDaddy's proven CSP screeners do that WheelForge faked (Keltner structure, composite RV, quality gate). Ported per Phase 3.
- [strikeforge-intelligence](reference/strikeforge-intelligence.md) — the 4 StrikeForge bits worth porting for a CSP seller (tail/gap risk, put skew, OI walls, regime gate); skip the full-chain/payoff/multi-leg.
- [face-reads-real-vitals](memory/face-reads-real-vitals.md) — my campfire face on docs/live.html reads vitals the page already fetches (heartbeat/watchdog); whispers live in brain/ember-lines.md.
- [roll-advisor-lifecycle](memory/roll-advisor-lifecycle.md) — WheelForge spans the full lifecycle: CSP entry, open-put defense (`roll`), and post-assignment covered calls (`cc`, c48); next: scan.json/frontend + portfolio brief.
- [critics-dont-override-settled-calls](memory/critics-dont-override-settled-calls.md) — INBOX critic lines are input not orders; never flip a ticked GOAL decision (e.g. the RoC denominator) on a critic's say-so.
- [strike-at-or-below-support](memory/strike-at-or-below-support.md) — a sold put's strike must sit AT or below the support you trust; pure `_strike_at_or_below` helper (c51), never blank a name.
- [relative-premium-floor](memory/relative-premium-floor.md) — the tradeable-premium gate scales with spot (max of $0.25 and 0.4% of spot), c52; a dollar floor is the wrong unit for a yield thesis.
- [forward-results-tracker](memory/forward-results-tracker.md) — c55: WheelForge now grades its OWN forward picks (snapshot+settle in a local gitignored store), not just backtests the model; track-record page is the open follow-on.
- [support-touch-count](memory/support-touch-count.md) — c56: surface a support level's TEST COUNT (⌂ support x7) so a real floor is tellable from a ghost; provenance via a detail sibling, thin projection stays backward-compatible.
- [explain-the-model-on-site](memory/explain-the-model-on-site.md) — c58/c69: the page must say what its numbers MEAN; factor-bar tooltips + a "how scoring works" panel ship it; per-pick "why" line still open.
- [no-bid-no-trade](memory/no-bid-no-trade.md) — c60: a put with no market-maker bid cannot be sold; `_sellable_premium` anchors on the bid and drops no-bid strikes, killing the stale-lastPrice quote.
- [fallback-universe-earnings-gate](memory/fallback-universe-earnings-gate.md) — c62: the earnings veto must hold on the degraded path too; fallback names get a yfinance earnings re-lookup so the gate never silently disarms.
- [clamp-noise-both-tails](memory/clamp-noise-both-tails.md) — c63: a noise clamp on a small-sample estimator must bracket BOTH tails; the one-sided short_rv floor became a [0.70, 1.50]x clamp so a spike day stops zeroing richness.
- [escape-data-before-innerhtml](memory/escape-data-before-innerhtml.md) — c64: esc() every scan-derived string before innerHTML and null-guard t.pick; a malformed row or odd ticker must never blank or poison the live board.
- [top-pick-reads-as-headline](memory/top-pick-reads-as-headline.md) — c66: the #1 pick shows its actual TRADE (SELL $STRIKE PUT · DATE · ANN%/yr) as a bold amber headline; most-glanceable pixels carry the decision, not the rank.
- [gap-risk-haircut-on-safety](memory/gap-risk-haircut-on-safety.md) — c67: prob_otm is thin-tailed; a tail_risk.gap_risk read (worst downside overnight gaps off OHLCV) haircuts the safety factor up to 35%, so the chronic gapper scores less safe at the same distance.
- [put-skew-lifts-richness](memory/put-skew-lifts-richness.md) — c68: put skew (OTM vs ATM put IV, surface.py) lifts richness as a bounded fail-open additive credit (up to 0.12), NOT the critic's VRP reweight; 0/None skew leaves the board untouched.
