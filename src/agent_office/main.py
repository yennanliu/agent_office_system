import argparse
import logging
import signal
import sys
import time

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def cmd_email(args: argparse.Namespace) -> None:
    from agent_office.crews.email_crew import EmailCrew
    result = EmailCrew().run(to=args.to, subject=args.subject, intent=args.intent)
    print(result)


def cmd_summarize(args: argparse.Namespace) -> None:
    from agent_office.crews.doc_summary_crew import DocSummaryCrew
    recipients = [r.strip() for r in args.to.split(",")]
    result = DocSummaryCrew().run(
        doc_path=args.doc,
        recipients=recipients,
        additional_notes=args.notes or "",
    )
    print(result)


def cmd_scheduler(args: argparse.Namespace) -> None:
    from agent_office.crews.scheduler_crew import SchedulerCrew
    scheduler = SchedulerCrew(schedule_config_path=args.config)
    scheduler.start()

    def _shutdown(sig, frame):
        logger.info("Shutting down scheduler...")
        scheduler.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info("Scheduler running — press Ctrl+C to stop.")
    while True:
        time.sleep(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agent-office",
        description="Multi-agent office automation system (CrewAI + OpenAI + Outlook)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- email ---
    ep = sub.add_parser("email", help="Draft and send an Outlook email")
    ep.add_argument("--to", required=True, help="Recipient email(s), comma-separated")
    ep.add_argument("--subject", required=True, help="Email subject")
    ep.add_argument("--intent", required=True, help="Natural language description of what to write")
    ep.set_defaults(func=cmd_email)

    # --- summarize ---
    sp = sub.add_parser("summarize", help="Summarize a document and email the result")
    sp.add_argument("--doc", required=True, help="Local path or URL to the document")
    sp.add_argument("--to", required=True, help="Recipient email(s), comma-separated")
    sp.add_argument("--notes", default="", help="Additional context or instructions for the summary")
    sp.set_defaults(func=cmd_summarize)

    # --- scheduler ---
    sched = sub.add_parser("scheduler", help="Start the background cron scheduler")
    sched.add_argument(
        "--config",
        default=None,
        help="Path to schedule.yaml (default: src/agent_office/config/schedule.yaml)",
    )
    sched.set_defaults(func=cmd_scheduler)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
