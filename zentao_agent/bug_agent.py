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


bug_agent = LlmAgent(
    model=zentao_model(),
    name="bug_agent",
    description="Handles read-only Zentao bug query workflows.",
    instruction=(
        "You are the Zentao bug specialist. Handle only read-only bug "
        "queries: list bugs, filter bugs, and inspect a single bug. "
        "Use the provided tools for all bug data. If the user asks to "
        "create, update, close, or delete a bug, explain that this first "
        "stage only supports bug query operations. Ask for the execution "
        "ID when listing bugs and the user has not provided one."
    ),
    tools=[list_bugs, get_bug],
)
