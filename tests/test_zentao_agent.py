from __future__ import annotations

from zentao_cli.errors import AuthError
from zentao_cli.models import Bug, Execution, Project


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


def test_list_latest_execution_bugs_uses_latest_execution_from_involved_projects(mocker):
    from zentao_agent import bug_agent

    client = mocker.Mock()
    client.list_projects.return_value = [
        Project(id=33, name="P03010-WIZ Resource", status="doing"),
        Project(id=362, name="P00402-Youchao 3D Factory Design", status="doing"),
    ]
    client.list_executions.return_value = [
        Execution(id=490, name="P00402-20260603", project="362", begin="2026-06-15"),
        Execution(id=492, name="P00402-20260604", project="362", begin="2026-06-22"),
    ]
    client.list_bugs.return_value = [Bug(id=1800, title="Layout detection level config is ineffective")]
    mocker.patch("zentao_agent.bug_agent.client_from_profile", return_value=client)

    result = bug_agent.list_latest_execution_bugs(project_name="Youchao")

    client.list_projects.assert_called_once_with(involved=True, fetch_all=True)
    client.list_executions.assert_called_once_with(project=362, fetch_all=True)
    client.list_bugs.assert_called_once_with(
        execution=492,
        assigned_to=None,
        opened_by=None,
        status=None,
        page=1,
        page_size=100,
        fetch_all=False,
    )
    assert result["project"]["id"] == 362
    assert result["execution"]["id"] == 492
    assert result["bugs"] == [
        {
            "id": 1800,
            "title": "Layout detection level config is ineffective",
            "status": "",
            "severity": "",
            "assigned_to": "",
            "opened_by": "",
        }
    ]


def test_list_latest_execution_bugs_returns_error_when_no_execution_exists(mocker):
    from zentao_agent import bug_agent

    client = mocker.Mock()
    client.list_projects.return_value = [Project(id=362, name="P00402-Youchao 3D Factory Design")]
    client.list_executions.return_value = []
    mocker.patch("zentao_agent.bug_agent.client_from_profile", return_value=client)

    result = bug_agent.list_latest_execution_bugs()

    assert result == {"error": "No executions found for involved projects."}


def test_bug_tools_return_structured_errors(mocker):
    from zentao_agent import bug_agent

    mocker.patch(
        "zentao_agent.bug_agent.client_from_profile",
        side_effect=AuthError("Not logged in. Run: zentao login"),
    )

    assert bug_agent.get_bug(7) == {
        "error": "Not logged in. Run: zentao login"
    }


def test_root_agent_registers_bug_agent():
    from zentao_agent.agent import root_agent
    from zentao_agent.bug_agent import bug_agent

    assert bug_agent in root_agent.sub_agents
    assert root_agent.name == "root_agent"
