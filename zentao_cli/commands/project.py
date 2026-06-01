from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from zentao_cli.auth import client_from_profile
from zentao_cli.errors import ZentaoCliError
from zentao_cli.formatters import error_payload, json_payload
from zentao_cli.models import Project

app = typer.Typer(help="Project commands.")
console = Console()


def _project_table(projects: list[Project]) -> Table:
    table = Table(title="Projects")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Code")
    table.add_column("Status")
    table.add_column("Model")
    table.add_column("Owner")
    for project in projects:
        table.add_row(
            str(project.id),
            project.name,
            project.code,
            project.status,
            project.model,
            project.owner,
        )
    return table


@app.command("list")
def list_projects(
    page: int = typer.Option(1, "--page", min=1, help="Page number."),
    page_size: int = typer.Option(100, "--page-size", min=1, max=1000, help="Records per page."),
    fetch_all: bool = typer.Option(False, "--all", help="Fetch all pages."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    try:
        client = client_from_profile()
        projects = client.list_projects(page=page, page_size=page_size, fetch_all=fetch_all)
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(projects))
    else:
        console.print(_project_table(projects))


@app.command("view")
def view_project(project_id: int, as_json: bool = typer.Option(False, "--json", help="Output JSON.")) -> None:
    try:
        client = client_from_profile()
        project = client.get_project(project_id)
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(project))
    else:
        console.print(_project_table([project]))
