import httpx
import respx

from zentao_cli.client import ZentaoClient
from zentao_cli.errors import ApiError, NotFoundError
from zentao_cli.models import Product, Task


@respx.mock
def test_login_parses_session():
    route = respx.post("https://zentao.example.com/api.php/v1/tokens").mock(
        return_value=httpx.Response(
            200,
            json={"token": "abc123", "sessionName": "zentaosid"},
        )
    )

    client = ZentaoClient("https://zentao.example.com")
    session = client.login("alice", "secret")

    assert route.called
    assert session.session_name == "zentaosid"
    assert session.session_id == "abc123"


@respx.mock
def test_list_tasks_returns_normalized_tasks():
    respx.get("https://zentao.example.com/api.php/v1/tasks").mock(
        return_value=httpx.Response(
            200,
            json={"tasks": [{"id": 1, "name": "Fix login", "status": "doing"}]},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_name="zentaosid", session_id="abc123")
    tasks = client.list_tasks(mine=True)

    assert tasks == [Task(id=1, name="Fix login", status="doing")]


@respx.mock
def test_list_products_returns_normalized_products():
    route = respx.get("https://zentao.example.com/api.php/v1/products").mock(
        return_value=httpx.Response(
            200,
            json={
                "products": [
                    {
                        "id": 5,
                        "name": "Platform",
                        "code": "PLAT",
                        "status": "normal",
                        "type": "product",
                        "PO": {"account": "alice"},
                    }
                ]
            },
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    products = client.list_products()

    assert route.called
    assert products == [Product(id=5, name="Platform", code="PLAT", status="normal", type="product", owner="alice")]


@respx.mock
def test_get_product_returns_normalized_product():
    respx.get("https://zentao.example.com/api.php/v1/products/5").mock(
        return_value=httpx.Response(
            200,
            json={"id": 5, "name": "Platform", "status": "normal", "PO": {"account": "alice"}},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    product = client.get_product(5)

    assert product.id == 5
    assert product.name == "Platform"
    assert product.owner == "alice"


@respx.mock
def test_http_error_uses_api_error_message():
    respx.get("https://zentao.example.com/api.php/v1/bugs").mock(
        return_value=httpx.Response(400, json={"error": "Need product id."})
    )

    client = ZentaoClient("https://zentao.example.com")

    try:
        client._request("GET", "bugs")
    except ApiError as exc:
        assert str(exc) == "Need product id."
    else:
        raise AssertionError("Expected ApiError")


@respx.mock
def test_list_bugs_uses_product_scope_when_product_is_provided():
    respx.get("https://zentao.example.com/api.php/v1/products").mock(
        return_value=httpx.Response(200, json={"products": [{"id": 5}]})
    )
    route = respx.get("https://zentao.example.com/api.php/v1/products/5/bugs").mock(
        return_value=httpx.Response(
            200,
            json={"bugs": [{"id": 7, "title": "Crash", "status": "active"}]},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    bugs = client.list_bugs(product=5)

    assert route.called
    assert bugs[0].id == 7
    assert bugs[0].title == "Crash"


@respx.mock
def test_list_bugs_rejects_unknown_product_before_querying_bugs():
    respx.get("https://zentao.example.com/api.php/v1/products").mock(
        return_value=httpx.Response(200, json={"products": [{"id": 5}]})
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")

    try:
        client.list_bugs(product=1000)
    except NotFoundError as exc:
        assert str(exc) == "Product 1000 was not found or is not visible"
    else:
        raise AssertionError("Expected NotFoundError")


@respx.mock
def test_list_bugs_aggregates_all_products_when_product_is_not_provided():
    respx.get("https://zentao.example.com/api.php/v1/products").mock(
        return_value=httpx.Response(200, json={"products": [{"id": 5}, {"id": 6}]})
    )
    respx.get("https://zentao.example.com/api.php/v1/products/5/bugs").mock(
        return_value=httpx.Response(200, json={"bugs": [{"id": 7, "title": "Crash"}]})
    )
    respx.get("https://zentao.example.com/api.php/v1/products/6/bugs").mock(
        return_value=httpx.Response(200, json={"bugs": [{"id": 8, "title": "UI bug"}]})
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    bugs = client.list_bugs()

    assert [bug.id for bug in bugs] == [7, 8]


@respx.mock
def test_list_stories_uses_product_scope_when_product_is_provided():
    respx.get("https://zentao.example.com/api.php/v1/products").mock(
        return_value=httpx.Response(200, json={"products": [{"id": 5}]})
    )
    route = respx.get("https://zentao.example.com/api.php/v1/products/5/stories").mock(
        return_value=httpx.Response(
            201,
            json={"stories": [{"id": 9, "title": "Login story", "status": "active"}]},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")
    stories = client.list_stories(product=5)

    assert route.called
    assert stories[0].id == 9
    assert stories[0].title == "Login story"


@respx.mock
def test_list_stories_rejects_unknown_product_before_querying_stories():
    respx.get("https://zentao.example.com/api.php/v1/products").mock(
        return_value=httpx.Response(200, json={"products": [{"id": 5}]})
    )

    client = ZentaoClient("https://zentao.example.com", session_id="abc123")

    try:
        client.list_stories(product=1000)
    except NotFoundError as exc:
        assert str(exc) == "Product 1000 was not found or is not visible"
    else:
        raise AssertionError("Expected NotFoundError")
