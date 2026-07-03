from __future__ import annotations

from dataclasses import asdict
from typing import Any

from google.adk.agents import LlmAgent

from zentao_agent.model import zentao_model
from zentao_cli.auth import client_from_profile, current_username
from zentao_cli.errors import ZentaoCliError
from zentao_cli.models import Bug


def _bug_payload(bug: Bug) -> dict[str, Any]:
    return asdict(bug)


def _resolve_me(value: str | None) -> str | None:
    if value is not None and value.lower() == "me":
        return current_username()
    return value


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


def create_bug(
    execution: int,
    title: str,
    steps: str,
    product: int | None = None,
    severity: int = 3,
    pri: int = 3,
    bug_type: str = "codeerror",
    assigned_to: str | None = None,
    opened_build: str = "trunk",
    deadline: str | None = None,
) -> dict[str, Any]:
    """Create a Zentao bug in one execution."""
    try:
        client = client_from_profile()
        bug = client.create_bug(
            execution=execution,
            title=title,
            steps=steps,
            product=product,
            severity=severity,
            pri=pri,
            bug_type=bug_type,
            assigned_to=_resolve_me(assigned_to),
            opened_build=opened_build,
            deadline=deadline,
        )
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"bug": _bug_payload(bug)}


def update_bug(
    bug_id: int,
    title: str | None = None,
    steps: str | None = None,
    severity: int | None = None,
    pri: int | None = None,
    bug_type: str | None = None,
    assigned_to: str | None = None,
    deadline: str | None = None,
) -> dict[str, Any]:
    """Update fields on one Zentao bug."""
    try:
        client = client_from_profile()
        bug = client.update_bug(
            bug_id=bug_id,
            title=title,
            steps=steps,
            severity=severity,
            pri=pri,
            bug_type=bug_type,
            assigned_to=_resolve_me(assigned_to),
            deadline=deadline,
        )
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"bug": _bug_payload(bug)}


def delete_bug(bug_id: int) -> dict[str, Any]:
    """Delete one Zentao bug by id."""
    try:
        client = client_from_profile()
        result = client.delete_bug(bug_id)
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"result": result}


bug_agent = LlmAgent(
    model=zentao_model(),
    name="bug_agent",
    description="Handles Zentao bug workflows.",
    instruction=(
        "You are the Zentao bug specialist. Handle bug requests: list bugs, "
        "filter bugs, inspect a single bug, create a bug, update fields, and "
        "delete a bug. Use list_bugs and create_bug only after an execution "
        "ID is known. If the user has not provided an execution ID, ask the "
        "coordinator to get project and execution context from the project "
        "and execution specialists first. If create_bug needs an explicit "
        "product ID, ask the coordinator to get product context from the "
        "product specialist first. Delete bugs only when the user clearly "
        "requests deletion of a specific bug ID. Use the provided tools for "
        "all bug data. Do not answer bug data questions from memory."
    ),
    tools=[list_bugs, get_bug, create_bug, update_bug, delete_bug],
)
