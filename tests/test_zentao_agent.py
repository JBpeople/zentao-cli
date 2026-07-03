from __future__ import annotations

from zentao_cli.errors import AuthError
from zentao_cli.models import Bug, Execution, Product, Project, Task


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


def test_bug_agent_exposes_only_bug_tools():
    from zentao_agent.bug_agent import bug_agent

    tool_names = [tool.__name__ for tool in bug_agent.tools]

    assert tool_names == ["list_bugs", "get_bug"]


def test_bug_tools_return_structured_errors(mocker):
    from zentao_agent import bug_agent

    mocker.patch(
        "zentao_agent.bug_agent.client_from_profile",
        side_effect=AuthError("Not logged in. Run: zentao login"),
    )

    assert bug_agent.get_bug(7) == {
        "error": "Not logged in. Run: zentao login"
    }


def test_task_agent_lists_tasks_as_plain_dicts(mocker):
    from zentao_agent import task_agent

    client = mocker.Mock()
    client.list_tasks.return_value = [
        Task(id=1, name="Fix login", status="doing", priority="2", assigned_to="alice")
    ]
    mocker.patch("zentao_agent.task_agent.client_from_profile", return_value=client)

    result = task_agent.list_tasks(
        execution=303,
        mine=True,
        status="doing",
        opened_by="bob",
        page=2,
        page_size=50,
        fetch_all=True,
    )

    client.list_tasks.assert_called_once_with(
        execution=303,
        mine=True,
        status="doing",
        opened_by="bob",
        page=2,
        page_size=50,
        fetch_all=True,
    )
    assert result == {
        "tasks": [
            {
                "id": 1,
                "name": "Fix login",
                "project": "",
                "status": "doing",
                "priority": "2",
                "deadline": "",
                "assigned_to": "alice",
                "opened_by": "",
            }
        ]
    }


def test_task_agent_resolves_me_for_opened_by(mocker):
    from zentao_agent import task_agent

    client = mocker.Mock()
    client.list_tasks.return_value = []
    mocker.patch("zentao_agent.task_agent.client_from_profile", return_value=client)
    mocker.patch("zentao_agent.task_agent.current_username", return_value="yangchangkun")

    result = task_agent.list_tasks(execution=303, opened_by="me")

    client.list_tasks.assert_called_once_with(
        execution=303,
        mine=False,
        status=None,
        opened_by="yangchangkun",
        page=1,
        page_size=100,
        fetch_all=False,
    )
    assert result == {"tasks": []}


def test_task_agent_gets_task_as_plain_dict(mocker):
    from zentao_agent import task_agent

    client = mocker.Mock()
    client.get_task.return_value = Task(id=9, name="Build import", status="wait", priority="3")
    mocker.patch("zentao_agent.task_agent.client_from_profile", return_value=client)

    result = task_agent.get_task(9)

    client.get_task.assert_called_once_with(9)
    assert result["task"]["id"] == 9
    assert result["task"]["name"] == "Build import"


def test_task_agent_creates_task_as_plain_dict(mocker):
    from zentao_agent import task_agent

    client = mocker.Mock()
    client.create_task.return_value = Task(id=9, name="Build import", status="wait", assigned_to="alice")
    mocker.patch("zentao_agent.task_agent.client_from_profile", return_value=client)

    result = task_agent.create_task(
        execution=303,
        name="Build import",
        est_started="2026-06-01",
        deadline="2026-06-05",
        story=789,
        task_type="devel",
        assigned_to="alice",
        estimate=2.5,
        pri=3,
        desc="Build import flow",
    )

    client.create_task.assert_called_once_with(
        execution=303,
        name="Build import",
        est_started="2026-06-01",
        deadline="2026-06-05",
        story=789,
        task_type="devel",
        assigned_to="alice",
        estimate=2.5,
        pri=3,
        desc="Build import flow",
    )
    assert result["task"]["id"] == 9
    assert result["task"]["assigned_to"] == "alice"


