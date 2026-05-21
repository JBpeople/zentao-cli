# Zentao CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI for Zentao Open Source Edition 21.7.5 focused on task workflows, with read-only bug/story commands and stable JSON output.

**Architecture:** The CLI uses Typer command groups, a `ZentaoClient` that encapsulates API v1 HTTP behavior, dataclass models that normalize raw API payloads, and a formatter layer for Rich table and JSON output. Configuration and session data are stored via `platformdirs`; command handlers do not construct API URLs directly.

**Tech Stack:** Python 3.11+, Typer, Rich, httpx, platformdirs, pytest, respx, pytest-mock.

---

## File Structure

- Create `pyproject.toml`: package metadata, dependencies, console script, pytest config.
- Create `README.md`: setup, login, common commands, JSON output examples.
- Create `src/zentao_cli/__init__.py`: package version.
- Create `src/zentao_cli/main.py`: Typer app entry point and command registration.
- Create `src/zentao_cli/config.py`: config directory resolution, TOML read/write, profile loading.
- Create `src/zentao_cli/auth.py`: interactive login and current session helpers.
- Create `src/zentao_cli/client.py`: API v1 HTTP client, request handling, login, task/bug/story methods.
- Create `src/zentao_cli/models.py`: normalized `Session`, `Task`, `Bug`, `Story`, and `User` dataclasses.
- Create `src/zentao_cli/formatters.py`: JSON output and Rich table helpers.
- Create `src/zentao_cli/errors.py`: exception hierarchy and JSON-safe error conversion.
- Create `src/zentao_cli/commands/__init__.py`: command package marker.
- Create `src/zentao_cli/commands/task.py`: task command group.
- Create `src/zentao_cli/commands/bug.py`: bug command group.
- Create `src/zentao_cli/commands/story.py`: story command group.
- Create `tests/conftest.py`: shared test fixtures.
- Create `tests/test_config.py`: config read/write tests.
- Create `tests/test_formatters.py`: JSON/table formatting tests.
- Create `tests/test_client.py`: mocked API client tests.
- Create `tests/test_task_commands.py`: Typer CLI task tests.
- Create `tests/test_readonly_commands.py`: bug/story command tests.

## Task 1: Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `src/zentao_cli/__init__.py`
- Create: `src/zentao_cli/main.py`
- Create: `src/zentao_cli/commands/__init__.py`
- Test: none

- [ ] **Step 1: Create package metadata**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "zentao-cli"
version = "0.1.0"
description = "Command-line client for Zentao Open Source Edition 21.7.5"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "httpx>=0.27,<1",
  "platformdirs>=4,<5",
  "rich>=13,<14",
  "typer>=0.12,<1",
]

[project.optional-dependencies]
dev = [
  "pytest>=8,<9",
  "pytest-mock>=3,<4",
  "respx>=0.21,<1",
]

[project.scripts]
zentao = "zentao_cli.main:app"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 2: Create package version**

Create `src/zentao_cli/__init__.py`:

```python
__version__ = "0.1.0"
```

- [ ] **Step 3: Create initial Typer app**

Create `src/zentao_cli/main.py`:

```python
from __future__ import annotations

import typer

from zentao_cli import __version__

app = typer.Typer(help="CLI for Zentao Open Source Edition 21.7.5.")


def version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show the zentao-cli version.",
    ),
) -> None:
    return None
```

- [ ] **Step 4: Create commands package marker**

Create `src/zentao_cli/commands/__init__.py`:

```python
"""Command groups for zentao-cli."""
```

- [ ] **Step 5: Verify CLI imports**

Run: `python -m zentao_cli.main --help`

Expected: command exits with code 0 and displays Typer help text.

## Task 2: Config Storage

**Files:**
- Create: `src/zentao_cli/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing config tests**

Create `tests/test_config.py`:

```python
from pathlib import Path

from zentao_cli.config import Profile, load_profile, save_profile


def test_save_and_load_default_profile(tmp_path: Path):
    path = tmp_path / "config.toml"
    profile = Profile(
        base_url="https://zentao.example.com",
        username="alice",
        session_name="zentaosid",
        session_id="abc123",
    )

    save_profile(profile, path=path)
    loaded = load_profile(path=path)

    assert loaded == profile


