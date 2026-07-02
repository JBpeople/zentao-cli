# Zentao ADK Agent Team Design

## Context

The project already has a working Zentao CLI layer with `ZentaoClient`, auth helpers, normalized dataclasses, and tested bug commands. The current ADK layer is still a prototype: `zentao_agent/agent.py` defines a clock demo, while `bug_agent.py` and `task_agent.py` are placeholders.

The first ADK goal is to introduce a small agent team and delegate bug-related user requests to a dedicated `bug_agent`.

## Goals

- Keep `root_agent` focused on intent routing and conversation flow.
- Give `bug_agent` ownership of bug query workflows.
- Reuse the existing Python client layer instead of invoking shell CLI commands.
- Start with read-only bug operations to reduce risk.
- Keep the design extensible for later `task_agent`, `story_agent`, and write operations.

## Non-Goals

- Do not rebuild Zentao API access inside the ADK agent layer.
- Do not call Typer CLI commands from tools.
- Do not add bug create, update, or delete in the first stage.
- Do not make `root_agent` own all domain-specific tools.

## Recommended Architecture

Use a coordinator-specialist layout:

```text
root_agent
  |-- bug_agent
  `-- task_agent later
```

`root_agent` decides whether the user request is bug-related. If it is, it transfers the request to `bug_agent`. The root agent should not call Zentao bug tools directly.

`bug_agent` handles only bug query workflows and exposes Python tools backed by the existing `zentao_cli` package.

## Components

### `zentao_agent/agent.py`

Responsibilities:

- Configure the shared LiteLLM model.
- Import specialist agents.
- Define `root_agent`.
- Register `bug_agent` as a sub-agent.
- Provide routing instructions in Chinese, matching the expected user language.

The root instruction should say that bug-related requests, such as listing bugs, viewing a bug, filtering by assignee, filtering by status, or checking bugs opened by a user, belong to `bug_agent`.

### `zentao_agent/bug_agent.py`

Responsibilities:

- Define bug-specific ADK tools.
- Define `bug_agent`.
- Keep prompt scope narrow: bug search, bug detail lookup, and bug summary.
- Refuse or defer write operations in stage one.

Initial tools:

- `list_bugs(execution, assigned_to=None, opened_by=None, status=None, page=1, page_size=100, fetch_all=False)`
- `get_bug(bug_id)`

Both tools should return plain dictionaries and lists, not Rich tables or Typer output.

### Existing `zentao_cli` Layer

The agent tools should call:

- `zentao_cli.auth.client_from_profile()`
- `ZentaoClient.list_bugs(...)`
- `ZentaoClient.get_bug(...)`

This keeps auth, session handling, API URLs, and response normalization in one existing place.

## Data Flow

For a user request such as "List active bugs assigned to me in execution 303":

1. `root_agent` classifies it as a bug request.
2. ADK transfers the request to `bug_agent`.
3. `bug_agent` extracts filters:
   - `execution=303`
   - `assigned_to="me"`
   - `status="active"`
4. `bug_agent` calls `list_bugs`.
5. The tool resolves `"me"` to the current Zentao username if needed.
6. The tool returns normalized bug dictionaries.
7. `bug_agent` summarizes results for the user.

## Tool Return Shape

Return plain JSON-compatible values:

```python
{
    "id": 7,
    "title": "Crash on import",
    "status": "active",
    "severity": "3",
    "assigned_to": "alice",
    "opened_by": "bob",
}
```

Errors should also be JSON-compatible:

```python
{
    "error": "Not logged in. Run: zentao login"
}
```

## Safety Rules

- Stage one tools are read-only.
- `bug_agent` must not create, update, or delete bugs.
- If the user asks for a write action, `bug_agent` should explain that the current agent only supports query operations.
- Later write tools should require explicit confirmation before mutating Zentao data.
- Delete should be added last, if at all, and should require a strong confirmation step.

## Error Handling

The tools should catch `ZentaoCliError` and return a structured error object instead of throwing raw exceptions into the model loop.

For missing required values, the agent should ask a short follow-up question. For example, `list_bugs` requires an execution ID because the existing client method is execution-scoped.

## Testing

Focused tests should cover:

- `list_bugs` calls `client_from_profile().list_bugs(...)` with the expected filters.
- `"me"` is resolved through the existing username helper when supported.
- `get_bug` calls `client_from_profile().get_bug(...)`.
- Zentao errors are returned as structured tool errors.
- `root_agent` includes `bug_agent` as a sub-agent.

These tests should mock the client layer and avoid real network calls.

## Implementation Order

1. Add bug tool functions in `zentao_agent/bug_agent.py`.
2. Define `bug_agent` with read-only bug instructions.
3. Replace the clock demo in `zentao_agent/agent.py` with the real `root_agent`.
4. Add focused tests for tool behavior and root team composition.
5. Run the relevant test subset.

## Later Extensions

After read-only queries are stable:

- Add `task_agent` with task query tools.
- Add `story_agent` or project/product discovery helpers if routing needs context.
- Add bug creation with explicit confirmation.
- Add bug updates with field-level confirmation.
- Consider delete only after create/update flows are reliable.
