from crewai import Crew, Process, Task

from agent_office.agents.email_agent import build_email_agent
from agent_office.db.tracker import track_crew_run


class EmailCrew:
    def run(self, to: str, subject: str, intent: str, attachments: list[str] | None = None) -> str:
        agent = build_email_agent()

        desc_lines = [
            f"Send an email to: {to}",
            f"Subject: {subject}",
            f"Intent / content guidance: {intent}",
        ]
        if attachments:
            desc_lines.append(f"Attach the following local file(s): {', '.join(attachments)}")
        desc_lines.append("Draft a professional email body matching the intent, then send it via Gmail.")

        task = Task(
            description="\n".join(desc_lines),
            expected_output="Confirmation that the email was sent, including recipient, subject, and any attachments.",
            agent=agent,
        )
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )
        return str(track_crew_run(
            name=f"Email to {to} — {subject}",
            job_type=type(self).__name__,
            agents=[agent.role],
            crew=crew,
        ))
