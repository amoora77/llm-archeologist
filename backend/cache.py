import sqlite3
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Any


DB_PATH = Path(__file__).parent / "cache.db"


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                cache_key TEXT PRIMARY KEY,
                repo_url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                report_json TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analysis_jobs (
                job_id TEXT PRIMARY KEY,
                repo_url TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                report_id TEXT
            )
        """)


def make_cache_key(repo_url: str, latest_commit_hash: str) -> str:
    raw = f"{repo_url}:{latest_commit_hash}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def get_cached_report(cache_key: str) -> dict[str, Any] | None:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT report_json FROM reports WHERE cache_key = ?", (cache_key,)
        ).fetchone()
    if row:
        return json.loads(row["report_json"])
    return None


def store_report(cache_key: str, repo_url: str, report: dict[str, Any]) -> None:
    with _get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO reports (cache_key, repo_url, created_at, report_json) VALUES (?, ?, ?, ?)",
            (cache_key, repo_url, datetime.utcnow().isoformat(), json.dumps(report, default=str)),
        )


def get_report_by_id(report_id: str) -> dict[str, Any] | None:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT report_json FROM reports WHERE cache_key = ?", (report_id,)
        ).fetchone()
    if row:
        return json.loads(row["report_json"])
    return None


def create_job(job_id: str, repo_url: str) -> None:
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO analysis_jobs (job_id, repo_url, status, created_at) VALUES (?, ?, 'pending', ?)",
            (job_id, repo_url, datetime.utcnow().isoformat()),
        )


def update_job(job_id: str, status: str, report_id: str | None = None) -> None:
    with _get_conn() as conn:
        conn.execute(
            "UPDATE analysis_jobs SET status = ?, report_id = ? WHERE job_id = ?",
            (status, report_id, job_id),
        )


def get_job(job_id: str) -> dict[str, Any] | None:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM analysis_jobs WHERE job_id = ?", (job_id,)
        ).fetchone()
    if row:
        return dict(row)
    return None
