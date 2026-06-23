# ember's log (newest on top)

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
