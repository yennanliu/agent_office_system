from crewai import Crew

from agent_office.db.database import RunStatus, insert_run, update_run


def track_crew_run(name: str, job_type: str, agents: list[str], crew: Crew):
    run_id = insert_run(name, job_type, agents)
    try:
        result = crew.kickoff()
        metrics = crew.calculate_usage_metrics()
        update_run(
            run_id,
            status=RunStatus.SUCCESS,
            total_tokens=getattr(metrics, "total_tokens", 0),
            prompt_tokens=getattr(metrics, "prompt_tokens", 0),
            completion_tokens=getattr(metrics, "completion_tokens", 0),
        )
        return result
    except Exception as exc:
        update_run(run_id, status=RunStatus.FAILED, error=str(exc))
        raise
