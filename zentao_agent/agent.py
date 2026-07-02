from __future__ import annotations

from google.adk.agents import LlmAgent

from zentao_agent.bug_agent import bug_agent
from zentao_agent.model import zentao_model


root_agent = LlmAgent(
    model=zentao_model(),
    name="root_agent",
    description="Routes Zentao assistant requests to specialist agents.",
    instruction=(
        "You are the Zentao assistant coordinator. Decide which specialist "
        "agent should handle the user request. Send bug-related requests to "
        "bug_agent, including listing bugs, viewing a bug, filtering by "
        "assignee, filtering by status, and checking bugs opened by a user. "
        "Do not answer bug data questions from memory; delegate them to "
        "bug_agent. If the request is outside the currently available "
        "specialists, explain the current limitation briefly."
    ),
    sub_agents=[bug_agent],
)
