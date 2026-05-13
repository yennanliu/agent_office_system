"""Tests for agent_office.db.tracker"""
from unittest.mock import MagicMock

import pytest

import agent_office.db.database as db_module
from agent_office.db.database import RunStatus, get_all_runs, get_steps_for_run, init_db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test_runs.db")
    init_db()


def _make_crew(total=100, prompt=60, completion=40, raises=None):
    crew = MagicMock()
    if raises:
        crew.kickoff.side_effect = raises
    else:
        crew.kickoff.return_value = "crew result"
    metrics = MagicMock()
    metrics.total_tokens = total
    metrics.prompt_tokens = prompt
    metrics.completion_tokens = completion
    crew.calculate_usage_metrics.return_value = metrics
    return crew


class TestTrackCrewRun:
    def test_success_stores_run(self):
        from agent_office.db.tracker import track_crew_run
        crew = _make_crew(total=200, prompt=120, completion=80)
        result = track_crew_run("test", "EmailCrew", ["email-agent"], crew)

        assert result == "crew result"
        runs = get_all_runs()
        assert len(runs) == 1
        assert runs[0]["status"] == RunStatus.SUCCESS
        assert runs[0]["total_tokens"] == 200
        assert runs[0]["prompt_tokens"] == 120
        assert runs[0]["completion_tokens"] == 80

    def test_failure_stores_error_and_reraises(self):
        from agent_office.db.tracker import track_crew_run
        crew = _make_crew(raises=RuntimeError("boom"))

        with pytest.raises(RuntimeError, match="boom"):
            track_crew_run("test", "EmailCrew", ["email-agent"], crew)

        runs = get_all_runs()
        assert runs[0]["status"] == RunStatus.FAILED
        assert "boom" in runs[0]["error"]

    def test_run_name_and_job_type_stored(self):
        from agent_office.db.tracker import track_crew_run
        crew = _make_crew()
        track_crew_run("My Run", "StockSummaryCrew", ["stock-agent"], crew)

        runs = get_all_runs()
        assert runs[0]["name"] == "My Run"
        assert runs[0]["job_type"] == "StockSummaryCrew"

    def test_agents_stored(self):
        from agent_office.db.tracker import track_crew_run
        crew = _make_crew()
        track_crew_run("r", "T", ["agent-a", "agent-b"], crew)

        runs = get_all_runs()
        assert "agent-a" in runs[0]["agents"]
        assert "agent-b" in runs[0]["agents"]

    def test_task_callback_records_steps(self):
        from agent_office.db.tracker import track_crew_run

        crew = _make_crew()

        # Simulate crew.kickoff() firing the task_callback for each task
        def fake_kickoff():
            task_out = MagicMock()
            task_out.agent = "Test Agent"
            task_out.description = "Do something"
            task_out.raw = "output text"
            crew.task_callback(task_out)
            return "done"

        crew.kickoff.side_effect = fake_kickoff
        track_crew_run("r", "T", ["a"], crew)

        runs = get_all_runs()
        steps = get_steps_for_run(runs[0]["id"])
        assert len(steps) == 1
        assert steps[0]["agent"] == "Test Agent"
        assert steps[0]["task_description"] == "Do something"
        assert steps[0]["output_preview"] == "output text"
        assert steps[0]["step_index"] == 0
        assert steps[0]["duration_s"] >= 0

    def test_multiple_steps_recorded_in_order(self):
        from agent_office.db.tracker import track_crew_run

        crew = _make_crew()

        def fake_kickoff():
            for i, label in enumerate(["Step A", "Step B", "Step C"]):
                task_out = MagicMock()
                task_out.agent = f"agent-{i}"
                task_out.description = label
                task_out.raw = f"output {i}"
                crew.task_callback(task_out)
            return "done"

        crew.kickoff.side_effect = fake_kickoff
        track_crew_run("r", "T", ["a"], crew)

        runs = get_all_runs()
        steps = get_steps_for_run(runs[0]["id"])
        assert len(steps) == 3
        assert [s["step_index"] for s in steps] == [0, 1, 2]
        assert steps[0]["task_description"] == "Step A"
        assert steps[2]["task_description"] == "Step C"
