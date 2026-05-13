"""Tests for agent_office.db.database"""
import pytest

import agent_office.db.database as db_module
from agent_office.db.database import (
    RunStatus,
    get_all_runs,
    get_steps_for_run,
    init_db,
    insert_run,
    insert_step,
    update_run,
)


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Point DB_PATH at a fresh temp file for every test."""
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test_runs.db")
    init_db()


class TestRunStatus:
    def test_values(self):
        assert RunStatus.RUNNING == "running"
        assert RunStatus.SUCCESS == "success"
        assert RunStatus.FAILED == "failed"

    def test_is_str(self):
        assert isinstance(RunStatus.SUCCESS, str)


class TestInitDb:
    def test_creates_table(self, tmp_path, monkeypatch):
        import sqlite3
        path = tmp_path / "fresh.db"
        monkeypatch.setattr(db_module, "DB_PATH", path)
        init_db()
        with sqlite3.connect(path) as con:
            rows = con.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='runs'"
            ).fetchall()
        assert len(rows) == 1

    def test_idempotent(self):
        # Calling init_db a second time must not raise
        init_db()


class TestInsertRun:
    def test_returns_positive_id(self):
        run_id = insert_run("test run", "EmailCrew", ["email-agent"])
        assert isinstance(run_id, int) and run_id > 0

    def test_status_is_running(self):
        run_id = insert_run("r", "T", ["a"])
        runs = get_all_runs()
        match = next(r for r in runs if r["id"] == run_id)
        assert match["status"] == RunStatus.RUNNING

    def test_agents_joined(self):
        insert_run("r", "T", ["agent-a", "agent-b"])
        runs = get_all_runs()
        assert "agent-a, agent-b" in runs[0]["agents"]

    def test_multiple_inserts_unique_ids(self):
        id1 = insert_run("r1", "T", ["a"])
        id2 = insert_run("r2", "T", ["a"])
        assert id1 != id2


class TestUpdateRun:
    def test_success_status(self):
        run_id = insert_run("r", "T", ["a"])
        update_run(run_id, status=RunStatus.SUCCESS, total_tokens=100,
                   prompt_tokens=60, completion_tokens=40)
        runs = get_all_runs()
        match = next(r for r in runs if r["id"] == run_id)
        assert match["status"] == RunStatus.SUCCESS
        assert match["total_tokens"] == 100
        assert match["prompt_tokens"] == 60
        assert match["completion_tokens"] == 40

    def test_failed_status_with_error(self):
        run_id = insert_run("r", "T", ["a"])
        update_run(run_id, status=RunStatus.FAILED, error="something broke")
        runs = get_all_runs()
        match = next(r for r in runs if r["id"] == run_id)
        assert match["status"] == RunStatus.FAILED
        assert match["error"] == "something broke"

    def test_cost_calculation(self):
        run_id = insert_run("r", "T", ["a"])
        # 1_000_000 prompt + 1_000_000 completion → $2.50 + $10.00 = $12.50
        update_run(run_id, status=RunStatus.SUCCESS,
                   prompt_tokens=1_000_000, completion_tokens=1_000_000)
        runs = get_all_runs()
        match = next(r for r in runs if r["id"] == run_id)
        assert abs(match["estimated_cost_usd"] - 12.50) < 1e-6

    def test_zero_tokens_zero_cost(self):
        run_id = insert_run("r", "T", ["a"])
        update_run(run_id, status=RunStatus.SUCCESS)
        runs = get_all_runs()
        match = next(r for r in runs if r["id"] == run_id)
        assert match["estimated_cost_usd"] == 0.0

    def test_finished_at_set(self):
        run_id = insert_run("r", "T", ["a"])
        update_run(run_id, status=RunStatus.SUCCESS)
        runs = get_all_runs()
        match = next(r for r in runs if r["id"] == run_id)
        assert match["finished_at"] is not None


class TestGetAllRuns:
    def test_empty_returns_list(self):
        assert get_all_runs() == []

    def test_returns_dicts(self):
        insert_run("r", "T", ["a"])
        runs = get_all_runs()
        assert isinstance(runs[0], dict)

    def test_ordered_newest_first(self):
        id1 = insert_run("r1", "T", ["a"])
        id2 = insert_run("r2", "T", ["a"])
        runs = get_all_runs()
        assert runs[0]["id"] == id2
        assert runs[1]["id"] == id1


class TestInsertStep:
    def test_inserts_step(self):
        run_id = insert_run("r", "T", ["a"])
        insert_step(run_id, 0, "agent-a", "Do thing", "output preview", 1.23)
        steps = get_steps_for_run(run_id)
        assert len(steps) == 1
        s = steps[0]
        assert s["run_id"] == run_id
        assert s["step_index"] == 0
        assert s["agent"] == "agent-a"
        assert s["task_description"] == "Do thing"
        assert s["output_preview"] == "output preview"
        assert abs(s["duration_s"] - 1.23) < 0.01

    def test_multiple_steps_ordered(self):
        run_id = insert_run("r", "T", ["a"])
        insert_step(run_id, 0, "a1", "task1", "out1", 0.5)
        insert_step(run_id, 1, "a2", "task2", "out2", 1.5)
        steps = get_steps_for_run(run_id)
        assert len(steps) == 2
        assert steps[0]["step_index"] == 0
        assert steps[1]["step_index"] == 1

    def test_empty_for_unknown_run(self):
        assert get_steps_for_run(9999) == []

    def test_steps_isolated_per_run(self):
        id1 = insert_run("r1", "T", ["a"])
        id2 = insert_run("r2", "T", ["a"])
        insert_step(id1, 0, "a", "t1", "o1", 1.0)
        insert_step(id2, 0, "b", "t2", "o2", 2.0)
        assert len(get_steps_for_run(id1)) == 1
        assert len(get_steps_for_run(id2)) == 1
        assert get_steps_for_run(id1)[0]["agent"] == "a"
        assert get_steps_for_run(id2)[0]["agent"] == "b"
