# Architecture

## Summary

This package is a **Codex multi-profile launcher**. Its job is to let the TBHRC GitHub control plane delegate selected work to one of two isolated Codex profiles without turning Codex into a separate operating system.

The owning GitHub repository and Issue/PR remain the system of record.

```text
Founder/user request
  |
  v
canonical Skill + owning GitHub Issue/PR
  |
  v
authorised controller/orchestrator
  |
  +--> normal provider/runtime when sufficient
  |
  +--> AI Engine when trusted Mac-local execution is required
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

### GitHub / Controller Owns

- task intake and durable work orders
- provider/seat routing and budget decisions
- visible status
- review and approval
- applying verified patches/results
- merges, deployments and other external authority
- reusable method through canonical Skills

### This Bridge Owns

- `C1` and `C2` worker identity
- separate `CODEX_HOME` directories
- exact profile-specific launcher mapping
- deterministic bounded `codex exec` calls
- explicit GitHub review profile selection
- local execution logs and result files

## Worker Map

| Code | Worker | Codex home | Runtime rule |
|---|---|---|---|
| `C1` | Codex Business | `~/.codex-business` | Explicit selection only; currently fail closed when Business credits are exhausted. |
| `C2` | Codex David | `~/.codex-david` | Explicit selection only; real model execution is proven. |

Neither seat is a permanent priority. The controller chooses a seat/provider based on task fit, authority and live capacity. This bridge never rotates accounts automatically.

## Dispatch Rule

Dispatch Codex only when the task economics make sense:

- self-contained coding task;
- mechanical change with a clear checklist;
- independent review of a diff or implementation;
- work that benefits from separate context;
- a bounded local implementation task where the controller retains external authority.

Work inline when the task is tiny, judgment-heavy, or already executable through a simpler authorised route.

## Authentication Model

Each Codex worker has its own home:

```text
~/.codex-business   # C1
~/.codex-david      # C2
```

Each home may contain its own `auth.json`, config, logs, and history. This repository must never contain, inspect or move those credentials.

For automated execution, `CODEX_HOME` supplies the selected identity/authentication while ambient user config is ignored. Trusted launcher code supplies the execution policy explicitly.

The desktop launchers also separate the GUI app data:

```text
~/Library/Application Support/Codex-C1-Business
~/Library/Application Support/Codex-C2-David
```

The normal ChatGPT/Codex app continues to use `~/Library/Application Support/Codex`.

## Automated Execution Boundary

General work orders and routed PR reviews share one fixed execution policy:

```text
codex exec
  --strict-config
  --ignore-user-config
  --ephemeral
  --skip-git-repo-check
  -C <bounded-workspace>
  -c default_permissions=":workspace"
  -c approval_policy="never"
  ...
```

Properties:

- exact C1/C2 identity selected through `CODEX_HOME`;
- only the supplied workspace is writable through the built-in `:workspace` profile;
- ambient profile configuration cannot silently widen authority;
- no interactive approval escape hatch;
- no persistent Codex session from automation;
- no legacy `--sandbox` mode;
- selected-seat failure is terminal for that invocation; no hidden fallback.

## Normal Work-Order Execution

1. Create/update the real work order in the owning GitHub repository.
2. Apply the canonical Skill and decide Codex dispatch is useful.
3. The controller explicitly chooses `C1` or `C2`.
4. AI Engine reaches the trusted Mac runtime when remote dispatch is required.
5. Invoke `wrappers/delegate_to_codex.sh` against a bounded worktree/workspace.
6. The wrapper writes execution evidence under `runtime/outputs/`.
7. The controller verifies the result and continues the owning repository's normal PR/merge lifecycle.

The Codex worker does not independently push, merge, deploy, send messages or mutate external production systems.

## GitHub Review Execution

1. An authorized maintainer comments an exact supported review command on a PR.
2. The default-branch workflow performs a cheap author-association filter.
3. A reusable trusted workflow runs on a dedicated `codex-profile-router` self-hosted runner.
4. The router verifies the commenter has `write`, `maintain`, or `admin` repository permission.
5. The router fetches PR metadata and the unified diff through GitHub's API; it never checks out or executes the PR branch.
6. The exact C1/C2 `CODEX_HOME` is selected from trusted code.
7. Codex runs in an empty disposable `:workspace` using the fixed no-approval, ignored-user-config, ephemeral execution boundary and returns structured review JSON.
8. The router validates the result and posts a GitHub COMMENT review.
9. Failure stops on the selected identity; there is no automatic fallback or quota-based rotation.

See `docs/04_GITHUB_REVIEW_ROUTER.md` for the operational and security contract.

## Design Principle

The bridge should stay boring. If a feature duplicates the GitHub control plane, canonical Skills, or AI Engine privileged-runtime ownership, it does not belong here.

Explicit profile routing is allowed; automatic account cycling, credential movement and implicit authority expansion are not.
