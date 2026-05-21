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
