from crewai import Agent

from agent_office.agents.base import build_agent


def build_scheduler_agent() -> Agent:
    return build_agent(
        role="Task Scheduler",
        goal="Coordinate and trigger the correct crew for each scheduled job based on configuration",
        backstory=(
            "You are a dependable automation controller that ensures recurring tasks run on time, "
            "logs their outcomes, and escalates failures appropriately."
        ),
        allow_delegation=True,
    )
