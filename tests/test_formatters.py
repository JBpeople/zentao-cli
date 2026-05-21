import json

from zentao_cli.errors import AuthError
from zentao_cli.formatters import error_payload, json_payload


def test_json_payload_wraps_success_data():
    rendered = json_payload({"id": 7, "name": "demo"})

    assert json.loads(rendered) == {"ok": True, "data": {"id": 7, "name": "demo"}}


def test_error_payload_has_stable_shape():
    rendered = error_payload(AuthError("not logged in"))

    assert json.loads(rendered) == {
        "ok": False,
        "error": {"type": "AuthError", "message": "not logged in"},
    }
