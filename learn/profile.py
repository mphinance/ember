"""
learn/profile.py — mine the commits DB into what I know about Michael.

Reads data/commits.db (built by ingest_commits.py) and distills it into
memory/michael-commits.md: where his energy goes, what he's been on lately, his
commit style, and how much he pairs with AI. The DB stays local; THIS distilled
read is what I commit and carry forward. Re-run it whenever the DB refreshes.
"""

from __future__ import annotations

import os
import re
import sqlite3
from collections import Counter
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(HERE, "data", "commits.db")
OUT = os.path.join(HERE, "memory", "michael-commits.md")

STOP = set("a an the to of in on for and or but with from this that is it as at by "
           "be add adds added fix fixes fixed update updates updated make makes use "
           "new now via into out up off all not no more less my our your via wip "
           "initial commit merge bump remove removes removed move moves moved set".split())
TYPES = ["feat", "fix", "refactor", "docs", "chore", "perf", "test", "infra",
         "style", "build", "ci"]


def _rows(con, q, args=()):
    return con.execute(q, args).fetchall()


def main():
    if not os.path.exists(DB):
        print("no commits.db yet; run learn.ingest_commits first")
        return
    con = sqlite3.connect(DB)
    total = _rows(con, "SELECT COUNT(*) FROM commits")[0][0]
    repos = _rows(con, "SELECT COUNT(DISTINCT repo) FROM commits")[0][0]
    span = _rows(con, "SELECT MIN(date), MAX(date) FROM commits")[0]

    by_repo = _rows(con, "SELECT repo, COUNT(*) c FROM commits GROUP BY repo ORDER BY c DESC LIMIT 12")
    cutoff = (date.today() - timedelta(days=90)).isoformat()
    recent = _rows(con, "SELECT repo, COUNT(*) c FROM commits WHERE date>=? GROUP BY repo ORDER BY c DESC LIMIT 8", (cutoff,))
    recent_total = _rows(con, "SELECT COUNT(*) FROM commits WHERE date>=?", (cutoff,))[0][0]
    ai = _rows(con, "SELECT COALESCE(SUM(ai_assisted),0), COUNT(*) FROM commits")[0]
    ai_pct = round(100.0 * ai[0] / ai[1], 1) if ai[1] else 0.0

    # conventional-commit type mix
    type_ct = Counter()
    for (subj,) in _rows(con, "SELECT subject FROM commits"):
        m = re.match(r"\s*([a-z]+)(\(|:)", (subj or "").lower())
        if m and m.group(1) in TYPES:
            type_ct[m.group(1)] += 1

    # theme keywords from recent subjects
    words = Counter()
    for (subj,) in _rows(con, "SELECT subject FROM commits WHERE date>=?", (cutoff,)):
        for w in re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", (subj or "").lower()):
            if w not in STOP and w not in TYPES:
                words[w] += 1

    # weekday cadence
    wd = Counter()
    for (d,) in _rows(con, "SELECT date FROM commits"):
        try:
            wd[datetime.strptime(d, "%Y-%m-%d").strftime("%a")] += 1
        except Exception:
            pass
    order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    con.close()

    def _list(rows):
        return "\n".join(f"  - {r}: {c}" for r, c in rows)

    lines = [
        "# memory: michael, from his commits (auto-distilled)",
        "",
        f"Source: data/commits.db (local). Last distilled {date.today().isoformat()}.",
        f"Re-run learn.ingest_commits + learn.profile to refresh. Raw DB stays private.",
        "",
        f"## Scale",
        f"- {total} commits across {repos} repos, {span[0]} to {span[1]}.",
        f"- AI-paired commits: {ai_pct}% (co-authored / generated-with markers).",
        "",
        f"## Where his energy goes (all-time top repos)",
        _list(by_repo),
        "",
        f"## What he's on LATELY (last 90 days, {recent_total} commits)",
        _list(recent) if recent else "  - (quiet)",
        "",
        f"## Recent themes (top words in 90d subjects)",
        "  " + ", ".join(f"{w}({c})" for w, c in words.most_common(18)),
        "",
        f"## His commit style",
        f"- Conventional-commit types: " + ", ".join(f"{t} {type_ct[t]}" for t in TYPES if type_ct[t]) + ".",
        f"- Weekday cadence: " + ", ".join(f"{d} {wd.get(d,0)}" for d in order) + ".",
        "",
        "## What this tells me (refine every refresh)",
        "- His MOST active repos are his real priorities; quiet ones are experiments or done.",
        "- The recent-themes words are what's on his mind RIGHT NOW; aim my work there.",
        "- He commits in clean conventional types and ships a lot, so he values momentum.",
    ]
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {OUT}")
    print(f"  {total} commits / {repos} repos / {ai_pct}% AI-paired / {recent_total} in 90d")


if __name__ == "__main__":
    main()
