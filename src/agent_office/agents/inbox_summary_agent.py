from crewai import Agent

from agent_office.agents.base import build_agent
from agent_office.tools.gmail_tool import GmailReadTool
from agent_office.tools.report_saver_tool import ReportSaverTool


def build_inbox_summary_agent() -> Agent:
    return build_agent(
        role="Inbox Summarizer",
        goal=(
            "Read recent Gmail messages, distil them into a concise structured summary, "
            "and save the report as a local text file"
        ),
        backstory=(
            "You are an executive assistant specialising in email triage. "
            "You cut through inbox noise to surface what matters, grouping emails by topic "
            "and clearly flagging any action items that need a follow-up."
        ),
        tools=[GmailReadTool(), ReportSaverTool()],
    )
