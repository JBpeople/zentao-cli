import httpx
import respx

from zentao_cli.client import ZentaoClient
from zentao_cli.models import Task


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
