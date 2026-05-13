import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parent.parent.parent.parent / "runs.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS runs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL,
    job_type            TEXT    NOT NULL,
    agents              TEXT    NOT NULL,
    started_at          TEXT    NOT NULL,
    finished_at         TEXT,
    status              TEXT    NOT NULL DEFAULT 'running',
    total_tokens        INTEGER DEFAULT 0,
    prompt_tokens       INTEGER DEFAULT 0,
    completion_tokens   INTEGER DEFAULT 0,
    estimated_cost_usd  REAL    DEFAULT 0.0,
    error               TEXT
)
"""

_CREATE_STEPS_TABLE = """
CREATE TABLE IF NOT EXISTS run_steps (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id           INTEGER NOT NULL REFERENCES runs(id),
    step_index       INTEGER NOT NULL,
    agent            TEXT,
    task_description TEXT,
    output_preview   TEXT,
    duration_s       REAL DEFAULT 0.0
)
"""


class RunStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@contextmanager
def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _conn() as con:
        con.execute(_CREATE_TABLE)
        con.execute(_CREATE_STEPS_TABLE)


def insert_run(name: str, job_type: str, agents: list[str]) -> int:
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO runs (name, job_type, agents, started_at, status) VALUES (?,?,?,?,?)",
            (name, job_type, ", ".join(agents), _now(), RunStatus.RUNNING),
        )
        return cur.lastrowid


def update_run(
    run_id: int,
    *,
    status: RunStatus,
    total_tokens: int = 0,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    error: str | None = None,
) -> None:
    # GPT-4o pricing: input $2.50/1M, output $10.00/1M
    cost = (prompt_tokens * 2.5 + completion_tokens * 10.0) / 1_000_000
    with _conn() as con:
        con.execute(
            """UPDATE runs SET
                status=?, finished_at=?,
                total_tokens=?, prompt_tokens=?, completion_tokens=?,
                estimated_cost_usd=?, error=?
               WHERE id=?""",
            (status, _now(), total_tokens, prompt_tokens, completion_tokens, cost, error, run_id),
        )


def get_all_runs() -> list[dict[str, Any]]:
    with _conn() as con:
        rows = con.execute("SELECT * FROM runs ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]


def insert_step(
    run_id: int,
    step_index: int,
    agent: str,
    task_description: str,
    output_preview: str,
    duration_s: float,
) -> None:
    with _conn() as con:
        con.execute(
            """INSERT INTO run_steps
               (run_id, step_index, agent, task_description, output_preview, duration_s)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (run_id, step_index, agent, task_description, output_preview, round(duration_s, 2)),
        )


def get_steps_for_run(run_id: int) -> list[dict[str, Any]]:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM run_steps WHERE run_id=? ORDER BY step_index",
            (run_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