def test_load_missing_profile_returns_none(tmp_path: Path):
    assert load_profile(path=tmp_path / "missing.toml") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`

Expected: FAIL with `ModuleNotFoundError` or missing `Profile`.

- [ ] **Step 3: Implement config module**

Create `src/zentao_cli/config.py`:

```python
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_config_dir

APP_NAME = "zentao-cli"
DEFAULT_PROFILE = "default"


@dataclass(frozen=True)
class Profile:
    base_url: str
    username: str
    session_name: str
    session_id: str


def default_config_path() -> Path:
    return Path(user_config_dir(APP_NAME)) / "config.toml"


def load_profile(profile_name: str = DEFAULT_PROFILE, path: Path | None = None) -> Profile | None:
    config_path = path or default_config_path()
    if not config_path.exists():
        return None

    data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    raw_profile = data.get(profile_name)
    if not raw_profile:
        return None

    return Profile(
        base_url=raw_profile["base_url"],
        username=raw_profile["username"],
        session_name=raw_profile["session_name"],
        session_id=raw_profile["session_id"],
    )


def save_profile(profile: Profile, profile_name: str = DEFAULT_PROFILE, path: Path | None = None) -> None:
    config_path = path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        f"[{profile_name}]\n"
        f'base_url = "{profile.base_url}"\n'
        f'username = "{profile.username}"\n'
        f'session_name = "{profile.session_name}"\n'
        f'session_id = "{profile.session_id}"\n'
    )
    config_path.write_text(content, encoding="utf-8")
```

- [ ] **Step 4: Run config tests**

Run: `pytest tests/test_config.py -v`

Expected: PASS.

## Task 3: Errors And Formatters

**Files:**
- Create: `src/zentao_cli/errors.py`
- Create: `src/zentao_cli/formatters.py`
- Create: `tests/test_formatters.py`

- [ ] **Step 1: Write failing formatter tests**

Create `tests/test_formatters.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_formatters.py -v`

Expected: FAIL with missing modules.

- [ ] **Step 3: Implement errors**

Create `src/zentao_cli/errors.py`:

```python
from __future__ import annotations


class ZentaoCliError(Exception):
    """Base class for user-facing CLI errors."""


class AuthError(ZentaoCliError):
    """Raised when login state is missing, expired, or invalid."""


class ApiError(ZentaoCliError):
    """Raised when Zentao returns an API-level error."""


class NetworkError(ZentaoCliError):
    """Raised when the CLI cannot reach Zentao."""


class ConfigError(ZentaoCliError):
    """Raised when local configuration is missing or invalid."""


class NotFoundError(ZentaoCliError):
    """Raised when a requested Zentao resource does not exist."""
```

- [ ] **Step 4: Implement formatters**

Create `src/zentao_cli/formatters.py`:

```python
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any


