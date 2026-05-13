import os
from typing import Optional

import httpx
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


def _get_access_token() -> str:
    tenant_id = os.environ["OUTLOOK_TENANT_ID"]
    resp = httpx.post(
        f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
        data={
            "client_id": os.environ["OUTLOOK_CLIENT_ID"],
            "client_secret": os.environ["OUTLOOK_CLIENT_SECRET"],
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _graph_headers() -> dict:
    return {"Authorization": f"Bearer {_get_access_token()}", "Content-Type": "application/json"}


# ── Send Email ────────────────────────────────────────────────────────────────

class SendEmailInput(BaseModel):
    to: str = Field(description="Recipient email address(es), comma-separated")
    subject: str = Field(description="Email subject line")
    body: str = Field(description="HTML or plain-text email body")
    cc: Optional[str] = Field(default=None, description="CC recipients, comma-separated")


class OutlookSendTool(BaseTool):
    name: str = "outlook_send_email"
    description: str = (
        "Send an email via Outlook using Microsoft Graph API. "
        "Provide recipient(s), subject, and body."
    )
    args_schema: type[BaseModel] = SendEmailInput

    def _run(self, to: str, subject: str, body: str, cc: Optional[str] = None) -> str:
        user_email = os.environ["OUTLOOK_USER_EMAIL"]

        def _addr_list(raw: str) -> list[dict]:
            return [{"emailAddress": {"address": a.strip()}} for a in raw.split(",")]

        message: dict = {
            "subject": subject,
            "body": {"contentType": "HTML", "content": body},
            "toRecipients": _addr_list(to),
        }
        if cc:
            message["ccRecipients"] = _addr_list(cc)

        resp = httpx.post(
            f"https://graph.microsoft.com/v1.0/users/{user_email}/sendMail",
            headers=_graph_headers(),
            json={"message": message, "saveToSentItems": True},
        )
        resp.raise_for_status()
        return f"Email sent successfully to {to} (subject: {subject!r})"


# ── Read Inbox ────────────────────────────────────────────────────────────────

class ReadInboxInput(BaseModel):
    max_results: int = Field(default=10, description="Maximum number of emails to retrieve")
    unread_only: bool = Field(default=False, description="When True, only retrieve unread emails")


class OutlookReadTool(BaseTool):
    name: str = "outlook_read_inbox"
    description: str = (
        "Read emails from the Outlook inbox via Microsoft Graph API. "
        "Returns subject, sender, date, and a body preview for each message."
    )
    args_schema: type[BaseModel] = ReadInboxInput

    def _run(self, max_results: int = 10, unread_only: bool = False) -> str:
        user_email = os.environ["OUTLOOK_USER_EMAIL"]
        params: dict = {
            "$top": max_results,
            "$select": "subject,from,receivedDateTime,bodyPreview,isRead",
            "$orderby": "receivedDateTime desc",
        }
        if unread_only:
            params["$filter"] = "isRead eq false"

        resp = httpx.get(
            f"https://graph.microsoft.com/v1.0/users/{user_email}/messages",
            headers=_graph_headers(),
            params=params,
        )
        resp.raise_for_status()

        messages = resp.json().get("value", [])
        if not messages:
            return "Inbox is empty or no messages matched the filter."

        lines = []
        for msg in messages:
            lines.append(
                f"From: {msg['from']['emailAddress']['address']}\n"
                f"Subject: {msg['subject']}\n"
                f"Date: {msg['receivedDateTime']}\n"
                f"Read: {msg['isRead']}\n"
                f"Preview: {msg['bodyPreview']}\n"
                "---"
            )
        return "\n".join(lines)
