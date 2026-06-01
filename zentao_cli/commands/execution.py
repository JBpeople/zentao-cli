from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from zentao_cli.auth import client_from_profile
from zentao_cli.errors import ZentaoCliError
from zentao_cli.formatters import error_payload, json_payload
from zentao_cli.models import Execution

app = typer.Typer(help="Execution commands.")
console = Console()


def _execution_table(executions: list[Execution]) -> Table:
    table = Table(title="Executions")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Project")
    table.add_column("Status")
    table.add_column("Type")
    table.add_column("Begin")
    table.add_column("End")
    for execution in executions:
        table.add_row(
            str(execution.id),
            execution.name,
            execution.project,
            execution.status,
            execution.type,
            execution.begin,
            execution.end,
        )
    return table


@app.command("list")
def list_executions(
    project: int = typer.Option(..., "--project", help="Project ID."),
    page: int = typer.Option(1, "--page", min=1, help="Page number."),
    page_size: int = typer.Option(100, "--page-size", min=1, max=1000, help="Records per page."),
    fetch_all: bool = typer.Option(False, "--all", help="Fetch all pages."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    try:
        client = client_from_profile()
        executions = client.list_executions(project=project, page=page, page_size=page_size, fetch_all=fetch_all)
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(executions))
    else:
        console.print(_execution_table(executions))


@app.command("view")
def view_execution(execution_id: int, as_json: bool = typer.Option(False, "--json", help="Output JSON.")) -> None:
    try:
        client = client_from_profile()
        execution = client.get_execution(execution_id)
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(execution))
    else:
        console.print(_execution_table([execution]))


@app.command("link-story")
def link_story(
    execution_id: int,
    story_id: int = typer.Option(..., "--story", help="Story ID."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    try:
        client = client_from_profile()
        result = client.link_story(execution_id=execution_id, story_id=story_id)
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(result))
    else:
        typer.echo(f"Linked story {story_id} to execution {execution_id}")
