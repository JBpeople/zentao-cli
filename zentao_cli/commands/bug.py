from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from zentao_cli.auth import client_from_profile, current_username
from zentao_cli.errors import ZentaoCliError
from zentao_cli.formatters import error_payload, json_payload
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
    execution: int = typer.Option(..., "--execution", help="Execution ID."),
    assigned_to: str | None = typer.Option(None, "--assigned-to"),
    opened_by: str | None = typer.Option(None, "--opened-by", help="Only show bugs opened by account, or me."),
    status: str | None = typer.Option(None, "--status"),
    page: int = typer.Option(1, "--page", min=1, help="Page number."),
    page_size: int = typer.Option(100, "--page-size", min=1, max=1000, help="Records per page."),
    fetch_all: bool = typer.Option(False, "--all", help="Fetch all pages."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    try:
        client = client_from_profile()
        kwargs = {
            "execution": execution,
            "assigned_to": assigned_to,
            "status": status,
            "page": page,
            "page_size": page_size,
            "fetch_all": fetch_all,
        }
        if opened_by:
            kwargs["opened_by"] = current_username() if opened_by.lower() == "me" else opened_by
        bugs = client.list_bugs(**kwargs)
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(bugs))
    else:
        console.print(_bug_table(bugs))


@app.command("view")
def view_bug(bug_id: int, as_json: bool = typer.Option(False, "--json", help="Output JSON.")) -> None:
    try:
        client = client_from_profile()
        bug = client.get_bug(bug_id)
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(bug))
    else:
        console.print(_bug_table([bug]))


@app.command("create")
def create_bug(
    execution: int = typer.Option(..., "--execution", help="Execution ID."),
    title: str = typer.Option(..., "--title", help="Bug title."),
    steps: str = typer.Option(..., "--steps", help="Reproduction steps."),
    product: int | None = typer.Option(None, "--product", help="Product ID."),
    severity: int = typer.Option(3, "--severity", min=1, max=4, help="Severity, usually 1-4."),
    pri: int = typer.Option(3, "--pri", min=1, max=4, help="Priority, usually 1-4."),
    bug_type: str = typer.Option("codeerror", "--type", help="Bug type."),
    assigned_to: str | None = typer.Option(None, "--assigned-to", help="Assignee account."),
    opened_build: str = typer.Option("trunk", "--opened-build", help="Affected build."),
    deadline: str | None = typer.Option(None, "--deadline", help="Deadline date, YYYY-MM-DD."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    try:
        client = client_from_profile()
        bug = client.create_bug(
            execution=execution,
            product=product,
            title=title,
            steps=steps,
            severity=severity,
            pri=pri,
            bug_type=bug_type,
            assigned_to=assigned_to,
            opened_build=opened_build,
            deadline=deadline,
        )
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(bug))
    else:
        console.print(_bug_table([bug]))


@app.command("update")
def update_bug(
    bug_id: int,
    title: str | None = typer.Option(None, "--title", help="Bug title."),
    steps: str | None = typer.Option(None, "--steps", help="Reproduction steps."),
    severity: int | None = typer.Option(None, "--severity", min=1, max=4, help="Severity, usually 1-4."),
    pri: int | None = typer.Option(None, "--pri", min=1, max=4, help="Priority, usually 1-4."),
    bug_type: str | None = typer.Option(None, "--type", help="Bug type."),
    assigned_to: str | None = typer.Option(None, "--assigned-to", help="Assignee account."),
    deadline: str | None = typer.Option(None, "--deadline", help="Deadline date, YYYY-MM-DD."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    if not any(value is not None for value in (title, steps, severity, pri, bug_type, assigned_to, deadline)):
        raise typer.BadParameter("Use at least one field to update.")
    try:
        client = client_from_profile()
        bug = client.update_bug(
            bug_id=bug_id,
            title=title,
            steps=steps,
            severity=severity,
            pri=pri,
            bug_type=bug_type,
            assigned_to=assigned_to,
            deadline=deadline,
        )
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(bug))
    else:
        console.print(_bug_table([bug]))


@app.command("delete")
def delete_bug(
    bug_id: int,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    if not yes:
        typer.confirm(f"Delete bug {bug_id}?", abort=True)
    try:
        client = client_from_profile()
        result = client.delete_bug(bug_id)
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(result))
    else:
        typer.echo(f"Deleted bug {bug_id}")
