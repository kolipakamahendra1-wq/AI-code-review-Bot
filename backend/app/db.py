import sqlite3
import threading
from contextlib import closing
from pathlib import Path

from . import config

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  repo TEXT, pr_number INTEGER, head_sha TEXT, title TEXT,
  source TEXT NOT NULL, model TEXT, score INTEGER, summary TEXT,
  files_reviewed INTEGER, status TEXT NOT NULL DEFAULT 'done', error TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(repo, pr_number, head_sha)
);
CREATE TABLE IF NOT EXISTS findings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  review_id INTEGER NOT NULL REFERENCES reviews(id) ON DELETE CASCADE,
  file TEXT, line INTEGER, severity TEXT, category TEXT,
  title TEXT, message TEXT, suggestion TEXT
);
"""


def _conn() -> sqlite3.Connection:
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(config.DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    c.executescript(SCHEMA)
    return c


def already_reviewed(repo: str, pr: int, sha: str) -> bool:
    with _lock, closing(_conn()) as c:
        return c.execute(
            "SELECT 1 FROM reviews WHERE repo=? AND pr_number=? AND head_sha=? AND status='done'",
            (repo, pr, sha),
        ).fetchone() is not None


def save_review(result: dict, *, source: str, repo=None, pr_number=None, head_sha=None,
                title=None, status="done", error=None) -> int:
    with _lock, closing(_conn()) as c, c:
        if repo is not None:  # replace a previous (e.g. failed) attempt for the same head
            c.execute("DELETE FROM reviews WHERE repo=? AND pr_number=? AND head_sha=?",
                      (repo, pr_number, head_sha))
        cur = c.execute(
            """INSERT INTO reviews
               (repo, pr_number, head_sha, title, source, model, score, summary,
                files_reviewed, status, error) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (repo, pr_number, head_sha, title, source, result.get("model"), result.get("score"),
             result.get("summary"), result.get("files_reviewed"), status, error),
        )
        rid = cur.lastrowid
        for f in result.get("findings", []):
            c.execute(
                """INSERT INTO findings (review_id,file,line,severity,category,title,message,suggestion)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (rid, f["file"], f["line"], f["severity"], f["category"], f["title"],
                 f["message"], f.get("suggestion", "")),
            )
        return rid


def list_reviews(limit: int = 50) -> list[dict]:
    with _lock, closing(_conn()) as c:
        rows = c.execute(
            """SELECT r.*, (SELECT COUNT(*) FROM findings f WHERE f.review_id=r.id) AS finding_count
               FROM reviews r ORDER BY r.id DESC LIMIT ?""", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_review(rid: int) -> dict | None:
    with _lock, closing(_conn()) as c:
        r = c.execute("SELECT * FROM reviews WHERE id=?", (rid,)).fetchone()
        if not r:
            return None
        fs = c.execute("SELECT * FROM findings WHERE review_id=? ORDER BY id", (rid,)).fetchall()
        return {**dict(r), "findings": [dict(f) for f in fs]}


def stats() -> dict:
    with _lock, closing(_conn()) as c:
        total = c.execute(
            "SELECT COUNT(*), COALESCE(AVG(score),0) FROM reviews WHERE status='done'").fetchone()
        sev = {r[0]: r[1] for r in c.execute("SELECT severity, COUNT(*) FROM findings GROUP BY severity")}
        cat = {r[0]: r[1] for r in c.execute("SELECT category, COUNT(*) FROM findings GROUP BY category")}
        nf = c.execute("SELECT COUNT(*) FROM findings").fetchone()[0]
        return {"reviews": total[0], "avg_score": round(total[1]), "findings": nf,
                "by_severity": sev, "by_category": cat}
