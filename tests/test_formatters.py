import json

from zentao_cli.errors import AuthError
from zentao_cli.formatters import error_payload, json_payload
from zentao_cli.models import Task


def test_json_payload_wraps_success_data():
    rendered = json_payload({"id": 7, "name": "demo"})

    assert json.loads(rendered) == {"ok": True, "data": {"id": 7, "name": "demo"}}


def test_error_payload_has_stable_shape():
    rendered = error_payload(AuthError("not logged in"))

    assert json.loads(rendered) == {
        "ok": False,
        "error": {"type": "AuthError", "message": "not logged in"},
    }


def test_json_payload_serializes_task_dataclass():
    task = Task(
        id=1,
        name="Fix login",
        project="Core",
        status="doing",
        priority="2",
        deadline="2026-06-01",
        assigned_to="alice",
    )

    rendered = json_payload(task)

    assert json.loads(rendered)["data"]["name"] == "Fix login"


def test_task_from_api_normalizes_assigned_user_object():
    task = Task.from_api(
        {
            "id": 2,
            "name": "Fix assigned user",
            "assignedTo": {"account": "alice", "realname": "Alice"},
        }
    )

    assert task.assigned_to == "alice"
