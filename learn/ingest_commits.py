"""
learn/ingest_commits.py — read all of Michael's repos, put the commits in a DB.

Walks every git repo under his GitHub folder and loads the full commit history into
a local SQLite database (`data/commits.db`) with an FTS5 search index. This is my
primary sense organ for learning who he is and what he's working on. The DB stays
LOCAL (gitignored): it holds his private repo history. Only the DISTILLED model that
learn/profile.py writes gets committed.

Read-only on his repos (charter rule 2). Fail-open per repo: one broken repo never
stops the ingest.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GH_ROOT = os.path.dirname(HERE)  # the GitHub folder that holds ember + his repos
DB = os.path.join(HERE, "data", "commits.db")

US = "\x1f"  # field sep
RS = "\x1e"  # record sep
FMT = US.join(["%H", "%ad", "%an", "%ae", "%s", "%b"]) + RS


def _repos():
    out = []
    for name in sorted(os.listdir(GH_ROOT)):
        path = os.path.join(GH_ROOT, name)
        if name == "ember":
            continue  # don't navel-gaze on my own repo
        if os.path.isdir(os.path.join(path, ".git")):
            out.append((name, path))
    return out


def _log(path):
    """Full history as (hash, date, author, email, subject, ai_assisted) rows."""
    try:
        raw = subprocess.run(
            ["git", "-C", path, "log", "--no-merges", "--date=short",
             "--pretty=format:" + FMT],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=60,
        ).stdout
    except Exception:
        return []
    rows = []
    for rec in raw.split(RS):
        rec = rec.strip("\n")
        if not rec:
            continue
        parts = rec.split(US)
        if len(parts) < 6:
            continue
        h, date, an, ae, subj, body = parts[:6]
        blob = (subj + " " + body).lower()
        ai = 1 if ("co-authored-by" in blob or "claude" in blob
                   or "generated with" in blob) else 0
        rows.append((h, date, an, ae, subj, ai))
    return rows


def main():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    con = sqlite3.connect(DB)
    con.executescript("""
        DROP TABLE IF EXISTS commits;
        CREATE TABLE commits (
            repo TEXT, hash TEXT, date TEXT, author TEXT, email TEXT,
            subject TEXT, ai_assisted INTEGER
        );
        DROP TABLE IF EXISTS commits_fts;
        CREATE VIRTUAL TABLE commits_fts USING fts5(subject, repo, content='');
    """)
    total = 0
    for name, path in _repos():
        rows = _log(path)
        for r in rows:
            con.execute(
                "INSERT INTO commits (repo,hash,date,author,email,subject,ai_assisted)"
                " VALUES (?,?,?,?,?,?,?)", (name,) + r)
            con.execute("INSERT INTO commits_fts (subject, repo) VALUES (?,?)",
                        (r[4], name))
        total += len(rows)
        print(f"  {name}: {len(rows)} commits")
    con.commit()
    con.close()
    print(f"\ningested {total} commits from {len(_repos())} repos -> {DB}")


if __name__ == "__main__":
    main()
