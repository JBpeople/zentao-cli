from __future__ import annotations

from google.adk.agents import LlmAgent

from zentao_agent.bug_agent import bug_agent
from zentao_agent.execution_agent import execution_agent
from zentao_agent.model import zentao_model
from zentao_agent.product_agent import product_agent


root_agent = LlmAgent(
    model=zentao_model(),
    name="root_agent",
    description="Routes Zentao assistant requests to specialist agents.",
    instruction=(
        "You are the Zentao assistant coordinator. Decide which specialist "
        "agent should handle the user request. Send product-related requests "
        "to product_agent, execution or latest-iteration requests to "
        "execution_agent, and bug-related requests to bug_agent, including "
        "listing bugs, viewing a bug, filtering by assignee, filtering by "
        "status, and checking bugs opened by a user. "
        "Do not answer bug data questions from memory; delegate them to "
        "bug_agent. If the request is outside the currently available "
        "specialists, explain the current limitation briefly."
    ),
    sub_agents=[product_agent, execution_agent, bug_agent],
)
