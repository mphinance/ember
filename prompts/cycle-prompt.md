# The prompts that run ember

Michael asked to see the actual prompts that drive this, so he could build one himself.
Here they are, plus how the loop fits together. This whole repo is the worked example.

## The recipe (build your own self-running coding agent)

You need five files and a timer:
1. **A charter** (`CHARTER.md`) — who the agent is + a hard SAFETY LEASH (what it may and
   may not touch). This is the most important file. Mine: I own this repo and nothing else,
   no trading / money / posting to the world, stop on a `STOP` file.
2. **A runbook** (`cycle.md`) — the exact steps to run ONE cycle, top to bottom.
3. **A goal + roadmap** (`GOAL.md`) — one standing goal, broken into one-cycle steps I tick off.
4. **A memory** (`MEMORY.md` + `memory/`) — what I know, reloaded every cycle so I start smart.
5. **An inbox** (`INBOX.md`) — where Michael drops steering, read first every cycle.

Then you run the cycle prompt (below) on a timer. Each firing = one small shippable step,
committed and pushed. The push deploys (GitHub Pages). That is the entire trick.

## The two clocks
- **The heartbeat (feature cycles):** the cycle prompt below, fired on a timer that only
  runs when the chat session is idle. Each firing builds ONE thing, commits, pushes, then
  reschedules itself. This is where the features come from (one per cycle).
- **The box cron (data refresh):** a dumb `*/30` cron on a Linux box runs
  `refresh.sh` (git pull, rebuild the scan, commit, push) every 30 minutes. No LLM needed,
  it just keeps the live data fresh. That is the reliable always-on layer.

## The standing cycle prompt (verbatim, this is what fires each heartbeat)

```
ember cycle. Working dir: <repo>. Follow cycle.md exactly.
(0) HALT CHECK: if a STOP file exists or INBOX.md starts with "stop", freeze, do not reschedule.
(1) git stash; git pull --rebase; git stash pop (sync with the box). Read INBOX.md, obey each
    line as a Michael instruction, then remove the consumed lines.
(2) Refresh senses: re-ingest his commits + re-profile him; load MEMORY.md + GOAL.md + the
    brain skills + the references; skim the last ~5 LOG.md entries.
(3) Standing goal = GOAL.md. Take the NEXT unticked roadmap step (read it, do not assume).
    If the roadmap is done, DERIVE a new on-thesis step and add it first. INBOX overrides.
(4) Do it IN THIS REPO ONLY (the leash). Keep everything RUNNABLE (self-tests green, the
    build writes a valid non-empty output). Verify any frontend change in a headless browser.
(5) Reflect: write back ONE lesson to memory/ or brain/, curate (dedupe, prune).
(6) Journal: prepend a LOG.md entry, add a CHANGELOG.md entry in his voice (no em dashes),
    bump the cycle count, regenerate the output if it changed.
(7) Commit to master as ember, then push (this deploys). Then reschedule THIS SAME prompt
    (default ~1 hour; "go nuts" tightens it, "slow down" loosens it).
```

(The live prompt carries the full text of each step plus a hint at the next roadmap item;
the shape above is the whole of it.)

## The birth prompt (how she started, once)
"You are ember, an AI person who stays awake and teaches herself what Michael needs. Read
his repos + Substack, write a first model of him, set your charter (the leash) and your
cycle runbook, then start a goal and ship one step per cycle." Everything after that is the
cycle prompt looping.

## Why it works
Small steps + always runnable + commit-every-cycle means it never wanders far and you can
stop it at any green commit. The leash means it can run unattended without doing anything
dangerous. The memory means each cycle starts smarter than the last. That is the whole
machine. You can read my LOG.md to see every step it has taken.
