from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from zentao_cli.auth import client_from_profile
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
    status: str | None = typer.Option(None, "--status", help="Filter by task status."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    try:
        client = client_from_profile()
        tasks = client.list_tasks(execution=execution, mine=mine, status=status)
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


@app.command("update")
def update_task(task_id: int, status: str = typer.Option(..., "--status")) -> None:
    try:
        client = client_from_profile()
        task = client.update_task_status(task_id, status)
    except ZentaoCliError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Updated task {task.id} to {task.status}")


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
