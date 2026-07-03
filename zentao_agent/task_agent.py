from __future__ import annotations

from dataclasses import asdict
from typing import Any

from google.adk.agents import LlmAgent

from zentao_agent.model import zentao_model
from zentao_cli.auth import client_from_profile, current_username
from zentao_cli.errors import ZentaoCliError
from zentao_cli.models import Task


def _task_payload(task: Task) -> dict[str, Any]:
    return asdict(task)


def _resolve_me(value: str | None) -> str | None:
    if value is not None and value.lower() == "me":
        return current_username()
    return value


def list_tasks(
    execution: int,
    mine: bool = False,
    status: str | None = None,
    opened_by: str | None = None,
    page: int = 1,
    page_size: int = 100,
    fetch_all: bool = False,
) -> dict[str, Any]:
    """List tasks in a Zentao execution using optional filters."""
    try:
        client = client_from_profile()
        tasks = client.list_tasks(
            execution=execution,
            mine=mine,
            status=status,
            opened_by=_resolve_me(opened_by),
            page=page,
            page_size=page_size,
            fetch_all=fetch_all,
        )
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"tasks": [_task_payload(task) for task in tasks]}


def get_task(task_id: int) -> dict[str, Any]:
    """Get one Zentao task by id."""
    try:
        client = client_from_profile()
        task = client.get_task(task_id)
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"task": _task_payload(task)}


def create_task(
    execution: int,
    name: str,
    est_started: str,
    deadline: str,
    story: int | None = None,
    task_type: str = "devel",
    assigned_to: str | None = None,
    estimate: float | None = None,
    pri: int = 3,
    desc: str | None = None,
) -> dict[str, Any]:
    """Create a Zentao task in one execution."""
    try:
        client = client_from_profile()
        task = client.create_task(
            execution=execution,
            name=name,
            est_started=est_started,
            deadline=deadline,
            story=story,
            task_type=task_type,
            assigned_to=_resolve_me(assigned_to),
            estimate=estimate,
            pri=pri,
            desc=desc,
        )
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"task": _task_payload(task)}


def update_task(
    task_id: int,
    name: str | None = None,
    status: str | None = None,
    assigned_to: str | None = None,
    estimate: float | None = None,
    deadline: str | None = None,
    est_started: str | None = None,
    pri: int | None = None,
    desc: str | None = None,
    task_type: str | None = None,
) -> dict[str, Any]:
    """Update fields on one Zentao task."""
    try:
        client = client_from_profile()
        task = client.update_task(
            task_id=task_id,
            name=name,
            status=status,
            assigned_to=_resolve_me(assigned_to),
            estimate=estimate,
            deadline=deadline,
            est_started=est_started,
            pri=pri,
            desc=desc,
            task_type=task_type,
        )
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"task": _task_payload(task)}


def delete_task(task_id: int) -> dict[str, Any]:
    """Delete one Zentao task by id."""
    try:
        client = client_from_profile()
        result = client.delete_task(task_id)
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"result": result}


def comment_task(task_id: int, content: str) -> dict[str, Any]:
    """Add one comment to a Zentao task."""
    try:
        client = client_from_profile()
        client.comment_task(task_id, content)
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"task": task_id, "commented": True}


def finish_task(task_id: int, comment: str | None = None) -> dict[str, Any]:
    """Finish one Zentao task, optionally adding a comment."""
    try:
        client = client_from_profile()
        task = client.finish_task(task_id, comment=comment)
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"task": _task_payload(task)}


task_agent = LlmAgent(
    model=zentao_model(),
    name="task_agent",
    description="Handles Zentao task workflows.",
    instruction=(
        "You are the Zentao task specialist. Handle task requests: list tasks, "
        "filter tasks, inspect a single task, create a task, update fields, "
        "delete a task, comment on a task, and finish a task. Use list_tasks "
        "and create_task only after an execution ID is known. If the user has "
        "not provided an execution ID, ask the coordinator to get project and "
        "execution context from the project and execution specialists first. "
        "Use the provided tools for all task data. Do not answer task data "
        "questions from memory."
    ),
    tools=[list_tasks, get_task, create_task, update_task, delete_task, comment_task, finish_task],
)
