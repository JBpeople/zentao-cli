import json

from typer.testing import CliRunner

from zentao_cli.main import app
from zentao_cli.models import Product

runner = CliRunner()


def test_product_list_json(mocker):
    client = mocker.Mock()
    client.list_products.return_value = [
        Product(id=5, name="Platform", code="PLAT", status="normal", type="product", owner="alice")
    ]
    mocker.patch("zentao_cli.commands.product.client_from_profile", return_value=client)

    result = runner.invoke(app, ["product", "list", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"][0]["id"] == 5
    client.list_products.assert_called_once_with(page=1, page_size=100, fetch_all=False)


def test_product_list_passes_pagination_options(mocker):
    client = mocker.Mock()
    client.list_products.return_value = [
        Product(id=5, name="Platform", code="PLAT", status="normal", type="product", owner="alice")
    ]
    mocker.patch("zentao_cli.commands.product.client_from_profile", return_value=client)

    result = runner.invoke(app, ["product", "list", "--page", "2", "--page-size", "50", "--all", "--json"])

    assert result.exit_code == 0
    client.list_products.assert_called_once_with(page=2, page_size=50, fetch_all=True)


def test_product_view_json(mocker):
    client = mocker.Mock()
    client.get_product.return_value = Product(id=5, name="Platform", status="normal", owner="alice")
    mocker.patch("zentao_cli.commands.product.client_from_profile", return_value=client)

    result = runner.invoke(app, ["product", "view", "5", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"]["name"] == "Platform"
    client.get_product.assert_called_once_with(5)
