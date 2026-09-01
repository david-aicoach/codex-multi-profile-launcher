# Architecture

## Summary

This package is a **Codex multi-profile launcher**. Its job is to let an orchestrator delegate selected work to one of two isolated Codex profiles without turning Codex into a separate operating system.

Your task workspace remains the system of record.

```text
User
  |
  v
task workspace / orchestrator
  |  owns tasks, routing, review, synthesis
  |
  +--> Codex Bridge
         |
         +--> C1 / Codex Business  (~/.codex-business)
         +--> C2 / Codex David     (~/.codex-david)
```

The package also provides an explicit GitHub PR review entry point. It does not change the native OpenAI `@codex` integration:

```text
GitHub PR comment
  |
  +--> @codex-business review -> trusted router -> C1
  |
  +--> @codex-david review    -> trusted router -> C2
```

## Boundaries

### Your Task System Owns

- task intake
- visible status
- routing
- review and approval
- review, approval, changelog, and session memory

### This Bridge Owns

- `C1` and `C2` worker identity
- separate `CODEX_HOME` directories
- profile-specific launcher scripts
- controlled `codex exec` wrapper calls
- explicit GitHub review profile selection
- local execution logs and result files

## Worker Map

| Code | Worker | Use For | Avoid For |
|---|---|---|---|
| `C1` | Codex Business | production implementation, hardening, integration follow-through, explicit review | early fuzzy exploration |
| `C2` | Codex David | prototypes, bootstrap work, reviews, second-pass critique | production deployment decisions |

## Dispatch Rule

Dispatch Codex only when the task economics make sense:

- self-contained coding task
- mechanical change with a clear checklist
- independent review of a diff or implementation
- work that benefits from separate context

Work inline when the task is tiny, judgment-heavy, or depends on evolving conversation context.

## Authentication Model

Each Codex worker has its own home:

```text
~/.codex-business   # C1
~/.codex-david      # C2
```

Each home may contain its own `auth.json`, config, logs, and history. This repository must never contain those credentials.

The desktop launchers also separate the GUI app data:

```text
~/Library/Application Support/Codex-C1-Business
~/Library/Application Support/Codex-C2-David
```

The normal ChatGPT/Codex app continues to use `~/Library/Application Support/Codex`.

## Normal Execution

1. Create or update the real task in your task workspace.
2. Decide that Codex dispatch is useful.
3. Choose `C1` or `C2`.
4. Invoke `wrappers/delegate_to_codex.sh`.
5. The wrapper writes execution evidence under `runtime/outputs/`.
6. Read the result and update the task record.

## GitHub Review Execution

1. An authorized maintainer comments an exact supported review command on a PR.
2. The default-branch workflow performs a cheap author-association filter.
3. A reusable trusted workflow runs on a dedicated `codex-profile-router` self-hosted runner.
4. The router verifies the commenter has `write`, `maintain`, or `admin` repository permission.
5. The router fetches PR metadata and the unified diff through GitHub's API; it never checks out or executes the PR branch.
6. The exact C1/C2 `CODEX_HOME` is selected from trusted code.
7. Codex runs in an empty read-only workspace and returns structured review JSON.
8. The router validates the result and posts a GitHub COMMENT review.
9. Failure stops on the selected identity; there is no automatic fallback or quota-based rotation.

See `docs/04_GITHUB_REVIEW_ROUTER.md` for the operational and security contract.

## Design Principle

The bridge should stay boring. If a feature duplicates your task system, remove it from this package or leave it in your task system only.

Explicit profile routing is allowed; automatic account cycling and credential movement are not.
