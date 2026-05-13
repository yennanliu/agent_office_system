"""Tests for crew orchestration (crewai.Task + track_crew_run mocked — no LLM calls)."""
from unittest.mock import patch

import pytest

import agent_office.db.database as db_module
from agent_office.db.database import init_db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test_runs.db")
    init_db()


# ── EmailCrew ─────────────────────────────────────────────────────────────────

class TestEmailCrew:
    @patch("agent_office.crews.email_crew.Task")
    @patch("agent_office.crews.email_crew.track_crew_run", return_value="email sent")
    @patch("agent_office.crews.email_crew.build_email_agent")
    @patch("agent_office.crews.email_crew.Crew")
    def test_run_returns_str(self, mock_crew_cls, mock_agent, mock_tracker, mock_task):
        from agent_office.crews.email_crew import EmailCrew
        result = EmailCrew().run(to="x@x.com", subject="Sub", intent="Say hello")
        assert result == "email sent"

    @patch("agent_office.crews.email_crew.Task")
    @patch("agent_office.crews.email_crew.track_crew_run", return_value="ok")
    @patch("agent_office.crews.email_crew.build_email_agent")
    @patch("agent_office.crews.email_crew.Crew")
    def test_job_type_is_classname(self, mock_crew_cls, mock_agent, mock_tracker, mock_task):
        from agent_office.crews.email_crew import EmailCrew
        EmailCrew().run(to="x@x.com", subject="S", intent="I")
        _, kwargs = mock_tracker.call_args
        assert kwargs.get("job_type") == "EmailCrew"

    @patch("agent_office.crews.email_crew.Task")
    @patch("agent_office.crews.email_crew.track_crew_run", return_value="ok")
    @patch("agent_office.crews.email_crew.build_email_agent")
    @patch("agent_office.crews.email_crew.Crew")
    def test_attachment_in_task_description(self, mock_crew_cls, mock_agent, mock_tracker, mock_task):
        from agent_office.crews.email_crew import EmailCrew
        EmailCrew().run(to="x@x.com", subject="S", intent="I",
                        attachments=["/tmp/report.pdf"])
        task_kwargs = mock_task.call_args[1]
        assert "/tmp/report.pdf" in task_kwargs["description"]

    @patch("agent_office.crews.email_crew.Task")
    @patch("agent_office.crews.email_crew.track_crew_run", return_value="ok")
    @patch("agent_office.crews.email_crew.build_email_agent")
    @patch("agent_office.crews.email_crew.Crew")
    def test_no_attachment_no_blank_line(self, mock_crew_cls, mock_agent, mock_tracker, mock_task):
        from agent_office.crews.email_crew import EmailCrew
        EmailCrew().run(to="x@x.com", subject="S", intent="I")
        task_kwargs = mock_task.call_args[1]
        assert "\n\n" not in task_kwargs["description"]

    @patch("agent_office.crews.email_crew.Task")
    @patch("agent_office.crews.email_crew.track_crew_run", return_value="ok")
    @patch("agent_office.crews.email_crew.build_email_agent")
    @patch("agent_office.crews.email_crew.Crew")
    def test_to_subject_intent_in_description(self, mock_crew_cls, mock_agent, mock_tracker, mock_task):
        from agent_office.crews.email_crew import EmailCrew
        EmailCrew().run(to="alice@x.com", subject="Q2 Report", intent="Report is ready")
        task_kwargs = mock_task.call_args[1]
        desc = task_kwargs["description"]
        assert "alice@x.com" in desc
        assert "Q2 Report" in desc
        assert "Report is ready" in desc


# ── DocSummaryCrew ────────────────────────────────────────────────────────────

