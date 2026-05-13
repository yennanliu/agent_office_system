"""Unit tests for tools — run with: uv run pytest tests/"""
from unittest.mock import MagicMock, patch

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

    def test_read_md_file(self, tmp_path):
        doc = tmp_path / "notes.md"
        doc.write_text("# Title\nSome content")
        result = self.tool._run(source=str(doc))
        assert "# Title" in result

    def test_read_csv_file(self, tmp_path):
        doc = tmp_path / "data.csv"
        doc.write_text("col1,col2\nval1,val2")
        result = self.tool._run(source=str(doc))
        assert "col1" in result

    def test_unsupported_extension(self, tmp_path):
        doc = tmp_path / "file.xyz"
        doc.write_text("data")
        result = self.tool._run(source=str(doc))
        assert "Unsupported" in result

    def test_missing_file(self):
        result = self.tool._run(source="/nonexistent/file.txt")
        assert "not found" in result

    @patch("agent_office.tools.doc_reader_tool.httpx.get")
    def test_url_text_type_returns_directly(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = "plain text content"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = self.tool._run(source="https://example.com/notes.txt")
        assert result == "plain text content"
        mock_get.assert_called_once()

    @patch("agent_office.tools.doc_reader_tool.httpx.get")
    def test_url_md_type_returns_directly(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.text = "# Markdown"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = self.tool._run(source="https://example.com/readme.md")
        assert result == "# Markdown"


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

    @patch("agent_office.tools.gmail_tool.smtplib.SMTP")
    def test_send_email_with_attachment(self, mock_smtp_cls, monkeypatch, tmp_path):
        monkeypatch.setenv("GMAIL_ADDRESS", "sender@gmail.com")
        monkeypatch.setenv("GMAIL_APP_PASSWORD", "test-app-password")

        att = tmp_path / "report.txt"
        att.write_text("report content")

        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = self.tool._run(to="r@gmail.com", subject="S", body="B",
                                attachments=str(att))
        assert "sent successfully" in result
        assert "report.txt" in result

    def test_missing_attachment_returns_error(self, monkeypatch):
        monkeypatch.setenv("GMAIL_ADDRESS", "sender@gmail.com")
        monkeypatch.setenv("GMAIL_APP_PASSWORD", "test-app-password")

        result = self.tool._run(to="r@gmail.com", subject="S", body="B",
                                attachments="/nonexistent/file.pdf")
        assert "Error" in result
        assert "not found" in result

    @patch("agent_office.tools.gmail_tool.smtplib.SMTP")
    def test_recipients_include_cc_in_sendmail(self, mock_smtp_cls, monkeypatch):
        monkeypatch.setenv("GMAIL_ADDRESS", "sender@gmail.com")
        monkeypatch.setenv("GMAIL_APP_PASSWORD", "pw")

        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)

        self.tool._run(to="to@x.com", subject="S", body="B", cc="cc@x.com")
        _, kwargs = mock_server.sendmail.call_args or (None, {})
        call_args = mock_server.sendmail.call_args
        recipients = call_args[0][1]  # positional arg 2
        assert "cc@x.com" in recipients


# ── GmailReadTool ─────────────────────────────────────────────────────────────

class TestGmailReadTool:
    def setup_method(self):
        from agent_office.tools.gmail_tool import GmailReadTool
        self.tool = GmailReadTool()

    @patch("agent_office.tools.gmail_tool.imaplib.IMAP4_SSL")
    def test_empty_inbox(self, mock_imap_cls, monkeypatch):
        monkeypatch.setenv("GMAIL_ADDRESS", "user@gmail.com")
        monkeypatch.setenv("GMAIL_APP_PASSWORD", "pw")

        mock_mail = MagicMock()
        mock_imap_cls.return_value.__enter__ = MagicMock(return_value=mock_mail)
        mock_imap_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_mail.search.return_value = (None, [b""])

        result = self.tool._run(max_results=5)
        assert "No emails found" in result

    @patch("agent_office.tools.gmail_tool.imaplib.IMAP4_SSL")
    def test_reads_one_email(self, mock_imap_cls, monkeypatch):
        monkeypatch.setenv("GMAIL_ADDRESS", "user@gmail.com")
        monkeypatch.setenv("GMAIL_APP_PASSWORD", "pw")

        mock_mail = MagicMock()
        mock_imap_cls.return_value.__enter__ = MagicMock(return_value=mock_mail)
        mock_imap_cls.return_value.__exit__ = MagicMock(return_value=False)

        mock_mail.search.return_value = (None, [b"1"])
        raw_header = b"From: alice@example.com\r\nSubject: Hello\r\nDate: Mon, 1 Jan 2024\r\n"
        mock_mail.fetch.side_effect = [
            (None, [(None, raw_header)]),
            (None, [(None, b"Preview text here")]),
        ]

        result = self.tool._run(max_results=5)
        assert "alice@example.com" in result
        assert "Hello" in result


# ── StockDataTool helpers ─────────────────────────────────────────────────────

class TestStockFormatHelpers:
    def test_pct_value(self):
        from agent_office.tools.stock_tool import _pct
        assert _pct(0.15) == "15.0%"
        assert _pct(None) == "N/A"
        assert _pct(0.0) == "0.0%"

    def test_usd_value(self):
        from agent_office.tools.stock_tool import _usd
        assert _usd(1234.5) == "$1,234.50"
        assert _usd(None) == "N/A"

    def test_fmt_value(self):
        from agent_office.tools.stock_tool import _fmt
        assert _fmt(3.14159) == "3.14"
        assert _fmt(None) == "N/A"

    def test_market_cap_trillion(self):
        from agent_office.tools.stock_tool import _market_cap
        assert _market_cap(3e12) == "$3.00T"

    def test_market_cap_billion(self):
        from agent_office.tools.stock_tool import _market_cap
        assert _market_cap(500e9) == "$500.00B"

    def test_market_cap_million(self):
        from agent_office.tools.stock_tool import _market_cap
        assert _market_cap(250e6) == "$250M"

    def test_market_cap_none(self):
        from agent_office.tools.stock_tool import _market_cap
        assert _market_cap(None) == "N/A"

    def test_market_cap_zero(self):
        from agent_office.tools.stock_tool import _market_cap
        assert _market_cap(0) == "N/A"


class TestStockDataTool:
    def setup_method(self):
        from agent_office.tools.stock_tool import StockDataTool
        self.tool = StockDataTool()

    @patch("agent_office.tools.stock_tool.yf.Ticker")
    def test_valid_ticker_returns_report(self, mock_ticker_cls):
        import pandas as pd

        mock_ticker = MagicMock()
        mock_ticker_cls.return_value = mock_ticker
        mock_ticker.info = {
            "currentPrice": 150.0,
            "longName": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "marketCap": 2.5e12,
            "trailingPE": 28.5,
            "forwardPE": 25.0,
            "revenueGrowth": 0.08,
            "grossMargins": 0.44,
            "profitMargins": 0.25,
            "recommendationKey": "buy",
            "targetMeanPrice": 200.0,
            "numberOfAnalystOpinions": 40,
            "dividendYield": 0.005,
            "beta": 1.2,
        }
        mock_ticker.history.return_value = pd.DataFrame(
            {"Close": [140.0, 155.0]},
            index=pd.date_range("2024-01-01", periods=2),
        )

        result = self.tool._run(ticker="AAPL")
        assert "AAPL" in result
        assert "Apple Inc." in result
        assert "BUY" in result
        assert "$2.50T" in result

    @patch("agent_office.tools.stock_tool.yf.Ticker")
    def test_invalid_ticker_returns_error(self, mock_ticker_cls):
        mock_ticker = MagicMock()
        mock_ticker_cls.return_value = mock_ticker
        mock_ticker.info = {}  # no price fields

        result = self.tool._run(ticker="XXXXXX")
        assert "Could not fetch" in result

    @patch("agent_office.tools.stock_tool.yf.Ticker")
    def test_ticker_uppercased(self, mock_ticker_cls):
        import pandas as pd

        mock_ticker = MagicMock()
        mock_ticker_cls.return_value = mock_ticker
        mock_ticker.info = {"currentPrice": 100.0, "longName": "Test Co"}
        mock_ticker.history.return_value = pd.DataFrame({"Close": [90.0, 100.0]},
                                                         index=pd.date_range("2024-01-01", periods=2))

        self.tool._run(ticker="aapl")
        call_arg = mock_ticker_cls.call_args[0][0]
        assert call_arg == "AAPL"
