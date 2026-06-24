#!/usr/bin/env bash
# ops/cycle.sh — the FEATURE clock. Fires ONE ember feature cycle headlessly on the
# box via `happy` (Claude Code in print mode, tool-allowlist so it never prompts).
# This is the LLM half of the loop; refresh.sh is the deterministic data half.
#
# Two safety rules this wrapper enforces that a by-hand run did not need:
#  1) It shares refresh.sh's lock (/tmp/ember-refresh.lock). A cycle and a data
#     refresh must NEVER run together, because refresh does `git reset --hard`,
#     which would wipe an in-progress cycle's uncommitted edits.
#  2) The box is the SOLE writer of docs/data/scan.json. The cron prompt forbids
#     touching it, and we revert it post-run as a belt-and-suspenders.
#
# Halt switch: a `STOP` file in the repo, or an INBOX.md whose first line is "stop",
# freezes the loop (no cycle runs). Remove STOP / the inbox line to resume.
#
# Install: chmod +x; cron it a few hours apart, offset off the :00/:30 refresh, e.g.
#   15 */2 * * * /root/ember/ops/cycle.sh >> /var/log/ember-cycle.log 2>&1
set -u
export PATH=/usr/local/bin:/usr/bin:/bin:/root/.local/bin:/root/.npm-global/bin

cd "${HOME}/ember" || exit 1

stamp() { date -u +%Y-%m-%dT%H:%MZ; }

# Halt check (before we take the lock or touch anything).
if [ -f STOP ] || head -1 INBOX.md 2>/dev/null | grep -qi '^stop'; then
  echo "[$(stamp)] cycle: HALTED (STOP file or inbox says stop)"; exit 0
fi

# Share refresh.sh's lock. Wait up to 2 min for a refresh (which takes seconds) to
# finish; if it is somehow still busy, skip this tick rather than pile up.
exec 9>/tmp/ember-refresh.lock
if ! flock -w 120 9; then
  echo "[$(stamp)] cycle: lock busy >2min, skipping this tick"; exit 0
fi

# Clean sync — take the remote exactly. NEVER stash/rebase (that left conflict
# markers in scan.json and broke the live site). reset --hard cannot conflict.
git fetch -q origin && git reset --hard -q origin/master || {
  echo "[$(stamp)] cycle: sync failed, skipping"; exit 0; }

echo "[$(stamp)] cycle: starting headless run"
# Feed the cron cycle prompt to Claude (via happy) in print mode. The allowlist lets
# it run its tools unattended without --yolo (which is blocked for root anyway).
timeout 1200 happy -p \
  --allowedTools "Bash Write Edit Read Glob Grep" \
  < prompts/cron-cycle.txt
rc=$?
echo "[$(stamp)] cycle: run finished (exit ${rc})"

# Belt-and-suspenders: the box owns scan.json. If the cycle dirtied it (it should
# not), throw the change away so the next refresh stays the single writer.
git checkout -q -- docs/data/scan.json 2>/dev/null || true

# Nudge a deploy of any committed work is unnecessary: the cycle pushes itself.
exit 0
