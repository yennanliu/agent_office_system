"""Unit tests for tools — run with: uv run pytest tests/"""
import os
import tempfile
from pathlib import Path
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


# ── OutlookSendTool ───────────────────────────────────────────────────────────

class TestOutlookSendTool:
    def setup_method(self):
        from agent_office.tools.outlook_tool import OutlookSendTool
        self.tool = OutlookSendTool()

    @patch("agent_office.tools.outlook_tool._get_access_token", return_value="fake-token")
    @patch("agent_office.tools.outlook_tool.httpx.post")
    def test_send_email_success(self, mock_post, mock_token, monkeypatch):
        monkeypatch.setenv("OUTLOOK_USER_EMAIL", "sender@example.com")
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        result = self.tool._run(to="a@b.com", subject="Test", body="Hello")
        assert "sent successfully" in result
        assert "a@b.com" in result
