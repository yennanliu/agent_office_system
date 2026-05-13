from crewai import Agent


def build_scheduler_agent() -> Agent:
    return Agent(
        role="Task Scheduler",
        goal="Coordinate and trigger the correct crew for each scheduled job based on configuration",
        backstory=(
            "You are a dependable automation controller that ensures recurring tasks run on time, "
            "logs their outcomes, and escalates failures appropriately."
        ),
        tools=[],
        llm="gpt-4o",
        verbose=True,
        allow_delegation=True,
    )
