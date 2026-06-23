#!/usr/bin/env bash
# ops/refresh.sh — the always-on DATA layer, runs on a Linux box via cron.
# This is the deterministic half of the loop: it re-runs the scan every 30 min and
# pushes fresh data. NO LLM, no auth beyond git push. The push deploys (GitHub Pages).
#
# Install on the box (one time):
#   gh repo clone <you>/<repo> ~/ember && cd ~/ember
#   python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # or the deps
#   git config user.name ember && git config user.email ember@local && gh auth setup-git
#   cp ops/refresh.sh ~/ember/refresh.sh && chmod +x ~/ember/refresh.sh
#   ( crontab -l 2>/dev/null; echo '*/30 * * * * /root/ember/refresh.sh >> /var/log/ember-refresh.log 2>&1' ) | crontab -
#
# The two design rules that keep it from corrupting the repo (learned the hard way):
#   1. flock => only one refresh runs at a time (a hung yfinance call can't pile up).
#   2. git reset --hard (never stash/rebase) => a sync can NEVER leave conflict markers.
#      This box is the SOLE committer of docs/data/scan.json; the feature-cycle agent
#      commits everything else. Two writers, different files, zero possible conflict.
export PATH=/usr/local/bin:/usr/bin:/bin
exec 9>/tmp/ember-refresh.lock
flock -n 9 || exit 0
cd "$HOME/ember" || exit 1
git fetch -q origin && git reset --hard -q origin/master || exit 0
.venv/bin/python -m wheelforge.build_site_data >/tmp/ember-build.log 2>&1 || exit 0
if ! git diff --quiet -- docs/data/scan.json; then
  git add docs/data/scan.json
  git -c user.name=ember -c user.email=ember@mphinance.local commit -q -m "scan refresh $(date -u +%Y-%m-%dT%H:%MZ): live universe rescored on the box"
  git push -q origin master && echo "[$(date -u +%H:%MZ)] refreshed + pushed"
fi
