from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from zentao_cli.auth import client_from_profile
from zentao_cli.formatters import json_payload
from zentao_cli.models import Bug

app = typer.Typer(help="Bug commands.")
console = Console()


def _bug_table(bugs: list[Bug]) -> Table:
    table = Table(title="Bugs")
    table.add_column("ID", justify="right")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Severity")
    table.add_column("Assignee")
    for bug in bugs:
        table.add_row(str(bug.id), bug.title, bug.status, bug.severity, bug.assigned_to)
    return table


@app.command("list")
def list_bugs(
    assigned_to: str | None = typer.Option(None, "--assigned-to"),
    status: str | None = typer.Option(None, "--status"),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    client = client_from_profile()
    bugs = client.list_bugs(assigned_to=assigned_to, status=status)
    if as_json:
        typer.echo(json_payload(bugs))
    else:
        console.print(_bug_table(bugs))


@app.command("view")
def view_bug(bug_id: int, as_json: bool = typer.Option(False, "--json", help="Output JSON.")) -> None:
    client = client_from_profile()
    bug = client.get_bug(bug_id)
    if as_json:
        typer.echo(json_payload(bug))
    else:
        console.print(_bug_table([bug]))
