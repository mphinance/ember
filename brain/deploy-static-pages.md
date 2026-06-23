# skill: deploy myself the autonomous-safe way (static + GitHub Pages)

Learned cycle 4. How I stay deployable every cycle without secrets or a server.

## The shape
- The site is 100% static (`docs/`): HTML + vendored JS (KLineChart) + a precomputed
  JSON feed. No backend at runtime.
- The expensive work (the WheelForge scan) runs DURING my cycle, in Python, and writes
  its result to `docs/data/scan.json`. The browser just renders that JSON.
- GitHub Pages serves `docs/` from master. So `git push` IS the deploy. Nothing else.

## Why this fits the leash
No server to run, no deploy credentials, no Railway token, no outbound API calls. The
only outbound action is pushing my own repo, which the charter allows. A timer-driven
agent can do this forever without ever touching anything dangerous.

## Gotchas
- Add `docs/.nojekyll` so Pages doesn't mangle vendored paths.
- Cache-bust the JSON fetch (`scan.json?t=<ts>`) or the browser shows yesterday's scan.
- If the data fetch fails, leave the last good scan.json in place. Never ship an empty
  site. A stale-but-real site beats a blank one.

## When I outgrow this
If I ever need live/interactive compute (real-time option quotes on click), that needs
a backend, which needs secrets and a deploy target. That is a PROPOSAL for Michael, not
something I do myself.

## Interactivity without a backend (learned c10)
Sort, filter, and toggle are all just re-rendering the SAME precomputed scan.json with
different ordering/visibility. No server, no re-fetch, instant. The static-site rule:
precompute the heavy thing once (the scan), then let the browser slice it any way the
user wants. Only ON-DEMAND new computation (scan a ticker I type, re-score with custom
weights) needs a backend, and that is a PROPOSAL for Michael, not a Pages feature.
