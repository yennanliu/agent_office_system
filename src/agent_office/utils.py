def parse_emails(s: str) -> list[str]:
    """Split a comma-separated email string into a stripped list, dropping blanks."""
    return [r.strip() for r in s.split(",") if r.strip()]
