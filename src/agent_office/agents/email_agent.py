from agent_office.agents.base import build_agent
from agent_office.tools.gmail_tool import GmailReadTool, GmailSendTool


def build_email_agent():
    return build_agent(
        role="Gmail Email Assistant",
        goal="Compose and send emails via Gmail accurately and professionally on behalf of the user",
        backstory=(
            "You are an email assistant with full access to the Gmail account. "
            "You draft clear, professional emails and handle all correspondence reliably."
        ),
        tools=[GmailSendTool(), GmailReadTool()],
    )