def _to_plain(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [_to_plain(item) for item in value]
    if isinstance(value, tuple):
        return [_to_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_plain(item) for key, item in value.items()}
    return value


def json_payload(data: Any) -> str:
    return json.dumps({"ok": True, "data": _to_plain(data)}, ensure_ascii=False, indent=2)


def error_payload(error: Exception) -> str:
    return json.dumps(
        {
            "ok": False,
            "error": {"type": error.__class__.__name__, "message": str(error)},
        },
        ensure_ascii=False,
        indent=2,
    )
```

- [ ] **Step 5: Run formatter tests**

Run: `pytest tests/test_formatters.py -v`

Expected: PASS.

## Task 4: Models

**Files:**
- Create: `src/zentao_cli/models.py`
- Modify: `tests/test_formatters.py`

- [ ] **Step 1: Add model serialization test**

Append to `tests/test_formatters.py`:

```python
from zentao_cli.models import Task


def test_json_payload_serializes_task_dataclass():
    task = Task(
        id=1,
        name="Fix login",
        project="Core",
        status="doing",
        priority="2",
        deadline="2026-06-01",
        assigned_to="alice",
    )

    rendered = json_payload(task)

    assert json.loads(rendered)["data"]["name"] == "Fix login"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_formatters.py -v`

Expected: FAIL with missing `zentao_cli.models`.

- [ ] **Step 3: Implement normalized models**

Create `src/zentao_cli/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Session:
    session_name: str
    session_id: str


@dataclass(frozen=True)
class User:
    account: str
    realname: str = ""


@dataclass(frozen=True)
class Task:
    id: int
    name: str
    project: str = ""
    status: str = ""
    priority: str = ""
    deadline: str = ""
    assigned_to: str = ""

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "Task":
        return cls(
            id=int(payload.get("id", 0)),
            name=str(payload.get("name", "")),
            project=str(payload.get("projectName") or payload.get("project") or ""),
            status=str(payload.get("status", "")),
            priority=str(payload.get("pri") or payload.get("priority") or ""),
            deadline=str(payload.get("deadline", "")),
            assigned_to=str(payload.get("assignedTo") or payload.get("assigned_to") or ""),
        )


@dataclass(frozen=True)
class Bug:
    id: int
    title: str
    status: str = ""
    severity: str = ""
    assigned_to: str = ""

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "Bug":
        return cls(
            id=int(payload.get("id", 0)),
            title=str(payload.get("title", "")),
            status=str(payload.get("status", "")),
            severity=str(payload.get("severity", "")),
            assigned_to=str(payload.get("assignedTo") or payload.get("assigned_to") or ""),
        )


@dataclass(frozen=True)
class Story:
    id: int
    title: str
    status: str = ""
    stage: str = ""
    product: str = ""

    @classmethod
    def from_api(cls, payload: dict[str, Any]) -> "Story":
        return cls(
            id=int(payload.get("id", 0)),
            title=str(payload.get("title", "")),
            status=str(payload.get("status", "")),
            stage=str(payload.get("stage", "")),
            product=str(payload.get("productName") or payload.get("product") or ""),
        )
```

- [ ] **Step 4: Run formatter/model tests**

Run: `pytest tests/test_formatters.py -v`

Expected: PASS.

## Task 5: Zentao API Client

**Files:**
- Create: `src/zentao_cli/client.py`
- Create: `tests/test_client.py`

- [ ] **Step 1: Write failing client tests**

Create `tests/test_client.py`:

```python
import httpx
import respx

from zentao_cli.client import ZentaoClient
from zentao_cli.models import Task


@respx.mock
def test_login_parses_session():
    route = respx.post("https://zentao.example.com/api.php/v1/tokens").mock(
        return_value=httpx.Response(
            200,
            json={"token": "abc123", "sessionName": "zentaosid"},
        )
    )

    client = ZentaoClient("https://zentao.example.com")
    session = client.login("alice", "secret")

    assert route.called
    assert session.session_name == "zentaosid"
    assert session.session_id == "abc123"


@respx.mock
def test_list_tasks_returns_normalized_tasks():
    respx.get("https://zentao.example.com/api.php/v1/tasks").mock(
        return_value=httpx.Response(
            200,
            json={"tasks": [{"id": 1, "name": "Fix login", "status": "doing"}]},
        )
    )

    client = ZentaoClient("https://zentao.example.com", session_name="zentaosid", session_id="abc123")
    tasks = client.list_tasks(mine=True)

    assert tasks == [Task(id=1, name="Fix login", status="doing")]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_client.py -v`

Expected: FAIL with missing `ZentaoClient`.

- [ ] **Step 3: Implement API client**

Create `src/zentao_cli/client.py`:

```python
from __future__ import annotations

from typing import Any

import httpx

from zentao_cli.errors import ApiError, NetworkError
from zentao_cli.models import Bug, Session, Story, Task


class ZentaoClient:
    def __init__(
        self,
        base_url: str,
        session_name: str | None = None,
        session_id: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.session_name = session_name
        self.session_id = session_id
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}/api.php/v1/{path.lstrip('/')}"

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.session_id:
            headers["Token"] = self.session_id
        return headers

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = httpx.request(
                method,
                self._url(path),
                headers=self._headers(),
                timeout=self.timeout,
                **kwargs,
            )
        except httpx.HTTPError as exc:
            raise NetworkError(str(exc)) from exc

        if response.status_code >= 400:
            raise ApiError(f"Zentao API returned HTTP {response.status_code}")

        data = response.json()
        if isinstance(data, dict) and data.get("error"):
            raise ApiError(str(data["error"]))
        if not isinstance(data, dict):
            raise ApiError("Zentao API returned a non-object response")
        return data

    def login(self, username: str, password: str) -> Session:
        data = self._request("POST", "tokens", json={"account": username, "password": password})
        session_id = str(data.get("token") or data.get("sessionID") or data.get("session_id") or "")
        session_name = str(data.get("sessionName") or data.get("session_name") or "zentaosid")
        if not session_id:
            raise ApiError("Zentao login response did not include a session token")
        return Session(session_name=session_name, session_id=session_id)

    def list_tasks(self, mine: bool = False, status: str | None = None, project: int | None = None) -> list[Task]:
        params: dict[str, Any] = {}
        if mine:
            params["mine"] = 1
        if status:
            params["status"] = status
        if project is not None:
            params["project"] = project
        data = self._request("GET", "tasks", params=params)
        raw_tasks = data.get("tasks") or data.get("data") or []
        return [Task.from_api(item) for item in raw_tasks]

    def get_task(self, task_id: int) -> Task:
        data = self._request("GET", f"tasks/{task_id}")
        return Task.from_api(data.get("task") or data.get("data") or data)

    def update_task_status(self, task_id: int, status: str) -> Task:
        data = self._request("PUT", f"tasks/{task_id}", json={"status": status})
        return Task.from_api(data.get("task") or data.get("data") or data)

    def comment_task(self, task_id: int, content: str) -> None:
        self._request("POST", f"tasks/{task_id}/comments", json={"content": content})

    def finish_task(self, task_id: int, comment: str | None = None) -> Task:
        payload: dict[str, Any] = {}
        if comment:
            payload["comment"] = comment
        data = self._request("POST", f"tasks/{task_id}/finish", json=payload)
        return Task.from_api(data.get("task") or data.get("data") or data)

    def list_bugs(self, assigned_to: str | None = None, status: str | None = None) -> list[Bug]:
        params = {"assignedTo": assigned_to, "status": status}
        data = self._request("GET", "bugs", params={k: v for k, v in params.items() if v})
        raw_bugs = data.get("bugs") or data.get("data") or []
        return [Bug.from_api(item) for item in raw_bugs]

    def get_bug(self, bug_id: int) -> Bug:
        data = self._request("GET", f"bugs/{bug_id}")
        return Bug.from_api(data.get("bug") or data.get("data") or data)

    def list_stories(self, product: int | None = None, status: str | None = None) -> list[Story]:
        params: dict[str, Any] = {}
        if product is not None:
            params["product"] = product
        if status:
            params["status"] = status
        data = self._request("GET", "stories", params=params)
        raw_stories = data.get("stories") or data.get("data") or []
        return [Story.from_api(item) for item in raw_stories]

    def get_story(self, story_id: int) -> Story:
        data = self._request("GET", f"stories/{story_id}")
        return Story.from_api(data.get("story") or data.get("data") or data)
```

- [ ] **Step 4: Run client tests**

Run: `pytest tests/test_client.py -v`

Expected: PASS.

## Task 6: Auth Commands

**Files:**
- Create: `src/zentao_cli/auth.py`
- Modify: `src/zentao_cli/main.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write shared CLI fixture**

Create `tests/conftest.py`:

```python
from typer.testing import CliRunner


runner = CliRunner()
```

- [ ] **Step 2: Implement auth helpers**

Create `src/zentao_cli/auth.py`:

```python
from __future__ import annotations

from getpass import getpass

import typer

from zentao_cli.client import ZentaoClient
from zentao_cli.config import Profile, load_profile, save_profile
from zentao_cli.errors import AuthError


def require_profile() -> Profile:
    profile = load_profile()
    if profile is None:
        raise AuthError("Not logged in. Run: zentao login")
    return profile


def client_from_profile() -> ZentaoClient:
    profile = require_profile()
    return ZentaoClient(
        profile.base_url,
        session_name=profile.session_name,
        session_id=profile.session_id,
    )


def login_interactive() -> None:
    base_url = typer.prompt("Zentao URL")
    username = typer.prompt("Username")
    password = getpass("Password: ")
    client = ZentaoClient(base_url)
    session = client.login(username, password)
    save_profile(
        Profile(
            base_url=base_url,
            username=username,
            session_name=session.session_name,
            session_id=session.session_id,
        )
    )
    typer.echo(f"Logged in as {username}")
```

- [ ] **Step 3: Register auth commands in main app**

Replace `src/zentao_cli/main.py` with:

```python
from __future__ import annotations

import typer

from zentao_cli import __version__
from zentao_cli.auth import login_interactive, require_profile

app = typer.Typer(help="CLI for Zentao Open Source Edition 21.7.5.")


def version_callback(value: bool) -> None:
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show the zentao-cli version.",
    ),
) -> None:
    return None


@app.command()
def login() -> None:
    login_interactive()


@app.command()
def whoami() -> None:
    profile = require_profile()
    typer.echo(profile.username)
```

- [ ] **Step 4: Verify CLI help includes auth commands**

Run: `python -m zentao_cli.main --help`

Expected: command list includes `login` and `whoami`.

## Task 7: Task Commands

**Files:**
- Create: `src/zentao_cli/commands/task.py`
- Modify: `src/zentao_cli/main.py`
- Create: `tests/test_task_commands.py`

- [ ] **Step 1: Write failing task command test**

Create `tests/test_task_commands.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_task_commands.py -v`

Expected: FAIL because `task` command is not registered.

- [ ] **Step 3: Implement task command group**

Create `src/zentao_cli/commands/task.py`:

```python
from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from zentao_cli.auth import client_from_profile
from zentao_cli.formatters import json_payload
from zentao_cli.models import Task

app = typer.Typer(help="Task commands.")
console = Console()


def _task_table(tasks: list[Task]) -> Table:
    table = Table(title="Tasks")
    table.add_column("ID", justify="right")
    table.add_column("Title")
    table.add_column("Project")
    table.add_column("Status")
    table.add_column("Pri")
    table.add_column("Deadline")
    table.add_column("Assignee")
    for task in tasks:
        table.add_row(
            str(task.id),
            task.name,
            task.project,
            task.status,
            task.priority,
            task.deadline,
            task.assigned_to,
        )
    return table


@app.command("list")
def list_tasks(
    mine: bool = typer.Option(False, "--mine", help="Only show tasks assigned to current user."),
    status: str | None = typer.Option(None, "--status", help="Filter by task status."),
    project: int | None = typer.Option(None, "--project", help="Filter by project ID."),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    client = client_from_profile()
    tasks = client.list_tasks(mine=mine, status=status, project=project)
    if as_json:
        typer.echo(json_payload(tasks))
    else:
        console.print(_task_table(tasks))


@app.command("view")
def view_task(task_id: int, as_json: bool = typer.Option(False, "--json", help="Output JSON.")) -> None:
    client = client_from_profile()
    task = client.get_task(task_id)
    if as_json:
        typer.echo(json_payload(task))
    else:
        console.print(_task_table([task]))


@app.command("update")
def update_task(task_id: int, status: str = typer.Option(..., "--status")) -> None:
    client = client_from_profile()
    task = client.update_task_status(task_id, status)
    typer.echo(f"Updated task {task.id} to {task.status}")


@app.command("comment")
def comment_task(task_id: int, content: str) -> None:
    client = client_from_profile()
    client.comment_task(task_id, content)
    typer.echo(f"Commented on task {task_id}")


@app.command("finish")
def finish_task(task_id: int, comment: str | None = typer.Option(None, "--comment")) -> None:
    client = client_from_profile()
    task = client.finish_task(task_id, comment=comment)
    typer.echo(f"Finished task {task.id}")
```

- [ ] **Step 4: Register task group**

Add to `src/zentao_cli/main.py` imports:

```python
from zentao_cli.commands import task
```

Add after app creation:

```python
app.add_typer(task.app, name="task")
```

- [ ] **Step 5: Run task command tests**

Run: `pytest tests/test_task_commands.py -v`

Expected: PASS.

## Task 8: Read-Only Bug And Story Commands

**Files:**
- Create: `src/zentao_cli/commands/bug.py`
- Create: `src/zentao_cli/commands/story.py`
- Modify: `src/zentao_cli/main.py`
- Create: `tests/test_readonly_commands.py`

- [ ] **Step 1: Write failing read-only command tests**

Create `tests/test_readonly_commands.py`:

```python
import json

from typer.testing import CliRunner

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
    client.list_bugs.assert_called_once_with(assigned_to="me", status=None)


def test_story_list_json(mocker):
    client = mocker.Mock()
    client.list_stories.return_value = [Story(id=8, title="Login story", status="active")]
    mocker.patch("zentao_cli.commands.story.client_from_profile", return_value=client)

    result = runner.invoke(app, ["story", "list", "--product", "2", "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"][0]["title"] == "Login story"
    client.list_stories.assert_called_once_with(product=2, status=None)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_readonly_commands.py -v`

Expected: FAIL because `bug` and `story` command groups are not registered.

- [ ] **Step 3: Implement bug command group**

Create `src/zentao_cli/commands/bug.py`:

```python
from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from zentao_cli.auth import client_from_profile
from zentao_cli.formatters import json_payload
from zentao_cli.models import Bug

app = typer.Typer(help="Bug commands.")
console = Console()


def _bug_table(bugs: list[Bug]) -> Table:
    table = Table(title="Bugs")
    table.add_column("ID", justify="right")
    table.add_column("Title")
    table.add_column("Status")
    table.add_column("Severity")
    table.add_column("Assignee")
    for bug in bugs:
        table.add_row(str(bug.id), bug.title, bug.status, bug.severity, bug.assigned_to)
    return table


@app.command("list")
def list_bugs(
    assigned_to: str | None = typer.Option(None, "--assigned-to"),
    status: str | None = typer.Option(None, "--status"),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    client = client_from_profile()
    bugs = client.list_bugs(assigned_to=assigned_to, status=status)
    if as_json:
        typer.echo(json_payload(bugs))
    else:
        console.print(_bug_table(bugs))


@app.command("view")
def view_bug(bug_id: int, as_json: bool = typer.Option(False, "--json", help="Output JSON.")) -> None:
    client = client_from_profile()
    bug = client.get_bug(bug_id)
    if as_json:
        typer.echo(json_payload(bug))
    else:
        console.print(_bug_table([bug]))
```

- [ ] **Step 4: Implement story command group**

Create `src/zentao_cli/commands/story.py`:

```python
from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from zentao_cli.auth import client_from_profile
from zentao_cli.formatters import json_payload
from zentao_cli.models import Story

app = typer.Typer(help="Story commands.")
console = Console()


def _story_table(stories: list[Story]) -> Table:
    table = Table(title="Stories")
    table.add_column("ID", justify="right")
    table.add_column("Title")
    table.add_column("Product")
    table.add_column("Status")
    table.add_column("Stage")
    for story in stories:
        table.add_row(str(story.id), story.title, story.product, story.status, story.stage)
    return table


@app.command("list")
def list_stories(
    product: int | None = typer.Option(None, "--product"),
    status: str | None = typer.Option(None, "--status"),
    as_json: bool = typer.Option(False, "--json", help="Output JSON."),
) -> None:
    client = client_from_profile()
    stories = client.list_stories(product=product, status=status)
    if as_json:
        typer.echo(json_payload(stories))
    else:
        console.print(_story_table(stories))


@app.command("view")
def view_story(story_id: int, as_json: bool = typer.Option(False, "--json", help="Output JSON.")) -> None:
    client = client_from_profile()
    story = client.get_story(story_id)
    if as_json:
        typer.echo(json_payload(story))
    else:
        console.print(_story_table([story]))
```

- [ ] **Step 5: Register bug and story groups**

Add to `src/zentao_cli/main.py` imports:

```python
from zentao_cli.commands import bug, story, task
```

Ensure command registration includes:

```python
app.add_typer(task.app, name="task")
app.add_typer(bug.app, name="bug")
app.add_typer(story.app, name="story")
```

- [ ] **Step 6: Run read-only command tests**

Run: `pytest tests/test_readonly_commands.py -v`

Expected: PASS.

## Task 9: User-Facing Error Handling

**Files:**
- Modify: `src/zentao_cli/main.py`
- Modify: `tests/test_task_commands.py`

- [ ] **Step 1: Add error handling test**

Append to `tests/test_task_commands.py`:

```python
from zentao_cli.errors import AuthError


def test_task_list_json_auth_error(mocker):
    mocker.patch("zentao_cli.commands.task.client_from_profile", side_effect=AuthError("not logged in"))

    result = runner.invoke(app, ["task", "list", "--json"])

    assert result.exit_code == 1
    assert json.loads(result.stdout)["error"]["type"] == "AuthError"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_task_commands.py::test_task_list_json_auth_error -v`

Expected: FAIL because the exception is not converted to JSON.

- [ ] **Step 3: Add command-level error handling helper to task commands**

Modify `src/zentao_cli/commands/task.py` by importing:

```python
from zentao_cli.errors import ZentaoCliError
from zentao_cli.formatters import error_payload, json_payload
```

Replace `list_tasks` body with:

```python
    try:
        client = client_from_profile()
        tasks = client.list_tasks(mine=mine, status=status, project=project)
    except ZentaoCliError as exc:
        if as_json:
            typer.echo(error_payload(exc))
        else:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    if as_json:
        typer.echo(json_payload(tasks))
    else:
        console.print(_task_table(tasks))
```

- [ ] **Step 4: Run error handling test**

Run: `pytest tests/test_task_commands.py::test_task_list_json_auth_error -v`

Expected: PASS.

- [ ] **Step 5: Apply same error handling pattern to `view`, `update`, `comment`, and `finish`**

For commands without `--json`, catch `ZentaoCliError`, print `str(exc)` to stderr, and exit 1. For `view --json`, emit `error_payload(exc)`.

- [ ] **Step 6: Run all tests**

Run: `pytest -v`

Expected: PASS.

## Task 10: README And Smoke Test Notes

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create README**

Create `README.md`:

````markdown
# zentao-cli

Python CLI for Zentao Open Source Edition 21.7.5.

## Install for development

```bash
pip install -e ".[dev]"
```

## Login

```bash
zentao login
```

The CLI stores session data in the OS-specific user config directory. It does not store the plaintext password.

## Common commands

```bash
zentao whoami
zentao task list --mine
zentao task view 123
zentao task update 123 --status doing
zentao task comment 123 "Checked locally"
zentao task finish 123 --comment "Done"
zentao bug list --assigned-to me --status active
zentao story list --product 1 --status active
```

## JSON output

```bash
zentao task list --mine --json
```

Successful JSON output:

```json
{
  "ok": true,
  "data": []
}
```

Error JSON output:

```json
{
  "ok": false,
  "error": {
    "type": "AuthError",
    "message": "not logged in"
  }
}
```

## Manual smoke test

Against a Zentao Open Source Edition 21.7.5 server:

1. Run `zentao login`.
2. Run `zentao whoami`.
3. Run `zentao task list --mine`.
4. Run `zentao task list --mine --json`.
5. Run `zentao bug list --assigned-to me --json`.
6. Run `zentao story list --json`.
````

- [ ] **Step 2: Run complete test suite**

Run: `pytest -v`

Expected: PASS.

- [ ] **Step 3: Verify CLI help**

Run: `python -m zentao_cli.main --help`

Expected: command list includes `login`, `whoami`, `task`, `bug`, and `story`.

## Self-Review

- Spec coverage: tasks are primary; bugs and stories are read-only; interactive login; table and JSON output; config/session storage; error hierarchy; tests with mocked HTTP are all covered.
- Placeholder scan: no `TBD`, `TODO`, `implement later`, or unspecified "add tests" steps remain.
- Type consistency: `Profile`, `Session`, `Task`, `Bug`, `Story`, `ZentaoClient`, and command method names are introduced before use and used consistently.
