from datetime import date

from crewai import Crew, Process, Task

from agent_office.agents.email_agent import build_email_agent
from agent_office.agents.inbox_summary_agent import build_inbox_summary_agent
from agent_office.db.tracker import track_crew_run


class InboxSummaryCrew:
    def run(
        self,
        recipients: list[str] | None = None,
        output_dir: str = "output",
        max_emails: int = 10,
    ) -> str:
        summary_agent = build_inbox_summary_agent()

        read_task = Task(
            description=(
                f"Use gmail_read_inbox to fetch the {max_emails} most recent emails from the inbox "
                f"(set max_results={max_emails}, unread_only=False).\n"
                "Then produce a structured plain-text summary report containing:\n"
                "  1. Overview — total emails read, date range covered, top senders\n"
                "  2. By-Topic Groups — cluster emails into themes "
                "(e.g. Finance, HR, Engineering, Admin, Newsletters)\n"
                "  3. Action Items — emails that need a reply or follow-up, "
                "with sender, subject, and a one-line note on what is needed\n"
                "  4. FYI Only — informational emails requiring no action\n"
                "Write the full report as plain text, ready to be saved and shared."
            ),
            expected_output="A complete structured plain-text inbox summary report.",
            agent=summary_agent,
        )

        save_task = Task(
            description=(
                "Save the inbox summary report produced in the previous task to a local .txt file "
                "using the save_report tool.\n"
                + (f"Output directory: {output_dir}\n" if output_dir else "")
                + "Use a descriptive timestamped filename such as 'inbox_summary_YYYYMMDD_HHMMSS'."
            ),
            expected_output="Confirmation message with the absolute file path of the saved report.",
            agent=summary_agent,
            context=[read_task],
        )

        tasks = [read_task, save_task]
        agents = [summary_agent]

        if recipients:
            email_agent = build_email_agent()
            recipient_str = ", ".join(recipients)
            today = date.today().strftime("%Y-%m-%d")
            send_task = Task(
                description=(
                    f"Send the inbox summary report from the read_task to: {recipient_str}\n"
                    f"Subject: Inbox Summary Report — {today}\n"
                    "Use the full structured summary as the email body. "
                    "Keep the formatting clean and readable."
                ),
                expected_output=f"Confirmation that the summary email was sent to {recipient_str}.",
                agent=email_agent,
                context=[read_task],
            )
            tasks.append(send_task)
            agents.append(email_agent)

        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )
        return str(track_crew_run(
            name="Inbox summary",
            job_type=type(self).__name__,
            agents=[a.role for a in agents],
            crew=crew,
        ))