def test_task_agent_updates_task_as_plain_dict(mocker):
    from zentao_agent import task_agent

    client = mocker.Mock()
    client.update_task.return_value = Task(id=9, name="Build import v2", status="doing", priority="2")
    mocker.patch("zentao_agent.task_agent.client_from_profile", return_value=client)

    result = task_agent.update_task(
        task_id=9,
        name="Build import v2",
        status="doing",
        assigned_to="bob",
        estimate=3.5,
        deadline="2026-06-10",
        est_started="2026-06-02",
        pri=2,
        desc="Updated task body",
        task_type="test",
    )

    client.update_task.assert_called_once_with(
        task_id=9,
        name="Build import v2",
        status="doing",
        assigned_to="bob",
        estimate=3.5,
        deadline="2026-06-10",
        est_started="2026-06-02",
        pri=2,
        desc="Updated task body",
        task_type="test",
    )
    assert result["task"]["status"] == "doing"


def test_task_agent_deletes_task(mocker):
    from zentao_agent import task_agent

    client = mocker.Mock()
    client.delete_task.return_value = {"id": 9, "deleted": True}
    mocker.patch("zentao_agent.task_agent.client_from_profile", return_value=client)

    result = task_agent.delete_task(9)

    client.delete_task.assert_called_once_with(9)
    assert result == {"result": {"id": 9, "deleted": True}}


def test_task_agent_comments_on_task(mocker):
    from zentao_agent import task_agent

    client = mocker.Mock()
    mocker.patch("zentao_agent.task_agent.client_from_profile", return_value=client)

    result = task_agent.comment_task(task_id=9, content="Done")

    client.comment_task.assert_called_once_with(9, "Done")
    assert result == {"task": 9, "commented": True}


def test_task_agent_finishes_task_as_plain_dict(mocker):
    from zentao_agent import task_agent

    client = mocker.Mock()
    client.finish_task.return_value = Task(id=9, name="Build import", status="done")
    mocker.patch("zentao_agent.task_agent.client_from_profile", return_value=client)

    result = task_agent.finish_task(task_id=9, comment="Done")

    client.finish_task.assert_called_once_with(9, comment="Done")
    assert result["task"]["status"] == "done"


def test_task_agent_exposes_only_task_tools():
    from zentao_agent.task_agent import task_agent

    tool_names = [tool.__name__ for tool in task_agent.tools]

    assert tool_names == [
        "list_tasks",
        "get_task",
        "create_task",
        "update_task",
        "delete_task",
        "comment_task",
        "finish_task",
    ]


def test_task_tools_return_structured_errors(mocker):
    from zentao_agent import task_agent

    mocker.patch(
        "zentao_agent.task_agent.client_from_profile",
        side_effect=AuthError("Not logged in. Run: zentao login"),
    )

    assert task_agent.get_task(9) == {
        "error": "Not logged in. Run: zentao login"
    }


def test_root_agent_registers_bug_agent():
    from zentao_agent.agent import root_agent
    from zentao_agent.bug_agent import bug_agent

    assert bug_agent in root_agent.sub_agents
    assert root_agent.name == "root_agent"


def test_product_agent_lists_products_as_plain_dicts(mocker):
    from zentao_agent import product_agent

    client = mocker.Mock()
    client.list_products.return_value = [
        Product(id=16, name="Factory Design", code="P00402", status="normal", type="normal", owner="alice")
    ]
    mocker.patch("zentao_agent.product_agent.client_from_profile", return_value=client)

    result = product_agent.list_products(page=2, page_size=50, fetch_all=True)

    client.list_products.assert_called_once_with(page=2, page_size=50, fetch_all=True)
    assert result == {
        "products": [
            {
                "id": 16,
                "name": "Factory Design",
                "code": "P00402",
                "status": "normal",
                "type": "normal",
                "owner": "alice",
            }
        ]
    }


def test_product_agent_gets_product_as_plain_dict(mocker):
    from zentao_agent import product_agent

    client = mocker.Mock()
    client.get_product.return_value = Product(id=16, name="Factory Design", status="normal")
    mocker.patch("zentao_agent.product_agent.client_from_profile", return_value=client)

    result = product_agent.get_product(16)

    client.get_product.assert_called_once_with(16)
    assert result["product"]["id"] == 16
    assert result["product"]["name"] == "Factory Design"


