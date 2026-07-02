from __future__ import annotations

from dataclasses import asdict
from typing import Any

from google.adk.agents import LlmAgent

from zentao_agent.model import zentao_model
from zentao_cli.auth import client_from_profile
from zentao_cli.errors import ZentaoCliError
from zentao_cli.models import Execution, Project


def _execution_payload(execution: Execution) -> dict[str, Any]:
    return asdict(execution)


def _project_payload(project: Project) -> dict[str, Any]:
    return asdict(project)


def _matches_project_name(project: Project, project_name: str | None) -> bool:
    if not project_name:
        return True
    return project_name.lower() in project.name.lower()


def _latest_execution(executions: list[Execution]) -> Execution | None:
    if not executions:
        return None
    return max(executions, key=lambda execution: (execution.begin or "", execution.id))


def list_project_executions(project_id: int, latest_only: bool = False) -> dict[str, Any]:
    """List executions under one Zentao project, optionally returning only the latest one."""
    try:
        client = client_from_profile()
        executions = client.list_executions(project=project_id, fetch_all=True)
    except ZentaoCliError as exc:
        return {"error": str(exc)}

    if latest_only:
        latest = _latest_execution(executions)
        executions = [] if latest is None else [latest]
    return {"executions": [_execution_payload(execution) for execution in executions]}


def get_execution(execution_id: int) -> dict[str, Any]:
    """Get one Zentao execution by id."""
    try:
        client = client_from_profile()
        execution = client.get_execution(execution_id)
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"execution": _execution_payload(execution)}


def find_latest_involved_execution(project_name: str | None = None) -> dict[str, Any]:
    """Find the latest execution from projects involving the current user."""
    try:
        client = client_from_profile()
        projects = [
            project
            for project in client.list_projects(involved=True, fetch_all=True)
            if _matches_project_name(project, project_name)
        ]
        if not projects:
            return {"error": "No involved projects found."}

        scoped_executions: list[tuple[Project, Execution]] = []
        for project in projects:
            executions = client.list_executions(project=project.id, fetch_all=True)
            scoped_executions.extend((project, execution) for execution in executions)
    except ZentaoCliError as exc:
        return {"error": str(exc)}

    if not scoped_executions:
        return {"error": "No executions found for involved projects."}
    project, execution = max(scoped_executions, key=lambda item: (item[1].begin or "", item[1].id))
    return {"project": _project_payload(project), "execution": _execution_payload(execution)}


execution_agent = LlmAgent(
    model=zentao_model(),
    name="execution_agent",
    description="Handles read-only Zentao execution discovery workflows.",
    instruction=(
        "You are the Zentao execution specialist. Handle read-only execution "
        "queries: list executions for a project, inspect one execution, and "
        "find the latest execution from the current user's involved projects. "
        "Use the provided tools for execution data. If the user asks for bugs, "
        "return the execution context and let the bug specialist handle bug data."
    ),
    tools=[list_project_executions, get_execution, find_latest_involved_execution],
)
