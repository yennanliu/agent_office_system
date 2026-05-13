import imaplib
import mimetypes
import os
import smtplib
from email import encoders, message_from_bytes
from email.header import decode_header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

_SMTP_HOST = "smtp.gmail.com"
_SMTP_PORT = 587
_IMAP_HOST = "imap.gmail.com"
_IMAP_PORT = 993


def _credentials() -> tuple[str, str]:
    return os.environ["GMAIL_ADDRESS"], os.environ["GMAIL_APP_PASSWORD"]


# ── Send Email ────────────────────────────────────────────────────────────────

class SendEmailInput(BaseModel):
    to: str = Field(description="Recipient email address(es), comma-separated")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="HTML or plain-text email body")
    cc: Optional[str] = Field(default=None, description="CC recipients, comma-separated")
    attachments: Optional[str] = Field(
        default=None,
        description="Local file path(s) to attach, comma-separated. Leave empty to send without attachments.",
    )


class GmailSendTool(BaseTool):
    name: str = "gmail_send_email"
    description: str = (
        "Send an email via Gmail SMTP. "
        "Provide recipient(s), subject, body, and optionally local file paths to attach."
    )
    args_schema: type[BaseModel] = SendEmailInput

    def _run(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        attachments: Optional[str] = None,
    ) -> str:
        gmail_address, app_password = _credentials()

        # Use "mixed" when there are attachments, "alternative" for body-only
        msg = MIMEMultipart("mixed" if attachments else "alternative")
        msg["From"] = gmail_address
        msg["To"] = to
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = cc
        msg.attach(MIMEText(body, "html"))

        attached_names = []
        if attachments:
            for raw_path in attachments.split(","):
                path = Path(raw_path.strip())
                if not path.exists():
                    return f"Error: attachment not found — {path}"
                mime_type, _ = mimetypes.guess_type(str(path))
                main_type, sub_type = (mime_type or "application/octet-stream").split("/", 1)
                part = MIMEBase(main_type, sub_type)
                part.set_payload(path.read_bytes())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", "attachment", filename=path.name)
                msg.attach(part)
                attached_names.append(path.name)

        recipients = [r.strip() for r in to.split(",")]
        if cc:
            recipients += [r.strip() for r in cc.split(",")]

        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(gmail_address, app_password)
            server.sendmail(gmail_address, recipients, msg.as_string())

        suffix = f" with attachment(s): {', '.join(attached_names)}" if attached_names else ""
        return f"Email sent successfully to {to} (subject: {subject!r}){suffix}"


# ── Read Inbox ────────────────────────────────────────────────────────────────

class ReadInboxInput(BaseModel):
    max_results: int = Field(default=10, description="Maximum number of emails to retrieve")
    unread_only: bool = Field(default=False, description="When True, only retrieve unread emails")


class GmailReadTool(BaseTool):
    name: str = "gmail_read_inbox"
    description: str = (
        "Read emails from the Gmail inbox via IMAP. "
        "Returns subject, sender, date, and a short preview for each message."
    )
    args_schema: type[BaseModel] = ReadInboxInput

    def _run(self, max_results: int = 10, unread_only: bool = False) -> str:
        gmail_address, app_password = _credentials()

        with imaplib.IMAP4_SSL(_IMAP_HOST, _IMAP_PORT) as mail:
            mail.login(gmail_address, app_password)
            mail.select("INBOX")

            criterion = "UNSEEN" if unread_only else "ALL"
            _, data = mail.search(None, criterion)
            ids = data[0].split()

            if not ids:
                return "No emails found."

            selected_ids = ids[-max_results:]
            lines = []
            for uid in reversed(selected_ids):
                _, raw = mail.fetch(uid, "(RFC822)")
                msg = message_from_bytes(raw[0][1])

                subject_parts = decode_header(msg["Subject"] or "")
                subject = "".join(
                    part.decode(enc or "utf-8") if isinstance(part, bytes) else part
                    for part, enc in subject_parts
                )

                body_preview = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body_preview = (part.get_payload(decode=True) or b"").decode(
                                "utf-8", errors="replace"
                            )[:200]
                            break
                else:
                    body_preview = (msg.get_payload(decode=True) or b"").decode(
                        "utf-8", errors="replace"
                    )[:200]

                lines.append(
                    f"From: {msg['From']}\n"
                    f"Subject: {subject}\n"
                    f"Date: {msg['Date']}\n"
                    f"Preview: {body_preview.strip()}\n"
                    "---"
                )

        return "\n".join(lines)