def test_execution_agent_lists_project_executions_as_plain_dicts(mocker):
    from zentao_agent import execution_agent

    client = mocker.Mock()
    client.list_executions.return_value = [
        Execution(id=490, name="P00402-20260603", project="362", begin="2026-06-15"),
        Execution(id=492, name="P00402-20260604", project="362", begin="2026-06-22"),
    ]
    mocker.patch("zentao_agent.execution_agent.client_from_profile", return_value=client)

    result = execution_agent.list_project_executions(project_id=362, latest_only=True)

    client.list_executions.assert_called_once_with(project=362, fetch_all=True)
    assert result["executions"] == [
        {
            "id": 492,
            "name": "P00402-20260604",
            "project": "362",
            "status": "",
            "type": "",
            "begin": "2026-06-22",
            "end": "",
        }
    ]


def test_execution_agent_finds_latest_involved_execution(mocker):
    from zentao_agent import execution_agent

    client = mocker.Mock()
    client.list_projects.return_value = [
        Project(id=33, name="P03010-WIZ Resource"),
        Project(id=362, name="P00402-Youchao 3D Factory Design"),
    ]
    client.list_executions.return_value = [
        Execution(id=490, name="P00402-20260603", project="362", begin="2026-06-15"),
        Execution(id=492, name="P00402-20260604", project="362", begin="2026-06-22"),
    ]
    mocker.patch("zentao_agent.execution_agent.client_from_profile", return_value=client)

    result = execution_agent.find_latest_involved_execution(project_name="Youchao")

    client.list_projects.assert_called_once_with(involved=True, fetch_all=True)
    client.list_executions.assert_called_once_with(project=362, fetch_all=True)
    assert result["project"]["id"] == 362
    assert result["execution"]["id"] == 492


def test_project_agent_lists_projects_as_plain_dicts(mocker):
    from zentao_agent import project_agent

    client = mocker.Mock()
    client.list_projects.return_value = [
        Project(id=362, name="P00402-Youchao 3D Factory Design", status="doing", owner="wenjinlong")
    ]
    mocker.patch("zentao_agent.project_agent.client_from_profile", return_value=client)

    result = project_agent.list_projects(involved=True, page=2, page_size=50, fetch_all=True)

    client.list_projects.assert_called_once_with(page=2, page_size=50, fetch_all=True, involved=True)
    assert result == {
        "projects": [
            {
                "id": 362,
                "name": "P00402-Youchao 3D Factory Design",
                "code": "",
                "status": "doing",
                "model": "",
                "owner": "wenjinlong",
            }
        ]
    }


def test_project_agent_gets_project_as_plain_dict(mocker):
    from zentao_agent import project_agent

    client = mocker.Mock()
    client.get_project.return_value = Project(id=362, name="P00402-Youchao 3D Factory Design", status="doing")
    mocker.patch("zentao_agent.project_agent.client_from_profile", return_value=client)

    result = project_agent.get_project(362)

    client.get_project.assert_called_once_with(362)
    assert result["project"]["id"] == 362
    assert result["project"]["name"] == "P00402-Youchao 3D Factory Design"


def test_root_agent_registers_product_execution_and_bug_agents():
    from zentao_agent.agent import root_agent
    from zentao_agent.bug_agent import bug_agent
    from zentao_agent.execution_agent import execution_agent
    from zentao_agent.project_agent import project_agent
    from zentao_agent.product_agent import product_agent
    from zentao_agent.task_agent import task_agent

    assert project_agent in root_agent.sub_agents
    assert product_agent in root_agent.sub_agents
    assert execution_agent in root_agent.sub_agents
    assert task_agent in root_agent.sub_agents
    assert bug_agent in root_agent.sub_agents


def test_root_agent_describes_project_execution_bug_chain():
    from zentao_agent.agent import root_agent

    assert "project_agent" in root_agent.instruction
    assert "execution_agent" in root_agent.instruction
    assert "bug_agent" in root_agent.instruction
    assert "project_agent first" in root_agent.instruction
    assert "execution_agent second" in root_agent.instruction
    assert "bug_agent last" in root_agent.instruction


def test_root_agent_describes_project_execution_task_chain():
    from zentao_agent.agent import root_agent

    assert "task_agent" in root_agent.instruction
    assert "project_agent first" in root_agent.instruction
    assert "execution_agent second" in root_agent.instruction
    assert "task_agent last" in root_agent.instruction
