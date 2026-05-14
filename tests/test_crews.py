"""Tests for crew orchestration (crewai.Task + track_crew_run mocked — no LLM calls)."""
from unittest.mock import call, patch

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


# ── InboxSummaryCrew ──────────────────────────────────────────────────────────

class TestInboxSummaryCrew:
    @patch("agent_office.crews.inbox_summary_crew.Task")
    @patch("agent_office.crews.inbox_summary_crew.track_crew_run", return_value="inbox done")
    @patch("agent_office.crews.inbox_summary_crew.build_inbox_summary_agent")
    @patch("agent_office.crews.inbox_summary_crew.Crew")
    def test_run_returns_str(self, mock_crew_cls, mock_agent, mock_tracker, mock_task):
        from agent_office.crews.inbox_summary_crew import InboxSummaryCrew
        result = InboxSummaryCrew().run()
        assert result == "inbox done"

    @patch("agent_office.crews.inbox_summary_crew.Task")
    @patch("agent_office.crews.inbox_summary_crew.track_crew_run", return_value="ok")
    @patch("agent_office.crews.inbox_summary_crew.build_inbox_summary_agent")
    @patch("agent_office.crews.inbox_summary_crew.Crew")
    def test_job_type_is_classname(self, mock_crew_cls, mock_agent, mock_tracker, mock_task):
        from agent_office.crews.inbox_summary_crew import InboxSummaryCrew
        InboxSummaryCrew().run()
        _, kwargs = mock_tracker.call_args
        assert kwargs.get("job_type") == "InboxSummaryCrew"

    @patch("agent_office.crews.inbox_summary_crew.Task")
    @patch("agent_office.crews.inbox_summary_crew.track_crew_run", return_value="ok")
    @patch("agent_office.crews.inbox_summary_crew.build_inbox_summary_agent")
    @patch("agent_office.crews.inbox_summary_crew.Crew")
    def test_two_tasks_created_without_recipients(self, mock_crew_cls, mock_agent, mock_tracker, mock_task):
        from agent_office.crews.inbox_summary_crew import InboxSummaryCrew
        InboxSummaryCrew().run(recipients=None)
        assert mock_task.call_count == 2

    @patch("agent_office.crews.inbox_summary_crew.Task")
    @patch("agent_office.crews.inbox_summary_crew.track_crew_run", return_value="ok")
    @patch("agent_office.crews.inbox_summary_crew.build_email_agent")
    @patch("agent_office.crews.inbox_summary_crew.build_inbox_summary_agent")
    @patch("agent_office.crews.inbox_summary_crew.Crew")
    def test_three_tasks_created_with_recipients(self, mock_crew_cls, mock_summary, mock_email, mock_tracker, mock_task):
        from agent_office.crews.inbox_summary_crew import InboxSummaryCrew
        InboxSummaryCrew().run(recipients=["a@x.com"])
        assert mock_task.call_count == 3

    @patch("agent_office.crews.inbox_summary_crew.Task")
    @patch("agent_office.crews.inbox_summary_crew.track_crew_run", return_value="ok")
    @patch("agent_office.crews.inbox_summary_crew.build_email_agent")
    @patch("agent_office.crews.inbox_summary_crew.build_inbox_summary_agent")
    @patch("agent_office.crews.inbox_summary_crew.Crew")
    def test_email_agent_not_built_without_recipients(self, mock_crew_cls, mock_summary, mock_email, mock_tracker, mock_task):
        from agent_office.crews.inbox_summary_crew import InboxSummaryCrew
        InboxSummaryCrew().run(recipients=None)
        mock_email.assert_not_called()

    @patch("agent_office.crews.inbox_summary_crew.Task")
    @patch("agent_office.crews.inbox_summary_crew.track_crew_run", return_value="ok")
    @patch("agent_office.crews.inbox_summary_crew.build_inbox_summary_agent")
    @patch("agent_office.crews.inbox_summary_crew.Crew")
    def test_max_emails_in_read_task_description(self, mock_crew_cls, mock_agent, mock_tracker, mock_task):
        from agent_office.crews.inbox_summary_crew import InboxSummaryCrew
        InboxSummaryCrew().run(max_emails=20)
        first_task_kwargs = mock_task.call_args_list[0][1]
        assert "20" in first_task_kwargs["description"]

    @patch("agent_office.crews.inbox_summary_crew.Task")
    @patch("agent_office.crews.inbox_summary_crew.track_crew_run", return_value="ok")
    @patch("agent_office.crews.inbox_summary_crew.build_inbox_summary_agent")
    @patch("agent_office.crews.inbox_summary_crew.Crew")
    def test_output_dir_in_save_task_description(self, mock_crew_cls, mock_agent, mock_tracker, mock_task):
        from agent_office.crews.inbox_summary_crew import InboxSummaryCrew
        InboxSummaryCrew().run(output_dir="/custom/reports")
        save_task_kwargs = mock_task.call_args_list[1][1]
        assert "/custom/reports" in save_task_kwargs["description"]

    @patch("agent_office.crews.inbox_summary_crew.Task")
    @patch("agent_office.crews.inbox_summary_crew.track_crew_run", return_value="ok")
    @patch("agent_office.crews.inbox_summary_crew.build_email_agent")
    @patch("agent_office.crews.inbox_summary_crew.build_inbox_summary_agent")
    @patch("agent_office.crews.inbox_summary_crew.Crew")
    def test_recipient_in_send_task_description(self, mock_crew_cls, mock_summary, mock_email, mock_tracker, mock_task):
        from agent_office.crews.inbox_summary_crew import InboxSummaryCrew
        InboxSummaryCrew().run(recipients=["boss@x.com"])
        send_task_kwargs = mock_task.call_args_list[2][1]
        assert "boss@x.com" in send_task_kwargs["description"]

    @patch("agent_office.crews.inbox_summary_crew.Task")
    @patch("agent_office.crews.inbox_summary_crew.track_crew_run", return_value="ok")
    @patch("agent_office.crews.inbox_summary_crew.build_inbox_summary_agent")
    @patch("agent_office.crews.inbox_summary_crew.Crew")
    def test_default_output_dir_is_output(self, mock_crew_cls, mock_agent, mock_tracker, mock_task):
        from agent_office.crews.inbox_summary_crew import InboxSummaryCrew
        InboxSummaryCrew().run()
        save_task_kwargs = mock_task.call_args_list[1][1]
        assert "output" in save_task_kwargs["description"]
