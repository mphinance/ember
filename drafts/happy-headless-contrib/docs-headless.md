# Running Happy unattended (headless / cron / CI)

Happy is usually driven interactively: start a session, pair your phone, watch it
work, approve permissions as they pop. But the same `happy` binary runs just as well
with no human in the loop — fired by cron, a systemd timer, or a CI step — as long as
you give it a way to act without permission prompts and you wrap it so a single bad
run can't wedge the machine.

This page is the recipe. It assumes Happy is installed and authenticated on the box
already (`happy doctor` is green), and that you want it to run a fixed prompt on a
schedule and exit.

> Flag names below match `happy --help` at the time of writing. Run it yourself to
> confirm against your version; Happy passes many flags straight through to Claude
> Code, so the exact spelling can drift.

## The shape of a headless run

```bash
happy -p --allowedTools "Bash Write Edit Read Glob Grep" < prompt.txt
```

- `-p` (print mode) runs once against the prompt on stdin and prints the result to
  stdout instead of opening an interactive session. Exit code reflects success.
- `--allowedTools "..."` is the key to running with **zero prompts**: every tool in
  the allowlist runs without asking. Anything not listed still stops and waits, which
  in a headless context means it hangs until your timeout fires — so the allowlist
  IS your permission policy. Scope it to exactly the tools the prompt needs.
- The prompt arrives on stdin, so you keep it in a version-controlled file rather than
  jamming it into the command line.

That single line is the whole agent. Everything below is the wrapper that keeps it
from hurting you when a run goes sideways.

## Why not `--dangerously-skip-permissions` / yolo

The obvious "just don't ask me anything" flag is the dangerous-skip-permissions /
yolo mode. Two problems for automation:

1. It is refused outright on root and some service accounts (the exact accounts cron
   jobs tend to run as), so you can't rely on it.
2. Even where it works, it is the wrong tool: it disables ALL guardrails, where what
   you actually want is "run THESE tools freely, refuse everything else." A scoped
   `--allowedTools` allowlist gives you the no-prompt behavior AND keeps a blast-radius
   limit. It is both the safer and the more available path.

So for unattended runs, prefer `--allowedTools`. (If you genuinely need a tool that
takes a path you can't predict, scope the prompt and the working directory instead of
reaching for yolo.)

## The five wrapper rules (learned the hard way)

A bare `happy -p` on a cron will eventually hang, double-fire, or commit garbage. Five
cheap guards prevent every failure we hit:

1. **Bound it with `timeout`.** A model can stall on a network hiccup forever. Wrap
   the call in `timeout 1200 happy -p ...` so a stuck run dies instead of holding the
   machine and blocking the next tick.

2. **Single-flight with `flock`.** If a run can outlast its interval, two will overlap
   and race. A non-blocking `flock` makes a late tick skip rather than pile up. If a
   separate deterministic job writes to the same repo, share ONE lock between them so
   they can never run together.

3. **Fail open, never crash the loop.** Every step (sync, build, the run itself) should
   degrade to "do nothing this tick" on error, not abort hard. A missing data point is
   a missing data point; it is not a reason to wedge the schedule.

4. **Sync with `git reset --hard`, never stash/rebase.** If the headless agent commits
   and pushes, the box has to re-sync each tick. `git fetch && git reset --hard
   origin/<branch>` cannot leave conflict markers in a generated file; `git stash` and
   `git pull --rebase` can, and a half-merged file silently breaks whatever you deploy.
   Take the remote exactly.

5. **One writer per file.** If both a headless agent and a deterministic job commit to
   the same repo, split them by file — the agent owns the code, the job owns the
   generated artifact — and never let both touch the same path. Two writers on one file
   is the dual-writer race, and it WILL surface as a conflict marker in production.

## A halt switch you can hit from anywhere

Give yourself a kill switch that doesn't require killing the cron. Check for a sentinel
before doing any work:

```bash
if [ -f STOP ] || head -1 INBOX.md 2>/dev/null | grep -qi '^stop'; then
  exit 0
fi
```

Now `touch STOP` (or a line in a file the agent reads) freezes the loop; deleting it
thaws. This is far less stressful than racing to `crontab -e` while a run misbehaves.

## Selecting a model per run

Pass model and other Claude env through without editing global config:

```bash
happy -p --claude-env ANTHROPIC_MODEL=claude-sonnet-4-6 < prompt.txt
```

Handy when you want a cheap model for a frequent low-stakes job and a stronger one for
the occasional heavy cycle, from the same install.

## Putting it together

See `headless-run.sh` in this directory for a complete, commented wrapper that applies
all five rules plus the halt switch. Install it as a cron line a few minutes off any
other job that touches the same repo:

```
15 */2 * * * /path/to/headless-run.sh >> /var/log/happy-headless.log 2>&1
```

## Checklist

- [ ] `happy doctor` green on the box, under the account cron will use
- [ ] Prompt lives in a file, fed on stdin
- [ ] `--allowedTools` scoped to exactly what the prompt needs (this is your permission policy)
- [ ] `timeout` around the call
- [ ] `flock` so ticks can't overlap (shared with any sibling job on the same repo)
- [ ] Every step fails open
- [ ] Re-sync is `git reset --hard`, never stash/rebase
- [ ] One writer per file if a second job shares the repo
- [ ] A `STOP` sentinel checked before any work
