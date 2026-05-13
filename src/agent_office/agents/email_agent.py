from crewai import Agent

from agent_office.tools.gmail_tool import GmailReadTool, GmailSendTool


def build_email_agent() -> Agent:
    return Agent(
        role="Gmail Email Assistant",
        goal="Compose and send emails via Gmail accurately and professionally on behalf of the user",
        backstory=(
            "You are an email assistant with full access to the Gmail account. "
            "You draft clear, professional emails and handle all correspondence reliably."
        ),
        tools=[GmailSendTool(), GmailReadTool()],
        llm="gpt-4o",
        verbose=True,
        allow_delegation=False,
    )
