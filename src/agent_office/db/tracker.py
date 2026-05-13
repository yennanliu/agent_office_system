import time

from crewai import Crew

from agent_office.db.database import RunStatus, insert_run, insert_step, update_run


def track_crew_run(name: str, job_type: str, agents: list[str], crew: Crew):
    run_id = insert_run(name, job_type, agents)

    step_state = {"index": 0, "t": time.monotonic()}

    def _on_task(task_output) -> None:
        elapsed = time.monotonic() - step_state["t"]
        step_state["t"] = time.monotonic()
        insert_step(
            run_id=run_id,
            step_index=step_state["index"],
            agent=getattr(task_output, "agent", "") or "",
            task_description=(getattr(task_output, "description", "") or "")[:200],
            output_preview=(getattr(task_output, "raw", "") or "")[:400],
            duration_s=elapsed,
        )
        step_state["index"] += 1

    crew.task_callback = _on_task

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
