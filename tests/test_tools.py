"""Unit tests for tools — run with: uv run pytest tests/"""
import os
from unittest.mock import MagicMock, patch

import pytest


# ── DocReaderTool ─────────────────────────────────────────────────────────────

class TestDocReaderTool:
    def setup_method(self):
        from agent_office.tools.doc_reader_tool import DocReaderTool
        self.tool = DocReaderTool()

    def test_read_txt_file(self, tmp_path):
        doc = tmp_path / "sample.txt"
        doc.write_text("Hello, world!")
        result = self.tool._run(source=str(doc))
        assert "Hello, world!" in result

    def test_unsupported_extension(self, tmp_path):
        doc = tmp_path / "file.xyz"
        doc.write_text("data")
        result = self.tool._run(source=str(doc))
        assert "Unsupported" in result

    def test_missing_file(self):
        result = self.tool._run(source="/nonexistent/file.txt")
        assert "not found" in result


# ── GmailSendTool ─────────────────────────────────────────────────────────────

class TestGmailSendTool:
    def setup_method(self):
        from agent_office.tools.gmail_tool import GmailSendTool
        self.tool = GmailSendTool()

    @patch("agent_office.tools.gmail_tool.smtplib.SMTP")
    def test_send_email_success(self, mock_smtp_cls, monkeypatch):
        monkeypatch.setenv("GMAIL_ADDRESS", "sender@gmail.com")
        monkeypatch.setenv("GMAIL_APP_PASSWORD", "test-app-password")

        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = self.tool._run(to="recipient@gmail.com", subject="Test", body="Hello")
        assert "sent successfully" in result
        assert "recipient@gmail.com" in result

    @patch("agent_office.tools.gmail_tool.smtplib.SMTP")
    def test_send_email_with_cc(self, mock_smtp_cls, monkeypatch):
        monkeypatch.setenv("GMAIL_ADDRESS", "sender@gmail.com")
        monkeypatch.setenv("GMAIL_APP_PASSWORD", "test-app-password")

        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = self.tool._run(to="a@gmail.com", subject="Test", body="Hi", cc="b@gmail.com")
        assert "sent successfully" in result
