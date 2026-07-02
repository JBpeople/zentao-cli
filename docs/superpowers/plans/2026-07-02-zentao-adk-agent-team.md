# Zentao ADK Agent Team Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a first-stage Google ADK agent team where `root_agent` routes bug requests to a read-only `bug_agent`.

**Architecture:** Keep Zentao API access in the existing `zentao_cli` client/auth layer. Add thin ADK tools in `zentao_agent/bug_agent.py` that return JSON-compatible dictionaries, and compose them under `root_agent` through ADK `sub_agents`.

**Tech Stack:** Python 3.11+, Google ADK `LlmAgent`, ADK `LiteLlm`, pytest, pytest-mock, existing `zentao_cli` client/auth/model modules.

---

## File Structure

- Create: `zentao_agent/model.py`
  - Owns shared LiteLLM construction for all ADK agents.
  - Reads `ZENTAO_AGENT_MODEL`, `OPENAI_BASE_URL`, and `OPENAI_API_KEY`.
- Modify: `zentao_agent/bug_agent.py`
  - Owns read-only bug tool functions and the `bug_agent` definition.
- Modify: `zentao_agent/agent.py`
  - Owns `root_agent` composition and routing instructions.
- Modify: `zentao_agent/__init__.py`
  - Keep import behavior simple and compatible with ADK discovery.
- Modify: `pyproject.toml`
  - Include `zentao_agent` in Hatch build packages.
- Create: `tests/test_zentao_agent.py`
  - Tests bug tool behavior and root team composition with mocked Zentao client calls.

## Task 1: Add Failing Tests For Bug Agent Tools

**Files:**
- Create: `tests/test_zentao_agent.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_zentao_agent.py` with this content:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/test_zentao_agent.py -v
```

Expected: FAIL because `zentao_agent.bug_agent` does not define `list_bugs`, `get_bug`, or a real `bug_agent` yet.

- [ ] **Step 3: Commit failing tests**

Run:

```bash
git add tests/test_zentao_agent.py
git commit -m "test: cover zentao bug agent tools"
```

## Task 2: Implement Shared Model Factory And Bug Agent

**Files:**
- Create: `zentao_agent/model.py`
- Modify: `zentao_agent/bug_agent.py`

- [ ] **Step 1: Add shared model factory**

Create `zentao_agent/model.py`:

```python
from __future__ import annotations

import os

from google.adk.models.lite_llm import LiteLlm

DEFAULT_MODEL = "openai/deepseek-ai/deepseek-v4-flash"


def zentao_model() -> LiteLlm:
    """Build the shared LiteLLM model used by Zentao ADK agents."""
    kwargs: dict[str, str] = {
        "model": os.getenv("ZENTAO_AGENT_MODEL", DEFAULT_MODEL),
    }
    api_base = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    if api_base:
        kwargs["api_base"] = api_base
    if api_key:
        kwargs["api_key"] = api_key
    return LiteLlm(**kwargs)
```

- [ ] **Step 2: Implement `bug_agent.py`**

Replace `zentao_agent/bug_agent.py` with:

```python
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from google.adk.agents import LlmAgent

from zentao_agent.model import zentao_model
from zentao_cli.auth import client_from_profile, current_username
from zentao_cli.errors import ZentaoCliError
from zentao_cli.models import Bug


def _bug_payload(bug: Bug) -> dict[str, Any]:
    return asdict(bug)


def _resolve_me(value: str | None) -> str | None:
    if value is not None and value.lower() == "me":
        return current_username()
    return value


def list_bugs(
    execution: int,
    assigned_to: str | None = None,
    opened_by: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 100,
    fetch_all: bool = False,
) -> dict[str, Any]:
    """List bugs in a Zentao execution using optional filters."""
    try:
        client = client_from_profile()
        bugs = client.list_bugs(
            execution=execution,
            assigned_to=_resolve_me(assigned_to),
            opened_by=_resolve_me(opened_by),
            status=status,
            page=page,
            page_size=page_size,
            fetch_all=fetch_all,
        )
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"bugs": [_bug_payload(bug) for bug in bugs]}


def get_bug(bug_id: int) -> dict[str, Any]:
    """Get one Zentao bug by id."""
    try:
        client = client_from_profile()
        bug = client.get_bug(bug_id)
    except ZentaoCliError as exc:
        return {"error": str(exc)}
    return {"bug": _bug_payload(bug)}


