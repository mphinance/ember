# THE LOOP — how to copy this self-building agent to any project

This repo is a worked example of an AI agent that wakes up, builds one thing, commits,
deploys, and reschedules itself, indefinitely, while staying on a safety leash. Here is the
whole machine in one page so you can clone the pattern into a new project.

## The idea in one breath
An agent runs a fixed CYCLE on a timer. Each firing: sync, read its inbox, do ONE small
shippable step, write down what it learned, commit, push (the push deploys), reschedule.
Small steps + always-runnable + commit-every-cycle means it never wanders far and you can
stop it at any green commit. A LEASH means it can run unattended without doing anything
dangerous. MEMORY means each cycle starts smarter than the last. That is all it is.

## The two clocks (this is the key architecture)
- **Feature clock (the brains):** an LLM agent runs the cycle prompt (`prompts/cycle-prompt.md`)
  on a self-rescheduling timer, building ONE feature per cycle. In this build it fires when
  the chat session is idle; the 24/7 version is a headless `claude -p "<cycle prompt>"` on a
  cron (needs the CLI authed on the box).
- **Data clock (the muscle):** a dumb shell script (`ops/refresh.sh`) on a Linux box, cron
  every 30 min, re-runs the scan and pushes fresh data. NO LLM. The push deploys.
Two clocks, two writers, DIFFERENT files (data script owns `docs/data/scan.json`; the agent
owns everything else). That separation is what makes them never collide.

## The five files (copy these, swap the contents)
1. `CHARTER.md` — WHO the agent is + the HARD SAFETY LEASH. Most important file. (Owns one
   repo, no trading/money/posting to the world, stop on a `STOP` file.)
2. `cycle.md` — the exact step-by-step runbook for ONE cycle.
3. `GOAL.md` — one standing goal, broken into one-cycle steps it ticks off (its roadmap).
4. `MEMORY.md` + `memory/` — what it knows, reloaded every cycle so it starts smart.
   `brain/` holds skills/lessons it writes for itself.
5. `INBOX.md` — where you drop steering; it reads this first every cycle, obeys, clears it.

Plus: `prompts/cycle-prompt.md` (the verbatim timer prompt) and `ops/refresh.sh` (the box
cron). The `learn/` dir (ingest the owner's commits into a local DB) is optional flavor.

## Replicate it to a NEW project (checklist)
1. Copy `CHARTER.md`, `cycle.md`, `GOAL.md`, `MEMORY.md`, `INBOX.md`, `prompts/`, `ops/`.
   Rewrite CHARTER + GOAL for the new project. Keep the leash strict.
2. Build a tiny first thing + a deploy target. Static + GitHub Pages is the no-secrets path
   (a push IS the deploy). See `brain/deploy-static-pages.md`.
3. Kick the feature clock: run the cycle prompt on a timer (idle-fired, or headless cron).
   Each firing builds one step, commits, pushes, reschedules.
4. (Optional) stand up the data clock: clone the repo on a box, `ops/refresh.sh` + a cron.

## Hard-won rules (do not skip)
- **One writer per file.** Two things committing the same generated file WILL leave git
  conflict markers and break your deploy. Split by file; sync with `git reset --hard`, never
  stash/rebase the generated file.
- **Always runnable.** Every cycle keeps the tests green and the build producing valid,
  non-empty output. If you can't ship a runnable step, ship a smaller one.
- **Fail open.** A missing endpoint / data point = a missing layer, never a crash.
- **Never blank the deploy.** If the build comes back empty, keep the last good output.
- **Call a proxy a proxy.** If a number is an approximation, the UI must say so.
- **Code review predicts your outages.** The dual-writer race that took this site down was
  flagged as a blocker in review before it ever happened. Do the review.

## Where the running pieces live
- Agent (this repo) deploys to GitHub Pages from `docs/`.
- The box runs `ops/refresh.sh` on a `*/30` cron (see the header of that file to install).
- Watch it: the live build log renders `LOG.md` + commit timestamps + a box-heartbeat banner.
