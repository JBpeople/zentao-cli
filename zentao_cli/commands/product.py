from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from zentao_cli.auth import client_from_profile
from zentao_cli.errors import ZentaoCliError
from zentao_cli.formatters import error_payload, json_payload
from zentao_cli.models import Product

app = typer.Typer(help="Product commands.")
console = Console()


def _product_table(products: list[Product]) -> Table:
    table = Table(title="Products")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Code")
    table.add_column("Status")
    table.add_column("Type")
    table.add_column("Owner")
    for product in products:
        table.add_row(
            str(product.id),
            product.name,
            product.code,
            product.status,
            product.type,
            product.owner,
        )
    return table


@app.command("list")
def list_products(as_json: bool = typer.Option(False, "--json", help="Output JSON.")) -> None:
    try:
        client = client_from_profile()
        products = client.list_products()
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(products))
    else:
        console.print(_product_table(products))


@app.command("view")
def view_product(product_id: int, as_json: bool = typer.Option(False, "--json", help="Output JSON.")) -> None:
    try:
        client = client_from_profile()
        product = client.get_product(product_id)
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(product))
    else:
        console.print(_product_table([product]))
