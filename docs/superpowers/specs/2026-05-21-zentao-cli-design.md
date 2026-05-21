# Zentao CLI Design

## Context

Build a Python command-line client for Zentao Open Source Edition 21.7.5. The first version must support the existing 21.7.5 deployment and should be based on Zentao RESTful API v1. API 2.0 support is out of scope for the first version.

The CLI targets three long-term use cases:

- Personal daily workflow for assigned tasks.
- Scriptable automation.
- Future expansion toward broader Zentao coverage.

The first release should stay focused: tasks are the primary workflow, while bugs and stories are read-only.

## Recommended Approach

Use Typer for the CLI, Rich for human-readable terminal output, and `httpx` for HTTP requests. The code should be layered so Zentao API details stay inside the client/model layer instead of leaking into command handlers.

This gives the CLI a pleasant daily workflow while keeping stable JSON output for scripts.

## Command Scope

Initial commands:

```text
zentao login
zentao whoami
zentao task list [--mine] [--status wait|doing|done|closed] [--project ID] [--json]
zentao task view TASK_ID [--json]
zentao task update TASK_ID --status doing
zentao task comment TASK_ID "content"
zentao task finish TASK_ID [--comment "finish note"]
zentao bug list [--assigned-to me] [--status active] [--json]
zentao bug view BUG_ID [--json]
zentao story list [--product ID] [--status active] [--json]
zentao story view STORY_ID [--json]
```

`zentao task list --mine` should be optimized for frequent daily use. Its table output should include task ID, title, project, status, priority, deadline, and assignee. Every user-facing command that returns data should support stable JSON output through `--json`.

## Architecture

Suggested package structure:

```text
src/zentao_cli/
  __init__.py
  main.py
  config.py
  auth.py
  client.py
  models.py
  formatters.py
  errors.py
  commands/
    task.py
    bug.py
    story.py
```

Responsibilities:

- `main.py`: Typer entry point and command group registration.
- `commands/*`: Parse CLI arguments and call application/client functions. Do not build API URLs directly here.
- `config.py`: Resolve config paths, read/write profiles, and expose current credentials/session data.
- `auth.py`: Implement `login`, `whoami`, and future logout/session refresh behavior.
- `client.py`: Encapsulate Zentao 21.7.5 API v1 request construction, authentication/session handling, timeouts, and response parsing.
- `models.py`: Normalize raw Zentao API responses into stable Python structures for tasks, bugs, stories, and users.
- `formatters.py`: Render Rich tables and JSON output consistently.
- `errors.py`: Define CLI-level exceptions.

This separation keeps API v1 specifics replaceable if the project later supports API 2.0 or another Zentao version.

## Authentication And Configuration

The first version uses interactive login:

```text
zentao login
```

Login flow:

1. Prompt for Zentao base URL.
2. Prompt for username.
3. Prompt for password with hidden input.
4. Call the Zentao API v1 login endpoint.
5. Save the session data locally.

Credentials should be stored via `platformdirs`, using the OS-appropriate config directory. On Windows this should resolve under the user's local app data directory. The first version should not save the plaintext password. It may save the active session name and session ID/token needed for subsequent API calls.

Example config shape:

```toml
[default]
base_url = "https://zentao.example.com"
username = "alice"
session_name = "zentaosid"
session_id = "..."
```

The architecture should allow future `--profile` support, although multi-profile management does not need to be fully built in the first release.

## Output Design

Default output is human-readable and should use Rich tables where useful. Script output is enabled with `--json`.

JSON output must use stable field names and should avoid exposing raw Zentao response shapes directly. This protects automation scripts from minor API or normalization changes.

Errors in human-readable mode should be concise and actionable, for example:

```text
Not logged in. Run: zentao login
```

Errors in JSON mode should use a stable structure:

```json
{
  "ok": false,
  "error": {
    "type": "AuthError",
    "message": "not logged in"
  }
}
```

## Error Handling

Define a small exception hierarchy:

- `AuthError`: not logged in, session expired, invalid credentials.
- `ApiError`: Zentao returned a business/API error.
- `NetworkError`: connection failure, timeout, TLS or DNS problem.
- `ConfigError`: missing or invalid local configuration.
- `NotFoundError`: requested task, bug, story, or user does not exist.

Command handlers should catch these exceptions and route them through the same output layer so table/text and JSON modes behave consistently.

## Testing Strategy

Use mocked HTTP responses for automated tests. Do not require a live Zentao server in the normal test suite.

Initial tests:

```text
tests/
  test_config.py
  test_formatters.py
  test_client.py
  test_task_commands.py
```

Coverage priorities:

- Config read/write preserves all required fields.
- API responses normalize into stable task, bug, and story models.
- Task commands produce correct table output and JSON output under mocked API responses.
- Auth/config errors produce stable text and JSON error responses.

Manual smoke testing against the real Zentao 21.7.5 server can be documented separately once implementation begins.

## Non-Goals For First Version

- Zentao API 2.0 support.
- Full CRUD for bugs and stories.
- Replacing the Zentao web UI.
- Saving plaintext passwords.
- Requiring a real Zentao server for automated tests.
