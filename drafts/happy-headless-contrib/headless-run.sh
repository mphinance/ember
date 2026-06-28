#!/usr/bin/env bash
# headless-run.sh — run Happy (Claude Code) once, unattended, on a schedule.
#
# A generic, hardened wrapper for firing a fixed prompt through `happy -p` with no
# human at the keyboard. Distilled from a real 24/7 autonomous-agent loop; the five
# guards below are each here because their absence broke something in production.
#
# Quick start:
#   1) Install + auth Happy on the box (`happy doctor` should be green).
#   2) Put your one-cycle instructions in prompt.txt next to this script.
#   3) Set REPO and ALLOWED_TOOLS below.
#   4) chmod +x headless-run.sh and cron it, offset from any sibling job, e.g.:
#        15 */2 * * * /path/to/headless-run.sh >> /var/log/happy-headless.log 2>&1
#
# Halt switch: a `STOP` file in the repo root freezes the loop (no run fires).
# Remove STOP to resume — no need to touch crontab.

set -u
export PATH=/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin:$HOME/.npm-global/bin

# --- config -----------------------------------------------------------------
REPO="${HOME}/myproject"                       # working dir / repo to run in
BRANCH="main"                                   # branch to sync to
PROMPT="$(dirname "$0")/prompt.txt"             # the instructions, on stdin
ALLOWED_TOOLS="Bash Write Edit Read Glob Grep"  # THIS is your permission policy
LOCK="/tmp/happy-headless.lock"                 # share with any sibling job on REPO
RUN_TIMEOUT=1200                                # hard ceiling, seconds
# Optional: pin a model for this job without touching global config.
# CLAUDE_ENV=(--claude-env ANTHROPIC_MODEL=claude-sonnet-4-6)
CLAUDE_ENV=()
# ----------------------------------------------------------------------------

stamp() { date -u +%Y-%m-%dT%H:%MZ; }

cd "$REPO" || { echo "[$(stamp)] no repo at $REPO"; exit 1; }

# (0) Halt switch — checked before we take the lock or touch anything.
if [ -f STOP ]; then
  echo "[$(stamp)] HALTED (STOP file present)"; exit 0
fi

# (1) Single-flight. Non-blocking: a late tick skips rather than piling up. If a
#     deterministic sibling job writes to this same repo, point it at the SAME lock
#     so the two can never run together (one of them may do `git reset --hard`,
#     which would wipe the other's uncommitted work mid-run).
exec 9>"$LOCK"
if ! flock -w 120 9; then
  echo "[$(stamp)] lock busy >2min, skipping this tick"; exit 0
fi

# (2) Clean sync — take the remote exactly. reset --hard CANNOT leave conflict
#     markers; stash/rebase can, and a half-merged generated file breaks your deploy.
#     Fail open: if the sync fails, do nothing this tick rather than run on a bad tree.
git fetch -q origin && git reset --hard -q "origin/${BRANCH}" || {
  echo "[$(stamp)] sync failed, skipping"; exit 0; }

# (3) The run. Print mode, prompt on stdin, allowlist = no permission prompts.
#     `timeout` bounds a stall. We do NOT use --dangerously-skip-permissions / yolo:
#     it is refused on root/service accounts and disables all guardrails; a scoped
#     allowlist gives no-prompt behavior AND a blast-radius limit.
echo "[$(stamp)] starting headless run"
timeout "$RUN_TIMEOUT" happy -p \
  --allowedTools "$ALLOWED_TOOLS" \
  "${CLAUDE_ENV[@]}" \
  < "$PROMPT"
rc=$?
echo "[$(stamp)] run finished (exit ${rc})"

# (4) If a sibling job is the SOLE writer of some generated file, revert any stray
#     edit to it here as belt-and-suspenders, so this run can never become a second
#     writer. Uncomment and set the path:
# git checkout -q -- path/to/generated-artifact.json 2>/dev/null || true

# The run commits and pushes its own work (that's what deploys). Nothing to do here.
exit 0
