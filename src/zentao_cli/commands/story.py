from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from zentao_cli.auth import client_from_profile
from zentao_cli.formatters import json_payload
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


@app.command("list")
def list_stories(
    product: int | None = typer.Option(None, "--product"),
    status: str | None = typer.Option(None, "--status"),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    client = client_from_profile()
    stories = client.list_stories(product=product, status=status)
    if as_json:
        typer.echo(json_payload(stories))
    else:
        console.print(_story_table(stories))


@app.command("view")
def view_story(story_id: int, as_json: bool = typer.Option(False, "--json", help="Output JSON.")) -> None:
    client = client_from_profile()
    story = client.get_story(story_id)
    if as_json:
        typer.echo(json_payload(story))
    else:
        console.print(_story_table([story]))
