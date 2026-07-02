from __future__ import annotations

from dataclasses import asdict
from typing import Any

from google.adk.agents import LlmAgent

from zentao_agent.model import zentao_model
from zentao_cli.auth import client_from_profile, current_username
from zentao_cli.errors import ZentaoCliError
from zentao_cli.models import Bug, Execution, Project


def _bug_payload(bug: Bug) -> dict[str, Any]:
    return asdict(bug)


def _project_payload(project: Project) -> dict[str, Any]:
    return asdict(project)


def _execution_payload(execution: Execution) -> dict[str, Any]:
    return asdict(execution)


def _resolve_me(value: str | None) -> str | None:
    if value is not None and value.lower() == "me":
        return current_username()
    return value


def _matches_project_name(project: Project, project_name: str | None) -> bool:
    if not project_name:
        return True
    return project_name.lower() in project.name.lower()


def _latest_execution(items: list[tuple[Project, Execution]]) -> tuple[Project, Execution] | None:
    if not items:
        return None
    return max(items, key=lambda item: (item[1].begin or "", item[1].id))


def list_bugs(
    execution: int,
    assigned_to: str | None = None,
    opened_by: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 100,
    fetch_all: bool = False,
) -> dict[str, Any]:
    """List bugs in a Zentao execution using optional filters."""
    try:
        client = client_from_profile()
        bugs = client.list_bugs(
            execution=execution,
            assigned_to=_resolve_me(assigned_to),
            opened_by=_resolve_me(opened_by),
            status=status,
            page=page,
            page_size=page_size,
            fetch_all=fetch_all,
        )
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"bugs": [_bug_payload(bug) for bug in bugs]}


def get_bug(bug_id: int) -> dict[str, Any]:
    """Get one Zentao bug by id."""
    try:
        client = client_from_profile()
        bug = client.get_bug(bug_id)
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"bug": _bug_payload(bug)}


def list_involved_projects(project_name: str | None = None) -> dict[str, Any]:
    """List projects involving the current Zentao user, optionally filtered by name."""
    try:
        client = client_from_profile()
        projects = [
            project
            for project in client.list_projects(involved=True, fetch_all=True)
            if _matches_project_name(project, project_name)
        ]
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"projects": [_project_payload(project) for project in projects]}


def list_project_executions(project_id: int, latest_only: bool = False) -> dict[str, Any]:
    """List executions under one Zentao project, optionally returning only the latest one."""
    try:
        client = client_from_profile()
        executions = client.list_executions(project=project_id, fetch_all=True)
    except ZentaoCliError as exc:
        return {"error": str(exc)}

    if latest_only:
        latest = _latest_execution([(Project(id=project_id, name=""), execution) for execution in executions])
        executions = [] if latest is None else [latest[1]]
    return {"executions": [_execution_payload(execution) for execution in executions]}


def list_latest_execution_bugs(
    project_name: str | None = None,
    assigned_to: str | None = None,
    opened_by: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 100,
    fetch_all: bool = False,
) -> dict[str, Any]:
    """List bugs from the latest execution in the current user's involved projects."""
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

        latest = _latest_execution(scoped_executions)
        if latest is None:
            return {"error": "No executions found for involved projects."}

        project, execution = latest
        bugs = client.list_bugs(
            execution=execution.id,
            assigned_to=_resolve_me(assigned_to),
            opened_by=_resolve_me(opened_by),
            status=status,
            page=page,
            page_size=page_size,
            fetch_all=fetch_all,
        )
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {
        "project": _project_payload(project),
        "execution": _execution_payload(execution),
        "bugs": [_bug_payload(bug) for bug in bugs],
    }


bug_agent = LlmAgent(
    model=zentao_model(),
    name="bug_agent",
    description="Handles read-only Zentao bug query workflows.",
    instruction=(
        "You are the Zentao bug specialist. Handle only read-only bug "
        "queries: list bugs, filter bugs, and inspect a single bug. "
        "You can also discover the current user's involved projects and "
        "list a project's executions before selecting an execution to query. "
        "When the user does not provide an execution ID, first use the "
        "latest-execution bug lookup tool so involved projects are checked, "
        "the latest execution is selected, and bugs are listed from there. "
        "Use the provided tools for all bug data. If the user asks to "
        "create, update, close, or delete a bug, explain that this first "
        "stage only supports bug query operations."
    ),
    tools=[list_involved_projects, list_project_executions, list_bugs, list_latest_execution_bugs, get_bug],
)
