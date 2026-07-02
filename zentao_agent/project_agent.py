from __future__ import annotations

from dataclasses import asdict
from typing import Any

from google.adk.agents import LlmAgent

from zentao_agent.model import zentao_model
from zentao_cli.auth import client_from_profile
from zentao_cli.errors import ZentaoCliError
from zentao_cli.models import Project


def _project_payload(project: Project) -> dict[str, Any]:
    return asdict(project)


def list_projects(
    involved: bool = False,
    page: int = 1,
    page_size: int = 100,
    fetch_all: bool = False,
) -> dict[str, Any]:
    """List Zentao projects visible to the current user."""
    try:
        client = client_from_profile()
        projects = client.list_projects(
            page=page,
            page_size=page_size,
            fetch_all=fetch_all,
            involved=involved,
        )
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"projects": [_project_payload(project) for project in projects]}


def get_project(project_id: int) -> dict[str, Any]:
    """Get one Zentao project by id."""
    try:
        client = client_from_profile()
        project = client.get_project(project_id)
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"project": _project_payload(project)}


project_agent = LlmAgent(
    model=zentao_model(),
    name="project_agent",
    description="Handles read-only Zentao project discovery workflows.",
    instruction=(
        "You are the Zentao project specialist. Handle only read-only project "
        "queries: list visible projects, list projects involving the current "
        "user, and inspect a single project. Use involved=True when the user "
        "asks for projects they participate in. Use the provided tools for all "
        "project data. If the user asks for executions, products, or bugs, "
        "explain that another specialist should handle that part."
    ),
    tools=[list_projects, get_project],
)
