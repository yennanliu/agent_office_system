"""Tests for agent_office.db.tracker"""
from unittest.mock import MagicMock

import pytest

import agent_office.db.database as db_module
from agent_office.db.database import RunStatus, get_all_runs, init_db


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
