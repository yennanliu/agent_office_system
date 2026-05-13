"""Tests for agent_office.utils"""

from agent_office.utils import parse_emails


class TestParseEmails:
    def test_single_address(self):
        assert parse_emails("a@example.com") == ["a@example.com"]

    def test_multiple_addresses(self):
        assert parse_emails("a@example.com, b@example.com") == ["a@example.com", "b@example.com"]

    def test_strips_whitespace(self):
        assert parse_emails("  a@example.com ,  b@example.com  ") == ["a@example.com", "b@example.com"]

    def test_drops_blank_segments(self):
        assert parse_emails("a@example.com,,b@example.com") == ["a@example.com", "b@example.com"]

    def test_empty_string(self):
        assert parse_emails("") == []

    def test_whitespace_only(self):
        assert parse_emails("   ,  ,  ") == []

    def test_no_spaces(self):
        assert parse_emails("a@x.com,b@x.com,c@x.com") == ["a@x.com", "b@x.com", "c@x.com"]
