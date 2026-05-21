import json

from typer.testing import CliRunner

from zentao_cli.errors import ApiError
from zentao_cli.main import app
from zentao_cli.models import Bug, Story

runner = CliRunner()


def test_bug_list_json(mocker):
    client = mocker.Mock()
    client.list_bugs.return_value = [Bug(id=5, title="Crash", status="active", assigned_to="alice")]
    mocker.patch("zentao_cli.commands.bug.client_from_profile", return_value=client)

    result = runner.invoke(app, ["bug", "list", "--assigned-to", "me", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"][0]["title"] == "Crash"
    client.list_bugs.assert_called_once_with(product=None, assigned_to="me", status=None)


def test_story_list_json(mocker):
    client = mocker.Mock()
    client.list_stories.return_value = [Story(id=8, title="Login story", status="active")]
    mocker.patch("zentao_cli.commands.story.client_from_profile", return_value=client)

    result = runner.invoke(app, ["story", "list", "--product", "2", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"][0]["title"] == "Login story"
    client.list_stories.assert_called_once_with(product=2, status=None)


def test_bug_list_json_api_error(mocker):
    client = mocker.Mock()
    client.list_bugs.side_effect = ApiError("Need product id.")
    mocker.patch("zentao_cli.commands.bug.client_from_profile", return_value=client)

    result = runner.invoke(app, ["bug", "list", "--json"])

    assert result.exit_code == 1
    assert json.loads(result.stdout)["error"]["message"] == "Need product id."
