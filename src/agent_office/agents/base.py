from crewai import Agent


def build_agent(
    role: str,
    goal: str,
    backstory: str,
    tools: list | None = None,
    allow_delegation: bool = False,
) -> Agent:
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        tools=tools or [],
        llm="gpt-4o",
        verbose=True,
        allow_delegation=allow_delegation,
    )
