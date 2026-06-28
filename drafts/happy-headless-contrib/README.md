# Contribution drafts for slopus/happy — running Happy unattended

These are drafts for Michael to take upstream to https://github.com/slopus/happy.
They are NOT wired into ember; they live in `drafts/` because the leash says ember
only commits to her own repo. Michael files them.

The thesis: Happy is a great remote/mobile client for Claude Code, but its docs
cover the interactive path (pair a phone, watch it work) and say nothing about the
headless path (run it on a cron, no human at the keyboard, no permission prompts).
ember has lived on that headless path for ~56 cycles. This is what she learned,
generalized off the WheelForge specifics, ready to give back.

## What's here

1. `docs-headless.md` — a docs page: "Running Happy unattended (headless / cron / CI)".
   Drop into Happy's docs site, or paste as a discussion/wiki page.
2. `headless-run.sh` — a generic, hardened example wrapper. The de-WheelForged
   distillation of `ops/cycle.sh`. Candidate for an `examples/` dir upstream.
3. `issue-noninteractive-permissions.md` — the one real gap as a filed issue:
   what is the blessed way to run Happy with zero permission prompts on a service
   or root account, given `--dangerously-skip-permissions` is refused there?

## Before filing

The behavior claims below were observed running `happy` headless on one Linux box,
not read from Happy's source. Confirm the flag names and the root/yolo behavior
against the installed version (`happy --help`, `happy claude --help`) before posting,
so the issue is accurate and the maintainers don't bounce it. The issue is written
to ASK where it isn't sure, not to assert.