class TestDocSummaryCrew:
    @patch("agent_office.crews.doc_summary_crew.Task")
    @patch("agent_office.crews.doc_summary_crew.track_crew_run", return_value="summary done")
    @patch("agent_office.crews.doc_summary_crew.build_email_agent")
    @patch("agent_office.crews.doc_summary_crew.build_doc_agent")
    @patch("agent_office.crews.doc_summary_crew.Crew")
    def test_run_returns_str(self, mock_crew_cls, mock_doc, mock_email, mock_tracker, mock_task):
        from agent_office.crews.doc_summary_crew import DocSummaryCrew
        result = DocSummaryCrew().run(doc_path="/tmp/doc.txt", recipients=["a@x.com"])
        assert result == "summary done"

    @patch("agent_office.crews.doc_summary_crew.Task")
    @patch("agent_office.crews.doc_summary_crew.track_crew_run", return_value="ok")
    @patch("agent_office.crews.doc_summary_crew.build_email_agent")
    @patch("agent_office.crews.doc_summary_crew.build_doc_agent")
    @patch("agent_office.crews.doc_summary_crew.Crew")
    def test_job_type_is_classname(self, mock_crew_cls, mock_doc, mock_email, mock_tracker, mock_task):
        from agent_office.crews.doc_summary_crew import DocSummaryCrew
        DocSummaryCrew().run(doc_path="/tmp/f.txt", recipients=["a@x.com"])
        _, kwargs = mock_tracker.call_args
        assert kwargs.get("job_type") == "DocSummaryCrew"

    @patch("agent_office.crews.doc_summary_crew.Task")
    @patch("agent_office.crews.doc_summary_crew.track_crew_run", return_value="ok")
    @patch("agent_office.crews.doc_summary_crew.build_email_agent")
    @patch("agent_office.crews.doc_summary_crew.build_doc_agent")
    @patch("agent_office.crews.doc_summary_crew.Crew")
    def test_doc_path_in_description(self, mock_crew_cls, mock_doc, mock_email, mock_tracker, mock_task):
        from agent_office.crews.doc_summary_crew import DocSummaryCrew
        DocSummaryCrew().run(doc_path="/tmp/report.pdf", recipients=["a@x.com"])
        first_task_kwargs = mock_task.call_args_list[0][1]
        assert "/tmp/report.pdf" in first_task_kwargs["description"]


# ── StockSummaryCrew ──────────────────────────────────────────────────────────

class TestStockSummaryCrew:
    @patch("agent_office.crews.stock_summary_crew.Task")
    @patch("agent_office.crews.stock_summary_crew.track_crew_run", return_value="stock done")
    @patch("agent_office.crews.stock_summary_crew.build_email_agent")
    @patch("agent_office.crews.stock_summary_crew.build_stock_agent")
    @patch("agent_office.crews.stock_summary_crew.Crew")
    def test_run_returns_str(self, mock_crew_cls, mock_stock, mock_email, mock_tracker, mock_task):
        from agent_office.crews.stock_summary_crew import StockSummaryCrew
        result = StockSummaryCrew().run(tickers=["AAPL"], recipients=["a@x.com"])
        assert result == "stock done"

    @patch("agent_office.crews.stock_summary_crew.Task")
    @patch("agent_office.crews.stock_summary_crew.track_crew_run", return_value="ok")
    @patch("agent_office.crews.stock_summary_crew.build_email_agent")
    @patch("agent_office.crews.stock_summary_crew.build_stock_agent")
    @patch("agent_office.crews.stock_summary_crew.Crew")
    def test_tickers_uppercased_in_name(self, mock_crew_cls, mock_stock, mock_email, mock_tracker, mock_task):
        from agent_office.crews.stock_summary_crew import StockSummaryCrew
        StockSummaryCrew().run(tickers=["aapl", "msft"], recipients=["a@x.com"])
        _, kwargs = mock_tracker.call_args
        assert "AAPL" in kwargs.get("name", "")
        assert "MSFT" in kwargs.get("name", "")

    @patch("agent_office.crews.stock_summary_crew.Task")
    @patch("agent_office.crews.stock_summary_crew.track_crew_run", return_value="ok")
    @patch("agent_office.crews.stock_summary_crew.build_email_agent")
    @patch("agent_office.crews.stock_summary_crew.build_stock_agent")
    @patch("agent_office.crews.stock_summary_crew.Crew")
    def test_job_type_is_classname(self, mock_crew_cls, mock_stock, mock_email, mock_tracker, mock_task):
        from agent_office.crews.stock_summary_crew import StockSummaryCrew
        StockSummaryCrew().run(tickers=["AAPL"], recipients=["a@x.com"])
        _, kwargs = mock_tracker.call_args
        assert kwargs.get("job_type") == "StockSummaryCrew"

    @patch("agent_office.crews.stock_summary_crew.Task")
    @patch("agent_office.crews.stock_summary_crew.track_crew_run", return_value="ok")
    @patch("agent_office.crews.stock_summary_crew.build_email_agent")
    @patch("agent_office.crews.stock_summary_crew.build_stock_agent")
    @patch("agent_office.crews.stock_summary_crew.Crew")
    def test_tickers_in_analyze_task_description(self, mock_crew_cls, mock_stock, mock_email, mock_tracker, mock_task):
        from agent_office.crews.stock_summary_crew import StockSummaryCrew
        StockSummaryCrew().run(tickers=["NVDA"], recipients=["a@x.com"])
        first_task_kwargs = mock_task.call_args_list[0][1]
        assert "NVDA" in first_task_kwargs["description"]
