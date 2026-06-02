from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from zentao_cli.auth import client_from_profile, current_username
from zentao_cli.errors import ZentaoCliError
from zentao_cli.formatters import error_payload, json_payload
from zentao_cli.models import Task

app = typer.Typer(help="Task commands.")
console = Console()


def _task_table(tasks: list[Task]) -> Table:
    table = Table(title="Tasks")
    table.add_column("ID", justify="right")
    table.add_column("Title")
    table.add_column("Project")
    table.add_column("Status")
    table.add_column("Pri")
    table.add_column("Deadline")
    table.add_column("Assignee")
    for task in tasks:
        table.add_row(
            str(task.id),
            task.name,
            task.project,
            task.status,
            task.priority,
            task.deadline,
            task.assigned_to,
        )
    return table


@app.command("list")
def list_tasks(
    execution: int = typer.Option(..., "--execution", help="Execution ID."),
    mine: bool = typer.Option(False, "--mine", help="Only show tasks assigned to current user."),
    opened_by: str | None = typer.Option(None, "--opened-by", help="Only show tasks opened by account, or me."),
    status: str | None = typer.Option(None, "--status", help="Filter by task status."),
    page: int = typer.Option(1, "--page", min=1, help="Page number."),
    page_size: int = typer.Option(100, "--page-size", min=1, max=1000, help="Records per page."),
    fetch_all: bool = typer.Option(False, "--all", help="Fetch all pages."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    try:
        client = client_from_profile()
        kwargs = {
            "execution": execution,
            "mine": mine,
            "status": status,
            "page": page,
            "page_size": page_size,
            "fetch_all": fetch_all,
        }
        if opened_by:
            kwargs["opened_by"] = current_username() if opened_by.lower() == "me" else opened_by
        tasks = client.list_tasks(**kwargs)
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(tasks))
    else:
        console.print(_task_table(tasks))


@app.command("view")
def view_task(task_id: int, as_json: bool = typer.Option(False, "--json", help="Output JSON.")) -> None:
    try:
        client = client_from_profile()
        task = client.get_task(task_id)
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(task))
    else:
        console.print(_task_table([task]))


@app.command("create")
def create_task(
    execution: int = typer.Option(..., "--execution", help="Execution ID."),
    story: int | None = typer.Option(None, "--story", help="Story ID to create the task from."),
    name: str = typer.Option(..., "--name", help="Task name."),
    est_started: str = typer.Option(..., "--est-started", help="Estimated start date, YYYY-MM-DD."),
    deadline: str = typer.Option(..., "--deadline", help="Deadline date, YYYY-MM-DD."),
    task_type: str = typer.Option("devel", "--type", help="Task type, for example devel/test/design."),
    assigned_to: str | None = typer.Option(None, "--assigned-to", help="Assignee account."),
    estimate: float | None = typer.Option(None, "--estimate", help="Estimated hours."),
    pri: int = typer.Option(3, "--pri", min=1, max=4, help="Priority, usually 1-4."),
    desc: str | None = typer.Option(None, "--desc", help="Task description."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    try:
        client = client_from_profile()
        task = client.create_task(
            execution=execution,
            name=name,
            story=story,
            est_started=est_started,
            task_type=task_type,
            assigned_to=assigned_to,
            estimate=estimate,
            deadline=deadline,
            pri=pri,
            desc=desc,
        )
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(task))
    else:
        console.print(_task_table([task]))


@app.command("delete")
def delete_task(
    task_id: int,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    if not yes:
        typer.confirm(f"Delete task {task_id}?", abort=True)
    try:
        client = client_from_profile()
        result = client.delete_task(task_id)
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(result))
    else:
        typer.echo(f"Deleted task {task_id}")


@app.command("update")
def update_task(
    task_id: int,
    name: str | None = typer.Option(None, "--name", help="Task name."),
    status: str | None = typer.Option(None, "--status", help="Task status."),
    assigned_to: str | None = typer.Option(None, "--assigned-to", help="Assignee account."),
    estimate: float | None = typer.Option(None, "--estimate", help="Estimated hours."),
    deadline: str | None = typer.Option(None, "--deadline", help="Deadline date, YYYY-MM-DD."),
    est_started: str | None = typer.Option(None, "--est-started", help="Estimated start date, YYYY-MM-DD."),
    pri: int | None = typer.Option(None, "--pri", min=1, max=4, help="Priority, usually 1-4."),
    task_type: str | None = typer.Option(None, "--type", help="Task type, for example devel/test/design."),
    desc: str | None = typer.Option(None, "--desc", help="Task description."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    if not any(value is not None for value in (name, status, assigned_to, estimate, deadline, est_started, pri, task_type, desc)):
        raise typer.BadParameter("Use at least one field to update.")
    try:
        client = client_from_profile()
        task = client.update_task(
            task_id=task_id,
            name=name,
            status=status,
            assigned_to=assigned_to,
            estimate=estimate,
            deadline=deadline,
            est_started=est_started,
            pri=pri,
            task_type=task_type,
            desc=desc,
        )
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(task))
    else:
        typer.echo(f"Updated task {task.id}")


@app.command("comment")
def comment_task(task_id: int, content: str) -> None:
    try:
        client = client_from_profile()
        client.comment_task(task_id, content)
    except ZentaoCliError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Commented on task {task_id}")


@app.command("finish")
def finish_task(task_id: int, comment: str | None = typer.Option(None, "--comment")) -> None:
    try:
        client = client_from_profile()
        task = client.finish_task(task_id, comment=comment)
    except ZentaoCliError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Finished task {task.id}")
