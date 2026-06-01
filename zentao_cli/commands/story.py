from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from zentao_cli.auth import client_from_profile
from zentao_cli.errors import ZentaoCliError
from zentao_cli.formatters import error_payload, json_payload
from zentao_cli.models import Story

app = typer.Typer(help="Story commands.")
console = Console()


def _story_table(stories: list[Story]) -> Table:
    table = Table(title="Stories")
    table.add_column("ID", justify="right")
    table.add_column("Title")
    table.add_column("Product")
    table.add_column("Status")
    table.add_column("Stage")
    for story in stories:
        table.add_row(str(story.id), story.title, story.product, story.status, story.stage)
    return table


def _print_story_result(story: Story, as_json: bool) -> None:
    if as_json:
        typer.echo(json_payload(story))
    else:
        console.print(_story_table([story]))


@app.command("list")
def list_stories(
    product: int | None = typer.Option(None, "--product", help="Product ID."),
    execution: int | None = typer.Option(None, "--execution", help="Execution ID."),
    status: str | None = typer.Option(None, "--status"),
    page: int = typer.Option(1, "--page", min=1, help="Page number."),
    page_size: int = typer.Option(100, "--page-size", min=1, max=1000, help="Records per page."),
    fetch_all: bool = typer.Option(False, "--all", help="Fetch all pages."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    if (product is None and execution is None) or (product is not None and execution is not None):
        raise typer.BadParameter("Use either --product or --execution.")

    try:
        client = client_from_profile()
        if product is not None:
            stories = client.list_stories(
                product=product,
                status=status,
                page=page,
                page_size=page_size,
                fetch_all=fetch_all,
            )
        else:
            stories = client.list_stories(
                execution=execution,
                status=status,
                page=page,
                page_size=page_size,
                fetch_all=fetch_all,
            )
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(stories))
    else:
        console.print(_story_table(stories))


@app.command("view")
def view_story(story_id: int, as_json: bool = typer.Option(False, "--json", help="Output JSON.")) -> None:
    try:
        client = client_from_profile()
        story = client.get_story(story_id)
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(story))
    else:
        console.print(_story_table([story]))


@app.command("create")
def create_story(
    product: int | None = typer.Option(None, "--product", help="Product ID."),
    execution: int | None = typer.Option(None, "--execution", help="Execution ID."),
    title: str = typer.Option(..., "--title", help="Story title."),
    spec: str = typer.Option(..., "--spec", help="Story body/specification."),
    verify: str | None = typer.Option(None, "--verify", help="Acceptance criteria."),
    pri: int = typer.Option(3, "--pri", min=1, max=4, help="Priority, usually 1-4."),
    category: str = typer.Option("feature", "--category", help="Story category, for example feature."),
    status: str = typer.Option("draft", "--status", help="Story status: draft or active."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    if product is None and execution is None:
        raise typer.BadParameter("Use --product or --execution.")
    if status not in {"active", "draft"}:
        raise typer.BadParameter("--status must be active or draft.")

    try:
        client = client_from_profile()
        story = client.create_story(
            product=product,
            execution=execution,
            title=title,
            spec=spec,
            verify=verify,
            pri=pri,
            category=category,
            status=status,
        )
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    _print_story_result(story, as_json)


@app.command("delete")
def delete_story(
    story_id: int,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    if not yes:
        typer.confirm(f"Delete story {story_id}?", abort=True)
    try:
        client = client_from_profile()
        result = client.delete_story(story_id)
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(result))
    else:
        typer.echo(f"Deleted story {story_id}")


@app.command("update")
def update_story(
    story_id: int,
    title: str = typer.Option(..., "--title", help="New story title."),
    spec: str = typer.Option(..., "--spec", help="New story body/specification."),
    verify: str | None = typer.Option(None, "--verify", help="New acceptance criteria."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    try:
        client = client_from_profile()
        story = client.update_story(story_id=story_id, title=title, spec=spec, verify=verify)
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    _print_story_result(story, as_json)


@app.command("change")
def change_story(
    story_id: int,
    title: str = typer.Option(..., "--title", help="New story title."),
    spec: str = typer.Option(..., "--spec", help="New story body/specification."),
    verify: str | None = typer.Option(None, "--verify", help="New acceptance criteria."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    try:
        client = client_from_profile()
        story = client.change_story(story_id=story_id, title=title, spec=spec, verify=verify)
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    _print_story_result(story, as_json)
