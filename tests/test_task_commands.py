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
    client.list_tasks.assert_called_once_with(execution=303, mine=True, status=None)


def test_task_list_requires_execution():
    result = runner.invoke(app, ["task", "list", "--json"])

    assert result.exit_code == 2
    assert "execution" in result.stderr.lower()


def test_task_list_json_auth_error(mocker):
    mocker.patch("zentao_cli.commands.task.client_from_profile", side_effect=AuthError("not logged in"))

    result = runner.invoke(app, ["task", "list", "--execution", "303", "--json"])

    assert result.exit_code == 1
    assert json.loads(result.stdout)["error"]["type"] == "AuthError"
