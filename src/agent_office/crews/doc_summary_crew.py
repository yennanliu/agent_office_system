from crewai import Crew, Process, Task

from agent_office.agents.doc_agent import build_doc_agent
from agent_office.agents.email_agent import build_email_agent


class DocSummaryCrew:
    def run(self, doc_path: str, recipients: list[str], additional_notes: str = "") -> str:
        doc_agent = build_doc_agent()
        email_agent = build_email_agent()
        recipient_str = ", ".join(recipients)

        summarize_task = Task(
            description=(
                f"Read the document at: {doc_path}\n"
                "Produce a structured summary with:\n"
                "  1. Executive Summary (2–3 sentences)\n"
                "  2. Key Points (bulleted list)\n"
                "  3. Action Items (if any)\n"
                f"Additional context: {additional_notes or 'None'}"
            ),
            expected_output="Structured document summary with executive summary, key points, and action items.",
            agent=doc_agent,
        )

        email_task = Task(
            description=(
                f"Send the document summary from the previous task via email to: {recipient_str}\n"
                "Use a clear subject line that references the document name.\n"
                "Format the email body with the full structured summary."
            ),
            expected_output=f"Confirmation that the summary email was sent to {recipient_str}.",
            agent=email_agent,
            context=[summarize_task],
        )

        result = Crew(
            agents=[doc_agent, email_agent],
            tasks=[summarize_task, email_task],
            process=Process.sequential,
            verbose=True,
        ).kickoff()
        return str(result)
