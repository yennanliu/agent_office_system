from crewai import Crew, Process, Task

from agent_office.agents.email_agent import build_email_agent


class EmailCrew:
    def run(self, to: str, subject: str, intent: str) -> str:
        agent = build_email_agent()
        task = Task(
            description=(
                f"Send an email to: {to}\n"
                f"Subject: {subject}\n"
                f"Intent / content guidance: {intent}\n\n"
                "Draft a professional email body matching the intent, then send it via Outlook."
            ),
            expected_output="Confirmation that the email was sent, including recipient and subject.",
            agent=agent,
        )
        result = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        ).kickoff()
        return str(result)
