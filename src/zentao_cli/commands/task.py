from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from zentao_cli.auth import client_from_profile
from zentao_cli.formatters import json_payload
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
    mine: bool = typer.Option(False, "--mine", help="Only show tasks assigned to current user."),
    status: str | None = typer.Option(None, "--status", help="Filter by task status."),
    project: int | None = typer.Option(None, "--project", help="Filter by project ID."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    client = client_from_profile()
    tasks = client.list_tasks(mine=mine, status=status, project=project)
    if as_json:
        typer.echo(json_payload(tasks))
    else:
        console.print(_task_table(tasks))


@app.command("view")
def view_task(task_id: int, as_json: bool = typer.Option(False, "--json", help="Output JSON.")) -> None:
    client = client_from_profile()
    task = client.get_task(task_id)
    if as_json:
        typer.echo(json_payload(task))
    else:
        console.print(_task_table([task]))


@app.command("update")
def update_task(task_id: int, status: str = typer.Option(..., "--status")) -> None:
    client = client_from_profile()
    task = client.update_task_status(task_id, status)
    typer.echo(f"Updated task {task.id} to {task.status}")


@app.command("comment")
def comment_task(task_id: int, content: str) -> None:
    client = client_from_profile()
    client.comment_task(task_id, content)
    typer.echo(f"Commented on task {task_id}")


@app.command("finish")
def finish_task(task_id: int, comment: str | None = typer.Option(None, "--comment")) -> None:
    client = client_from_profile()
    task = client.finish_task(task_id, comment=comment)
    typer.echo(f"Finished task {task.id}")
