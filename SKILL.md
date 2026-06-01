---
name: zentao-cli-workflows
description: Use when an agent needs to operate ZenTao through this repository's CLI, including discovering products/projects/executions, listing and managing execution-scoped stories, tasks, and bugs, creating/updating/deleting records, linking stories to executions, handling pagination, and safely verifying changes against a live ZenTao instance.
---

# ZenTao CLI Workflows

This repository provides a Python Typer CLI for ZenTao. Prefer JSON output for agent work, and use `python -m zentao_cli.main ...` from the repository root when the `zentao` console script is not installed.

## Safety Rules

- Treat create/update/delete/link commands as live ZenTao mutations.
- Before destructive verification, create records with a `[CLI TEST]` prefix and delete only those test records.
- Do not print credentials, tokens, `.env`, or saved profile contents.
- Use `--json` for machine-readable output.
- Use `--yes` only when intentionally deleting a known test or user-approved record.

## Discovery Flow

Start from the broad context and narrow down:

```bash
zentao product list --json
zentao project list --json
zentao execution list --project PROJECT_ID --json
zentao execution view EXECUTION_ID --json
```

Then inspect execution-scoped work:

```bash
zentao story list --execution EXECUTION_ID --all --json
zentao task list --execution EXECUTION_ID --all --json
zentao bug list --execution EXECUTION_ID --all --json
```

If results are incomplete, use pagination explicitly:

```bash
zentao story list --execution EXECUTION_ID --page 1 --page-size 100 --json
zentao story list --execution EXECUTION_ID --all --page-size 1000 --json
```

## Stories

Create a product story:

```bash
zentao story create --product PRODUCT_ID --title "Title" --spec "Requirement body" --json
```

Create a story under an execution. `--product` is optional only when the execution has exactly one linked product:

```bash
zentao story create --execution EXECUTION_ID --title "Title" --spec "Requirement body" --status draft --json
zentao story create --execution EXECUTION_ID --product PRODUCT_ID --title "Title" --spec "Requirement body" --json
```

Link an existing story to an execution:

```bash
zentao execution link-story EXECUTION_ID --story STORY_ID --json
```

Update or delete a story:

```bash
zentao story update STORY_ID --title "New title" --spec "New body" --verify "Acceptance criteria" --json
zentao story delete STORY_ID --yes --json
```

`story update` uses ZenTao's story change endpoint, so pass both `--title` and `--spec`.

## Tasks

Create a task directly under an execution:

```bash
zentao task create --execution EXECUTION_ID --name "Task title" --est-started 2026-06-01 --deadline 2026-06-05 --json
```

Create a task from a story:

```bash
zentao task create --execution EXECUTION_ID --story STORY_ID --name "Task title" --est-started 2026-06-01 --deadline 2026-06-05 --json
```

`--type` defaults to `devel`; `--estimate` is optional.

Update or delete a task:

```bash
zentao task update TASK_ID --name "New title" --desc "New description" --deadline 2026-06-10 --json
zentao task update TASK_ID --status doing --json
zentao task delete TASK_ID --yes --json
```

## Bugs

Create a bug under an execution. `--product` is optional only when the execution has exactly one linked product:

```bash
zentao bug create --execution EXECUTION_ID --title "Bug title" --steps "Reproduction steps" --json
zentao bug create --execution EXECUTION_ID --product PRODUCT_ID --title "Bug title" --steps "Reproduction steps" --severity 2 --pri 2 --json
```

Update or delete a bug:

```bash
zentao bug update BUG_ID --title "New title" --steps "New steps" --severity 2 --pri 2 --json
zentao bug delete BUG_ID --yes --json
```

## Common Errors

- `您无权访问该项目！`: The current account cannot access that project/execution through the API. Query visible projects first with `zentao project list --json`.
- `Execution ... has multiple linked products`: pass `--product` explicitly.
- `『预计开始』不能为空` or `『截止日期』不能为空`: task creation requires `--est-started` and `--deadline`.
- `『评审人』不能为空`: story creation under execution should use this CLI path; it sends the no-review flag used by the web UI.

## Verification Pattern

For live smoke tests, create, update, and delete a test record in one sequence:

```bash
zentao task create --execution EXECUTION_ID --name "[CLI TEST] task smoke" --est-started 2026-06-01 --deadline 2026-06-05 --json
zentao task update TASK_ID --name "[CLI TEST] task smoke updated" --json
zentao task delete TASK_ID --yes --json
```
