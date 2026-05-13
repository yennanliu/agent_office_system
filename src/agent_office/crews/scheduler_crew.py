import logging
from pathlib import Path

from agent_office.tools.cron_tool import (
    load_schedule,
    register_job,
    start_scheduler,
    stop_scheduler,
)

logger = logging.getLogger(__name__)


def _run_crew(crew_name: str, params: dict) -> None:
    logger.info("Running scheduled crew '%s' with params: %s", crew_name, params)
    try:
        if crew_name == "EmailCrew":
            from agent_office.crews.email_crew import EmailCrew
            EmailCrew().run(
                to=params.get("to", ""),
                subject=params.get("subject", "Scheduled Task"),
                intent=params.get("task", ""),
            )
        elif crew_name == "DocSummaryCrew":
            from agent_office.crews.doc_summary_crew import DocSummaryCrew
            DocSummaryCrew().run(
                doc_path=params.get("doc_path", ""),
                recipients=params.get("recipients", []),
                additional_notes=params.get("notes", ""),
            )
        elif crew_name == "StockSummaryCrew":
            from agent_office.crews.stock_summary_crew import StockSummaryCrew
            StockSummaryCrew().run(
                tickers=params.get("tickers", []),
                recipients=params.get("recipients", []),
            )
        else:
            raise ValueError(f"Unknown crew: {crew_name!r}")
    except Exception:
        logger.exception("Scheduled crew '%s' failed", crew_name)


class SchedulerCrew:
    def __init__(self, schedule_config_path: str | None = None):
        if schedule_config_path is None:
            schedule_config_path = str(
                Path(__file__).parent.parent / "config" / "schedule.yaml"
            )
        self.config_path = schedule_config_path

    def start(self) -> None:
        jobs = load_schedule(self.config_path)
        for job in jobs:
            register_job(job, _run_crew)
        start_scheduler()
        logger.info("SchedulerCrew started with %d job(s)", len(jobs))

    def stop(self) -> None:
        stop_scheduler()
