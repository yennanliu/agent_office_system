from crewai import Agent

from agent_office.tools.doc_reader_tool import DocReaderTool
from agent_office.tools.outlook_tool import OutlookSendTool


def build_doc_agent() -> Agent:
    return Agent(
        role="Document Analyst",
        goal=(
            "Read documents thoroughly, extract key information, and produce structured summaries "
            "with an executive summary, key points, and action items"
        ),
        backstory=(
            "You are a meticulous analyst who specializes in distilling long documents into "
            "clear, actionable insights. You never miss important details."
        ),
        tools=[DocReaderTool(), OutlookSendTool()],
        llm="gpt-4o",
        verbose=True,
        allow_delegation=False,
    )
