# Codex Multi-Profile Launcher Instructions

This repository is a small bridge for running two isolated Codex profiles from your preferred task workspace.

Your task workspace remains the orchestration home:

```text
/path/to/your/task-workspace
```

Your orchestrator owns task intake, routing, tracker updates, review, and synthesis. This folder only provides the Codex runtime boundary.

## Worker Codes

| Code | Name | Role | Codex home |
|---|---|---|---|
| `C1` | Codex Business | Production implementation, hardening, integration work, explicit review | `~/.codex-business` |
| `C2` | Codex David | Prototypes, bootstrap work, independent review | `~/.codex-david` |

These codes are examples. Rename them if they conflict with your own agent roster.

## Startup Check

Before changing files in this package:

1. Read `README.md`.
2. Read `docs/00_MASTER_ARCHITECTURE.md`.
3. Read the relevant worker file under `agents/`.
4. Read `runtime/active_worker.json`.
5. Run `python3 tools/aosctl.py validate`.
6. Inspect Git status and avoid unrelated changes.

## Rules

- Keep tasks in your task system.
- Use this package only for Codex profile isolation and wrapper execution.
- Do not read, print, copy, or commit any `auth.json`.
- Do not alter the other worker's Codex home.
- Do not create account cycling, quota switching, or automatic credential movement.
- Keep edits small, local, and reversible.
- Do not deploy, publish, delete, or write to external systems without human approval.
- For the GitHub review router, an exact supported review command from a requester with verified write/maintain/admin repository permission is human approval to post that review only.
- The GitHub review router must never execute pull-request code, silently fall back to another Codex profile, or impersonate the native OpenAI `@codex` GitHub bot.

## GitHub Review Router

Explicit review routing is documented in `docs/04_GITHUB_REVIEW_ROUTER.md`.

Supported profile selectors are intentionally fixed:

```text
@codex-business review  -> C1 -> ~/.codex-business
@codex-david review     -> C2 -> ~/.codex-david
```

The router runs from trusted default-branch code on a dedicated self-hosted runner and fetches PR metadata/diffs through the GitHub API. PR code is untrusted review input and must not be executed.

## Output Contract

Wrapper runs write local execution evidence under:

```text
runtime/outputs/<TASK-ID>/
  status.json
  summary.md
  run.log
  events.jsonl
  artifacts/
  error.md      # only on failure
```

The task remains the human source of truth. These files are execution evidence.

## Stop Conditions

Stop and report when:

- the expected worker identity is missing or wrong
- a task asks for credentials or `auth.json`
- a destructive or external action is needed without explicit authorization
- tests fail for unrelated reasons
- the requested change belongs in your task system instead of this bridge
