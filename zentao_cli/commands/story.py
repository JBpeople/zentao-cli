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
    product: int = typer.Option(..., "--product", help="Product ID."),
    status: str | None = typer.Option(None, "--status"),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    try:
        client = client_from_profile()
        stories = client.list_stories(product=product, status=status)
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
    product: int = typer.Option(..., "--product", help="Product ID."),
    title: str = typer.Option(..., "--title", help="Story title."),
    spec: str = typer.Option(..., "--spec", help="Story body/specification."),
    verify: str | None = typer.Option(None, "--verify", help="Acceptance criteria."),
    pri: int = typer.Option(3, "--pri", min=1, max=4, help="Priority, usually 1-4."),
    category: str = typer.Option("feature", "--category", help="Story category, for example feature."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    try:
        client = client_from_profile()
        story = client.create_story(
            product=product,
            title=title,
            spec=spec,
            verify=verify,
            pri=pri,
            category=category,
        )
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
