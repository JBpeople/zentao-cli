import json

from typer.testing import CliRunner

from zentao_cli.main import app
from zentao_cli.models import Task

runner = CliRunner()


def test_task_list_json(mocker):
    client = mocker.Mock()
    client.list_tasks.return_value = [
        Task(id=1, name="Fix login", status="doing", priority="2", assigned_to="alice")
    ]
    mocker.patch("zentao_cli.commands.task.client_from_profile", return_value=client)

    result = runner.invoke(app, ["task", "list", "--mine", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"][0]["name"] == "Fix login"
    client.list_tasks.assert_called_once_with(mine=True, status=None, project=None)
