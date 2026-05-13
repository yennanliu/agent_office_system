from crewai import Agent

from agent_office.tools.outlook_tool import OutlookReadTool, OutlookSendTool


def build_email_agent() -> Agent:
    return Agent(
        role="Outlook Email Assistant",
        goal="Compose and send emails via Outlook accurately and professionally on behalf of the user",
        backstory=(
            "You are a corporate email assistant with full access to the Outlook mailbox. "
            "You draft clear, professional emails and handle all correspondence reliably."
        ),
        tools=[OutlookSendTool(), OutlookReadTool()],
        llm="gpt-4o",
        verbose=True,
        allow_delegation=False,
    )
