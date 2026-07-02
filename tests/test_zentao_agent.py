from __future__ import annotations

from zentao_cli.errors import AuthError
from zentao_cli.models import Bug


def test_list_bugs_returns_plain_dicts(mocker):
    from zentao_agent import bug_agent

    client = mocker.Mock()
    client.list_bugs.return_value = [
        Bug(
            id=7,
            title="Crash on import",
            status="active",
            severity="3",
            assigned_to="alice",
            opened_by="bob",
        )
    ]
    mocker.patch("zentao_agent.bug_agent.client_from_profile", return_value=client)

    result = bug_agent.list_bugs(
        execution=303,
        assigned_to="alice",
        status="active",
        page=2,
        page_size=50,
        fetch_all=True,
    )

    client.list_bugs.assert_called_once_with(
        execution=303,
        assigned_to="alice",
        opened_by=None,
        status="active",
        page=2,
        page_size=50,
        fetch_all=True,
    )
    assert result == {
        "bugs": [
            {
                "id": 7,
                "title": "Crash on import",
                "status": "active",
                "severity": "3",
                "assigned_to": "alice",
                "opened_by": "bob",
            }
        ]
    }


def test_list_bugs_resolves_me_for_assigned_to(mocker):
    from zentao_agent import bug_agent

    client = mocker.Mock()
    client.list_bugs.return_value = []
    mocker.patch("zentao_agent.bug_agent.client_from_profile", return_value=client)
    mocker.patch("zentao_agent.bug_agent.current_username", return_value="yangchangkun")

    result = bug_agent.list_bugs(execution=303, assigned_to="me")

    client.list_bugs.assert_called_once_with(
        execution=303,
        assigned_to="yangchangkun",
        opened_by=None,
        status=None,
        page=1,
        page_size=100,
        fetch_all=False,
    )
    assert result == {"bugs": []}


def test_list_bugs_resolves_me_for_opened_by(mocker):
    from zentao_agent import bug_agent

    client = mocker.Mock()
    client.list_bugs.return_value = []
    mocker.patch("zentao_agent.bug_agent.client_from_profile", return_value=client)
    mocker.patch("zentao_agent.bug_agent.current_username", return_value="yangchangkun")

    result = bug_agent.list_bugs(execution=303, opened_by="me")

    client.list_bugs.assert_called_once_with(
        execution=303,
        assigned_to=None,
        opened_by="yangchangkun",
        status=None,
        page=1,
        page_size=100,
        fetch_all=False,
    )
    assert result == {"bugs": []}


def test_get_bug_returns_plain_dict(mocker):
    from zentao_agent import bug_agent

    client = mocker.Mock()
    client.get_bug.return_value = Bug(
        id=7,
        title="Crash on import",
        status="active",
        severity="3",
        assigned_to="alice",
        opened_by="bob",
    )
    mocker.patch("zentao_agent.bug_agent.client_from_profile", return_value=client)

    result = bug_agent.get_bug(7)

    client.get_bug.assert_called_once_with(7)
    assert result == {
        "bug": {
            "id": 7,
            "title": "Crash on import",
            "status": "active",
            "severity": "3",
            "assigned_to": "alice",
            "opened_by": "bob",
        }
    }


def test_bug_tools_return_structured_errors(mocker):
    from zentao_agent import bug_agent

    mocker.patch(
        "zentao_agent.bug_agent.client_from_profile",
        side_effect=AuthError("Not logged in. Run: zentao login"),
    )

    assert bug_agent.get_bug(7) == {
        "error": "Not logged in. Run: zentao login"
    }
