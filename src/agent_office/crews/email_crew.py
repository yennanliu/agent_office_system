from crewai import Crew, Process, Task

from agent_office.agents.email_agent import build_email_agent


class EmailCrew:
    def run(self, to: str, subject: str, intent: str, attachments: list[str] | None = None) -> str:
        agent = build_email_agent()

        attachment_instruction = ""
        if attachments:
            paths = ", ".join(attachments)
            attachment_instruction = f"\nAttach the following local file(s): {paths}"

        task = Task(
            description=(
                f"Send an email to: {to}\n"
                f"Subject: {subject}\n"
                f"Intent / content guidance: {intent}\n"
                f"{attachment_instruction}\n"
                "Draft a professional email body matching the intent, then send it via Gmail."
            ),
            expected_output="Confirmation that the email was sent, including recipient, subject, and any attachments.",
            agent=agent,
        )
        result = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        ).kickoff()
        return str(result)
