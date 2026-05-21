from __future__ import annotations

import typer

from zentao_cli import __version__

app = typer.Typer(help="CLI for Zentao Open Source Edition 21.7.5.")


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


if __name__ == "__main__":
    app()
