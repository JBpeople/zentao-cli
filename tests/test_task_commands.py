import json

from typer.testing import CliRunner

from zentao_cli.errors import AuthError
from zentao_cli.main import app
from zentao_cli.models import Task

runner = CliRunner()


def test_task_list_json(mocker):
    client = mocker.Mock()
    client.list_tasks.return_value = [
        Task(id=1, name="Fix login", status="doing", priority="2", assigned_to="alice")
    ]
    mocker.patch("zentao_cli.commands.task.client_from_profile", return_value=client)

    result = runner.invoke(app, ["task", "list", "--execution", "303", "--mine", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"][0]["name"] == "Fix login"
    client.list_tasks.assert_called_once_with(
        execution=303,
        mine=True,
        status=None,
        page=1,
        page_size=100,
        fetch_all=False,
    )


def test_task_list_filters_by_current_user_as_opened_by(mocker):
    client = mocker.Mock()
    client.list_tasks.return_value = [
        Task(id=1, name="Spec import", status="wait", priority="3", assigned_to="alice")
    ]
    mocker.patch("zentao_cli.commands.task.client_from_profile", return_value=client)
    mocker.patch("zentao_cli.commands.task.current_username", return_value="alice")

    result = runner.invoke(app, ["task", "list", "--execution", "303", "--opened-by", "me", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"][0]["name"] == "Spec import"
    client.list_tasks.assert_called_once_with(
        execution=303,
        mine=False,
        status=None,
        page=1,
        page_size=100,
        fetch_all=False,
        opened_by="alice",
    )


def test_task_list_passes_pagination_options(mocker):
    client = mocker.Mock()
    client.list_tasks.return_value = [
        Task(id=1, name="Fix login", status="doing", priority="2", assigned_to="alice")
    ]
    mocker.patch("zentao_cli.commands.task.client_from_profile", return_value=client)

    result = runner.invoke(
        app,
        ["task", "list", "--execution", "303", "--page", "2", "--page-size", "50", "--all", "--json"],
    )

    assert result.exit_code == 0
    client.list_tasks.assert_called_once_with(
        execution=303,
        mine=False,
        status=None,
        page=2,
        page_size=50,
        fetch_all=True,
    )


def test_task_list_requires_execution():
    result = runner.invoke(app, ["task", "list", "--json"])

    assert result.exit_code == 2
    assert "execution" in result.stderr.lower()


def test_task_list_json_auth_error(mocker):
    mocker.patch("zentao_cli.commands.task.client_from_profile", side_effect=AuthError("not logged in"))

    result = runner.invoke(app, ["task", "list", "--execution", "303", "--json"])

    assert result.exit_code == 1
    assert json.loads(result.stdout)["error"]["type"] == "AuthError"


def test_task_create_json(mocker):
    client = mocker.Mock()
    client.create_task.return_value = Task(id=9, name="Build import", status="wait", priority="3", assigned_to="alice")
    mocker.patch("zentao_cli.commands.task.client_from_profile", return_value=client)

    result = runner.invoke(
        app,
        [
            "task",
            "create",
            "--execution",
            "303",
            "--name",
            "Build import",
            "--est-started",
            "2026-06-01",
            "--deadline",
            "2026-06-05",
            "--type",
            "devel",
            "--assigned-to",
            "alice",
            "--estimate",
            "2.5",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"]["id"] == 9
    client.create_task.assert_called_once_with(
        execution=303,
        name="Build import",
        story=None,
        est_started="2026-06-01",
        task_type="devel",
        assigned_to="alice",
        estimate=2.5,
        deadline="2026-06-05",
        pri=3,
        desc=None,
    )


def test_task_create_with_story_json(mocker):
    client = mocker.Mock()
    client.create_task.return_value = Task(id=10, name="Build story", status="wait", priority="3")
    mocker.patch("zentao_cli.commands.task.client_from_profile", return_value=client)

    result = runner.invoke(
        app,
        [
            "task",
            "create",
            "--execution",
            "303",
            "--story",
            "789",
            "--name",
            "Build story",
            "--est-started",
            "2026-06-01",
            "--deadline",
            "2026-06-05",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"]["id"] == 10
    client.create_task.assert_called_once_with(
        execution=303,
        name="Build story",
        story=789,
        est_started="2026-06-01",
        task_type="devel",
        assigned_to=None,
        estimate=None,
        deadline="2026-06-05",
        pri=3,
        desc=None,
    )


def test_task_delete_json(mocker):
    client = mocker.Mock()
    client.delete_task.return_value = {"id": 9, "deleted": True}
    mocker.patch("zentao_cli.commands.task.client_from_profile", return_value=client)

    result = runner.invoke(app, ["task", "delete", "9", "--yes", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"] == {"id": 9, "deleted": True}
    client.delete_task.assert_called_once_with(9)


def test_task_delete_requires_confirmation(mocker):
    client = mocker.Mock()
    mocker.patch("zentao_cli.commands.task.client_from_profile", return_value=client)

    result = runner.invoke(app, ["task", "delete", "9"], input="n\n")

    assert result.exit_code == 1
    client.delete_task.assert_not_called()


def test_task_update_json(mocker):
    client = mocker.Mock()
    client.update_task.return_value = Task(id=9, name="Build import v2", status="doing", priority="2")
    mocker.patch("zentao_cli.commands.task.client_from_profile", return_value=client)

    result = runner.invoke(
        app,
        [
            "task",
            "update",
            "9",
            "--name",
            "Build import v2",
            "--status",
            "doing",
            "--assigned-to",
            "bob",
            "--estimate",
            "3.5",
            "--deadline",
            "2026-06-10",
            "--est-started",
            "2026-06-02",
            "--pri",
            "2",
            "--type",
            "test",
            "--desc",
            "Updated task body",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"]["name"] == "Build import v2"
    client.update_task.assert_called_once_with(
        task_id=9,
        name="Build import v2",
        status="doing",
        assigned_to="bob",
        estimate=3.5,
        deadline="2026-06-10",
        est_started="2026-06-02",
        pri=2,
        task_type="test",
        desc="Updated task body",
    )


def test_task_update_requires_at_least_one_field(mocker):
    client_from_profile = mocker.patch("zentao_cli.commands.task.client_from_profile")

    result = runner.invoke(app, ["task", "update", "9", "--json"])

    assert result.exit_code == 2
    client_from_profile.assert_not_called()
