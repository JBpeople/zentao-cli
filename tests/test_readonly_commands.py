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

    result = runner.invoke(app, ["bug", "list", "--execution", "303", "--assigned-to", "me", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"][0]["title"] == "Crash"
    client.list_bugs.assert_called_once_with(
        execution=303,
        assigned_to="me",
        status=None,
        page=1,
        page_size=100,
        fetch_all=False,
    )


def test_bug_list_passes_pagination_options(mocker):
    client = mocker.Mock()
    client.list_bugs.return_value = [Bug(id=5, title="Crash", status="active", assigned_to="alice")]
    mocker.patch("zentao_cli.commands.bug.client_from_profile", return_value=client)

    result = runner.invoke(
        app,
        ["bug", "list", "--execution", "303", "--page", "2", "--page-size", "50", "--all", "--json"],
    )

    assert result.exit_code == 0
    client.list_bugs.assert_called_once_with(
        execution=303,
        assigned_to=None,
        status=None,
        page=2,
        page_size=50,
        fetch_all=True,
    )


def test_bug_list_requires_execution():
    result = runner.invoke(app, ["bug", "list", "--json"])

    assert result.exit_code == 2
    assert "execution" in result.stderr.lower()


def test_story_list_json(mocker):
    client = mocker.Mock()
    client.list_stories.return_value = [Story(id=8, title="Login story", status="active")]
    mocker.patch("zentao_cli.commands.story.client_from_profile", return_value=client)

    result = runner.invoke(app, ["story", "list", "--product", "2", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"][0]["title"] == "Login story"
    client.list_stories.assert_called_once_with(product=2, status=None, page=1, page_size=100, fetch_all=False)


def test_story_list_by_execution_json(mocker):
    client = mocker.Mock()
    client.list_stories.return_value = [Story(id=8, title="Login story", status="active")]
    mocker.patch("zentao_cli.commands.story.client_from_profile", return_value=client)

    result = runner.invoke(app, ["story", "list", "--execution", "303", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"][0]["title"] == "Login story"
    client.list_stories.assert_called_once_with(execution=303, status=None, page=1, page_size=100, fetch_all=False)


def test_story_list_passes_pagination_options(mocker):
    client = mocker.Mock()
    client.list_stories.return_value = [Story(id=8, title="Login story", status="active")]
    mocker.patch("zentao_cli.commands.story.client_from_profile", return_value=client)

    result = runner.invoke(
        app,
        ["story", "list", "--execution", "303", "--page", "2", "--page-size", "50", "--all", "--json"],
    )

    assert result.exit_code == 0
    client.list_stories.assert_called_once_with(
        execution=303,
        status=None,
        page=2,
        page_size=50,
        fetch_all=True,
    )


def test_story_list_rejects_product_and_execution_together(mocker):
    client_from_profile = mocker.patch("zentao_cli.commands.story.client_from_profile")

    result = runner.invoke(app, ["story", "list", "--product", "2", "--execution", "303", "--json"])

    assert result.exit_code == 2
    assert "either --product or --execution" in result.stderr.lower()
    client_from_profile.assert_not_called()


def test_story_create_json(mocker):
    client = mocker.Mock()
    client.create_story.return_value = Story(id=42, title="Improve onboarding", status="active")
    mocker.patch("zentao_cli.commands.story.client_from_profile", return_value=client)

    result = runner.invoke(
        app,
        [
            "story",
            "create",
            "--product",
            "5",
            "--title",
            "Improve onboarding",
            "--spec",
            "As a user, I can finish onboarding.",
            "--verify",
            "Dashboard is shown.",
            "--pri",
            "2",
            "--category",
            "feature",
            "--status",
            "draft",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"]["id"] == 42
    client.create_story.assert_called_once_with(
        product=5,
        execution=None,
        title="Improve onboarding",
        spec="As a user, I can finish onboarding.",
        verify="Dashboard is shown.",
        pri=2,
        category="feature",
        status="draft",
    )


def test_story_create_by_execution_json(mocker):
    client = mocker.Mock()
    client.create_story.return_value = Story(id=42, title="Improve onboarding", status="active")
    mocker.patch("zentao_cli.commands.story.client_from_profile", return_value=client)

    result = runner.invoke(
        app,
        [
            "story",
            "create",
            "--execution",
            "303",
            "--title",
            "Improve onboarding",
            "--spec",
            "As a user, I can finish onboarding.",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"]["id"] == 42
    client.create_story.assert_called_once_with(
        product=None,
        execution=303,
        title="Improve onboarding",
        spec="As a user, I can finish onboarding.",
        verify=None,
        pri=3,
        category="feature",
        status="draft",
    )


def test_story_create_requires_product_or_execution_title_and_spec():
    result = runner.invoke(app, ["story", "create", "--title", "Missing scope", "--spec", "Missing scope", "--json"])
    assert result.exit_code == 2
    assert "product" in result.stderr.lower()
    assert "execution" in result.stderr.lower()

    result = runner.invoke(app, ["story", "create", "--product", "5", "--json"])
    assert result.exit_code == 2
    assert "title" in result.stderr.lower()

    result = runner.invoke(app, ["story", "create", "--product", "5", "--title", "Missing spec", "--json"])
    assert result.exit_code == 2
    assert "spec" in result.stderr.lower()


def test_story_change_json(mocker):
    client = mocker.Mock()
    client.change_story.return_value = Story(id=42, title="Improve onboarding v2", status="active")
    mocker.patch("zentao_cli.commands.story.client_from_profile", return_value=client)

    result = runner.invoke(
        app,
        [
            "story",
            "change",
            "42",
            "--title",
            "Improve onboarding v2",
            "--spec",
            "Updated body",
            "--verify",
            "Updated verify",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"]["title"] == "Improve onboarding v2"
    client.change_story.assert_called_once_with(
        story_id=42,
        title="Improve onboarding v2",
        spec="Updated body",
        verify="Updated verify",
    )


def test_story_update_json(mocker):
    client = mocker.Mock()
    client.update_story.return_value = Story(id=42, title="Improve onboarding v3", status="active")
    mocker.patch("zentao_cli.commands.story.client_from_profile", return_value=client)

    result = runner.invoke(
        app,
        [
            "story",
            "update",
            "42",
            "--title",
            "Improve onboarding v3",
            "--spec",
            "Updated body",
            "--verify",
            "Updated verify",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"]["title"] == "Improve onboarding v3"
    client.update_story.assert_called_once_with(
        story_id=42,
        title="Improve onboarding v3",
        spec="Updated body",
        verify="Updated verify",
    )


def test_story_delete_json(mocker):
    client = mocker.Mock()
    client.delete_story.return_value = {"id": 42, "deleted": True}
    mocker.patch("zentao_cli.commands.story.client_from_profile", return_value=client)

    result = runner.invoke(app, ["story", "delete", "42", "--yes", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"] == {"id": 42, "deleted": True}
    client.delete_story.assert_called_once_with(42)


def test_story_delete_requires_confirmation(mocker):
    client = mocker.Mock()
    mocker.patch("zentao_cli.commands.story.client_from_profile", return_value=client)

    result = runner.invoke(app, ["story", "delete", "42"], input="n\n")

    assert result.exit_code == 1
    client.delete_story.assert_not_called()


def test_bug_list_json_api_error(mocker):
    client = mocker.Mock()
    client.list_bugs.side_effect = ApiError("Need execution id.")
    mocker.patch("zentao_cli.commands.bug.client_from_profile", return_value=client)

    result = runner.invoke(app, ["bug", "list", "--execution", "303", "--json"])

    assert result.exit_code == 1
    assert json.loads(result.stdout)["error"]["message"] == "Need execution id."


def test_bug_create_json(mocker):
    client = mocker.Mock()
    client.create_bug.return_value = Bug(id=7, title="Crash on import", status="active", severity="3")
    mocker.patch("zentao_cli.commands.bug.client_from_profile", return_value=client)

    result = runner.invoke(
        app,
        [
            "bug",
            "create",
            "--execution",
            "303",
            "--title",
            "Crash on import",
            "--steps",
            "Open import and click submit.",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"]["id"] == 7
    client.create_bug.assert_called_once_with(
        execution=303,
        product=None,
        title="Crash on import",
        steps="Open import and click submit.",
        severity=3,
        pri=3,
        bug_type="codeerror",
        assigned_to=None,
        opened_build="trunk",
        deadline=None,
    )


def test_bug_update_json(mocker):
    client = mocker.Mock()
    client.update_bug.return_value = Bug(id=7, title="Crash on import v2", status="active", severity="2")
    mocker.patch("zentao_cli.commands.bug.client_from_profile", return_value=client)

    result = runner.invoke(
        app,
        [
            "bug",
            "update",
            "7",
            "--title",
            "Crash on import v2",
            "--steps",
            "Updated steps",
            "--severity",
            "2",
            "--pri",
            "1",
            "--type",
            "config",
            "--assigned-to",
            "bob",
            "--deadline",
            "2026-06-10",
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"]["title"] == "Crash on import v2"
    client.update_bug.assert_called_once_with(
        bug_id=7,
        title="Crash on import v2",
        steps="Updated steps",
        severity=2,
        pri=1,
        bug_type="config",
        assigned_to="bob",
        deadline="2026-06-10",
    )


def test_bug_update_requires_at_least_one_field(mocker):
    client_from_profile = mocker.patch("zentao_cli.commands.bug.client_from_profile")

    result = runner.invoke(app, ["bug", "update", "7", "--json"])

    assert result.exit_code == 2
    client_from_profile.assert_not_called()


def test_bug_delete_json(mocker):
    client = mocker.Mock()
    client.delete_bug.return_value = {"id": 7, "deleted": True}
    mocker.patch("zentao_cli.commands.bug.client_from_profile", return_value=client)

    result = runner.invoke(app, ["bug", "delete", "7", "--yes", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"] == {"id": 7, "deleted": True}
    client.delete_bug.assert_called_once_with(7)


def test_bug_delete_requires_confirmation(mocker):
    client = mocker.Mock()
    mocker.patch("zentao_cli.commands.bug.client_from_profile", return_value=client)

    result = runner.invoke(app, ["bug", "delete", "7"], input="n\n")

    assert result.exit_code == 1
    client.delete_bug.assert_not_called()


def test_story_list_requires_product():
    result = runner.invoke(app, ["story", "list", "--json"])

    assert result.exit_code == 2
    assert "product" in result.stderr.lower()
    assert "execution" in result.stderr.lower()