bug_agent = LlmAgent(
    model=zentao_model(),
    name="bug_agent",
    description="Handles read-only Zentao bug query workflows.",
    instruction=(
        "You are the Zentao bug specialist. Handle only read-only bug "
        "queries: list bugs, filter bugs, and inspect a single bug. "
        "Use the provided tools for all bug data. If the user asks to "
        "create, update, close, or delete a bug, explain that this first "
        "stage only supports bug query operations. Ask for the execution "
        "ID when listing bugs and the user has not provided one."
    ),
    tools=[list_bugs, get_bug],
)
```

- [ ] **Step 3: Run bug agent tests**

Run:

```bash
uv run pytest tests/test_zentao_agent.py -v
```

Expected: the five bug tool tests pass. Any root composition tests added later are not present yet.

- [ ] **Step 4: Commit implementation**

Run:

```bash
git add zentao_agent/model.py zentao_agent/bug_agent.py tests/test_zentao_agent.py
git commit -m "feat: add read-only zentao bug agent"
```

## Task 3: Add And Implement Root Agent Team Composition

**Files:**
- Modify: `tests/test_zentao_agent.py`
- Modify: `zentao_agent/agent.py`
- Modify: `zentao_agent/__init__.py`
- Modify: `pyproject.toml`

- [ ] **Step 1: Add failing root composition test**

Append this test to `tests/test_zentao_agent.py`:

```python
def test_root_agent_registers_bug_agent():
    from zentao_agent.agent import root_agent
    from zentao_agent.bug_agent import bug_agent

    assert bug_agent in root_agent.sub_agents
    assert root_agent.name == "root_agent"
```

- [ ] **Step 2: Run the new test to verify it fails**

Run:

```bash
uv run pytest tests/test_zentao_agent.py::test_root_agent_registers_bug_agent -v
```

Expected: FAIL because `zentao_agent/agent.py` still contains the clock demo and does not register `bug_agent`.

- [ ] **Step 3: Replace `agent.py` with real root agent**

Replace `zentao_agent/agent.py` with:

```python
from __future__ import annotations

from google.adk.agents import LlmAgent

from zentao_agent.bug_agent import bug_agent
from zentao_agent.model import zentao_model


root_agent = LlmAgent(
    model=zentao_model(),
    name="root_agent",
    description="Routes Zentao assistant requests to specialist agents.",
    instruction=(
        "You are the Zentao assistant coordinator. Decide which specialist "
        "agent should handle the user request. Send bug-related requests to "
        "bug_agent, including listing bugs, viewing a bug, filtering by "
        "assignee, filtering by status, and checking bugs opened by a user. "
        "Do not answer bug data questions from memory; delegate them to "
        "bug_agent. If the request is outside the currently available "
        "specialists, explain the current limitation briefly."
    ),
    sub_agents=[bug_agent],
)
```

- [ ] **Step 4: Simplify package init**

Replace `zentao_agent/__init__.py` with:

```python
from __future__ import annotations

from zentao_agent.agent import root_agent

__all__ = ["root_agent"]
```

- [ ] **Step 5: Include `zentao_agent` in the build package list**

In `pyproject.toml`, change:

```toml
[tool.hatch.build.targets.wheel]
packages = ["zentao_cli"]
```

to:

```toml
[tool.hatch.build.targets.wheel]
packages = ["zentao_cli", "zentao_agent"]
```

- [ ] **Step 6: Run root composition test**

Run:

```bash
uv run pytest tests/test_zentao_agent.py::test_root_agent_registers_bug_agent -v
```

Expected: PASS.

- [ ] **Step 7: Run all ADK agent tests**

Run:

```bash
uv run pytest tests/test_zentao_agent.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit root team composition**

Run:

```bash
git add zentao_agent/agent.py zentao_agent/__init__.py pyproject.toml tests/test_zentao_agent.py
git commit -m "feat: compose zentao adk agent team"
```

## Task 4: Verify Existing Project Tests Still Pass

**Files:**
- No source changes expected.

- [ ] **Step 1: Run focused existing tests around bug behavior**

Run:

```bash
uv run pytest tests/test_client.py tests/test_readonly_commands.py -v
```

Expected: PASS. These tests confirm the underlying CLI client and bug command behavior still work.

- [ ] **Step 2: Run full test suite**

Run:

```bash
uv run pytest -v
```

Expected: PASS.

- [ ] **Step 3: Check git status**

Run:

```bash
git status --short
```

Expected: only intentional changes remain, or a clean tree if each task was committed.

## Self-Review

Spec coverage:

- `root_agent` routing and specialist layout are covered by Task 3.
- Read-only `bug_agent` tools are covered by Tasks 1 and 2.
- Reuse of `zentao_cli.auth.client_from_profile()` and `ZentaoClient` is covered by Task 2.
- Plain JSON-compatible tool returns are covered by Task 1.
- Structured error returns are covered by Task 1.
- Tests for tool behavior and team composition are covered by Tasks 1 and 3.
- Build packaging for `zentao_agent` is covered by Task 3.

Placeholder scan:

- No task uses placeholder markers or underspecified implementation steps.

Type consistency:

- Tool signatures match the design spec.
- Tests patch `zentao_agent.bug_agent.client_from_profile` and `zentao_agent.bug_agent.current_username`, matching the imports in the implementation.
- `root_agent.sub_agents` is tested against the actual `bug_agent` object.
