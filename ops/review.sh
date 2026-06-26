#!/usr/bin/env bash
# ops/review.sh — the CRITIC clock. Runs ops/critic.py: a cheap single-shot reviewer that
# reads the code + live picks + journal through a ROTATING lens and a ROTATING model, and
# appends 1-3 steering notes to INBOX.md. ember (the Opus builder) reads INBOX first every
# cycle, so a DIFFERENT model keeps the builder honest and aimed.
#
# Models: if ops/.critic.env supplies OPENROUTER_API_KEY, critic.py rotates GPT / Gemini /
# DeepSeek / Grok / Claude / etc. Without a key it falls back to local Sonnet via happy.
#
# Leash: critic.py only APPENDS to INBOX.md. This wrapper hard-reverts anything else before
# committing, so the critic physically cannot touch code or scan.json. Shares the builder/
# refresh lock so it never runs on top of a cycle's `git reset --hard`.
#
# Install (offset from refresh :00/:30 and builder :15-even): every 3h at :45 ->
#   45 1,4,7,10,13,16,19,22 * * * /root/ember/ops/review.sh >> /var/log/ember-review.log 2>&1
set -u
export PATH=/usr/local/bin:/usr/bin:/bin:/root/.local/bin:/root/.npm-global/bin
cd "${HOME}/ember" || exit 1
stamp() { date -u +%Y-%m-%dT%H:%MZ; }

if [ -f STOP ] || head -1 INBOX.md 2>/dev/null | grep -qi '^stop'; then
  echo "[$(stamp)] review: HALTED (STOP/inbox)"; exit 0
fi

# OpenRouter key (gitignored). Absent -> critic.py uses the keyless local-Sonnet fallback.
[ -f ops/.critic.env ] && . ops/.critic.env
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}"

# Share the builder/refresh lock.
exec 9>/tmp/ember-refresh.lock
flock -w 120 9 || { echo "[$(stamp)] review: lock busy >2min, skip"; exit 0; }

git fetch -q origin && git reset --hard -q origin/master || {
  echo "[$(stamp)] review: sync failed, skip"; exit 0; }

echo "[$(stamp)] review: starting"
PY="$( [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3 )"
cp INBOX.md /tmp/ember-inbox.before
timeout 360 "$PY" ops/critic.py
echo "[$(stamp)] review: critic finished (exit $?)"

# Hard guard: critic may ONLY change INBOX.md. critic.py writes nothing else, but to be
# certain, revert any tracked change and keep just the inbox it appended to. (No `git clean`
# here on purpose: it could delete unrelated untracked files in the box working tree.)
cp INBOX.md /tmp/ember-inbox.after
git checkout -q -- . 2>/dev/null || true
cp /tmp/ember-inbox.after INBOX.md

if ! git diff --quiet -- INBOX.md; then
  git add INBOX.md
  git -c user.name=ember-critic -c user.email=critic@mphinance.local \
      commit -q -m "critic: steering for ember $(stamp)"
  git push -q origin master && echo "[$(stamp)] review: inbox updated + pushed"
else
  echo "[$(stamp)] review: nothing new to add this run"
fi
exit 0
