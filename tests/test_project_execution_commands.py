import json

from typer.testing import CliRunner

from zentao_cli.main import app
from zentao_cli.models import Execution, Project

runner = CliRunner()


def test_project_list_json(mocker):
    client = mocker.Mock()
    client.list_projects.return_value = [
        Project(id=12, name="CRM Upgrade", code="CRM", status="doing", model="scrum", owner="alice")
    ]
    mocker.patch("zentao_cli.commands.project.client_from_profile", return_value=client)

    result = runner.invoke(app, ["project", "list", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"][0]["id"] == 12
    client.list_projects.assert_called_once_with(page=1, page_size=100, fetch_all=False)


def test_project_list_passes_pagination_options(mocker):
    client = mocker.Mock()
    client.list_projects.return_value = [
        Project(id=12, name="CRM Upgrade", code="CRM", status="doing", model="scrum", owner="alice")
    ]
    mocker.patch("zentao_cli.commands.project.client_from_profile", return_value=client)

    result = runner.invoke(app, ["project", "list", "--page", "3", "--page-size", "25", "--all", "--json"])

    assert result.exit_code == 0
    client.list_projects.assert_called_once_with(page=3, page_size=25, fetch_all=True)


def test_project_view_json(mocker):
    client = mocker.Mock()
    client.get_project.return_value = Project(id=12, name="CRM Upgrade", status="doing", owner="alice")
    mocker.patch("zentao_cli.commands.project.client_from_profile", return_value=client)

    result = runner.invoke(app, ["project", "view", "12", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"]["name"] == "CRM Upgrade"
    client.get_project.assert_called_once_with(12)


def test_execution_list_json(mocker):
    client = mocker.Mock()
    client.list_executions.return_value = [
        Execution(id=303, name="Sprint 1", project="CRM Upgrade", status="doing", type="sprint")
    ]
    mocker.patch("zentao_cli.commands.execution.client_from_profile", return_value=client)

    result = runner.invoke(app, ["execution", "list", "--project", "12", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"][0]["id"] == 303
    client.list_executions.assert_called_once_with(project=12, page=1, page_size=100, fetch_all=False)


def test_execution_list_passes_pagination_options(mocker):
    client = mocker.Mock()
    client.list_executions.return_value = [
        Execution(id=303, name="Sprint 1", project="CRM Upgrade", status="doing", type="sprint")
    ]
    mocker.patch("zentao_cli.commands.execution.client_from_profile", return_value=client)

    result = runner.invoke(
        app,
        ["execution", "list", "--project", "12", "--page", "2", "--page-size", "50", "--all", "--json"],
    )

    assert result.exit_code == 0
    client.list_executions.assert_called_once_with(project=12, page=2, page_size=50, fetch_all=True)


def test_execution_list_requires_project():
    result = runner.invoke(app, ["execution", "list", "--json"])

    assert result.exit_code == 2
    assert "project" in result.stderr.lower()


def test_execution_view_json(mocker):
    client = mocker.Mock()
    client.get_execution.return_value = Execution(id=303, name="Sprint 1", project="CRM Upgrade", status="doing")
    mocker.patch("zentao_cli.commands.execution.client_from_profile", return_value=client)

    result = runner.invoke(app, ["execution", "view", "303", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"]["name"] == "Sprint 1"
    client.get_execution.assert_called_once_with(303)


def test_execution_link_story_json(mocker):
    client = mocker.Mock()
    client.link_story.return_value = {"execution": 303, "story": 789, "linked": True}
    mocker.patch("zentao_cli.commands.execution.client_from_profile", return_value=client)

    result = runner.invoke(app, ["execution", "link-story", "303", "--story", "789", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"]["linked"] is True
    client.link_story.assert_called_once_with(execution_id=303, story_id=789)


def test_execution_link_story_text(mocker):
    client = mocker.Mock()
    client.link_story.return_value = {"execution": 303, "story": 789, "linked": True}
    mocker.patch("zentao_cli.commands.execution.client_from_profile", return_value=client)

    result = runner.invoke(app, ["execution", "link-story", "303", "--story", "789"])

    assert result.exit_code == 0
    assert "Linked story 789 to execution 303" in result.stdout
