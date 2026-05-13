import logging
from pathlib import Path
from typing import Callable

import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler()


def load_schedule(config_path: str) -> list[dict]:
    with open(config_path) as f:
        data = yaml.safe_load(f)
    return data.get("jobs", [])


def register_job(job: dict, runner: Callable[[str, dict], None]) -> None:
    parts = job["cron"].split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression for job '{job['id']}': {job['cron']!r}")

    trigger = CronTrigger(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        day_of_week=parts[4],
    )
    _scheduler.add_job(
        func=runner,
        trigger=trigger,
        id=job["id"],
        args=[job["crew"], job.get("params", {})],
        coalesce=True,
        max_instances=1,
        replace_existing=True,
    )
    logger.info("Registered job '%s' (%s) — cron: %s", job["id"], job["crew"], job["cron"])


def start_scheduler() -> None:
    if not _scheduler.running:
        _scheduler.start()
        logger.info("APScheduler started")


def stop_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
