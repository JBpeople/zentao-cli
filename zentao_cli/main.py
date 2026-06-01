from __future__ import annotations

import typer

from zentao_cli import __version__
from zentao_cli.auth import login_interactive, require_profile
from zentao_cli.commands import bug, execution, product, project, story, task

app = typer.Typer(help="CLI for Zentao Open Source Edition 21.7.5.")
app.add_typer(product.app, name="product")
app.add_typer(project.app, name="project")
app.add_typer(execution.app, name="execution")
app.add_typer(task.app, name="task")
app.add_typer(bug.app, name="bug")
app.add_typer(story.app, name="story")


def version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show the zentao-cli version.",
    ),
) -> None:
    return None


@app.command()
def login() -> None:
    login_interactive()


@app.command()
def whoami() -> None:
    profile = require_profile()
    typer.echo(profile.username)


if __name__ == "__main__":
    app()
