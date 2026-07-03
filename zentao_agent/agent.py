from __future__ import annotations

from google.adk.agents import LlmAgent

from zentao_agent.bug_agent import bug_agent
from zentao_agent.execution_agent import execution_agent
from zentao_agent.model import zentao_model
from zentao_agent.project_agent import project_agent
from zentao_agent.product_agent import product_agent
from zentao_agent.task_agent import task_agent


root_agent = LlmAgent(
    model=zentao_model(),
    name="root_agent",
    description="Routes Zentao assistant requests to specialist agents.",
    instruction=(
        "You are the Zentao assistant coordinator. Decide which specialist "
        "agent should handle the user request. Send project-related requests "
        "to project_agent, product-related requests to product_agent, "
        "execution or latest-iteration requests to execution_agent, and "
        "task-related requests to task_agent. Send bug-related requests to "
        "bug_agent, including listing bugs, viewing a bug, filtering by "
        "assignee, filtering by status, and checking bugs opened by a user. "
        "For bug requests without an execution ID, use project_agent first "
        "to identify involved projects, execution_agent second to select the "
        "latest execution, and bug_agent last to query bugs from that "
        "execution. For task requests without an execution ID, use "
        "project_agent first to identify involved projects, execution_agent "
        "second to select the execution, and task_agent last to handle the "
        "task workflow. "
        "Do not answer bug data questions from memory; delegate them to "
        "bug_agent. Do not answer task data questions from memory; delegate "
        "them to task_agent. If the request is outside the currently "
        "available specialists, explain the current limitation briefly."
    ),
    sub_agents=[project_agent, product_agent, execution_agent, task_agent, bug_agent],
)
