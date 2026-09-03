# Codex Multi-Profile Launcher Instructions

This repository is a small runtime bridge for two isolated Codex profiles on David's Mac.

It is **not** the TBHRC task system, orchestration home, Skill Bank, or production authority.

## Current TBHRC control plane

```text
founder/user request
-> most specific canonical Skill in tbhrc/skills
-> owning GitHub repository + controlling Issue/PR
-> github-agent-workflow / github-multi-agent-orchestrator
-> normal authorised provider/runtime when sufficient
-> tbhrc/ai-engine only when trusted Mac/local-profile access is genuinely required
-> this launcher for explicit C1/C2 Codex isolation/execution
-> verified result/evidence back to the owning GitHub work record
```

Canonical navigation:

- Skills / reusable HOW: https://github.com/tbhrc/skills
- Human + AI operating map: https://github.com/tbhrc/skills/tree/main/human-ai-operations-map
- Multi-agent routing: https://github.com/tbhrc/skills/tree/main/github-multi-agent-orchestrator
- Durable GitHub workflow: https://github.com/tbhrc/skills/tree/main/github-agent-workflow
- Mac runner operations: https://github.com/tbhrc/skills/tree/main/gh-mac-runner-operator-maintenance
- Privileged runtime owner: https://github.com/tbhrc/ai-engine

## Worker Codes

| Code | Name | Codex home | Notes |
|---|---|---|---|
| `C1` | Codex Business | `~/.codex-business` | Explicit Business identity. Availability/budget is runtime state, not a permanent priority. |
| `C2` | Codex David | `~/.codex-david` | Explicit David identity. Availability/budget is runtime state, not a permanent priority. |

These two IDs are now established TBHRC runtime aliases. Do not silently reinterpret or swap them.

The normal/default Codex home `~/.codex` may also exist on the Mac, but it is **not** `C2`. When a work order names `C1` or `C2`, use the exact homes above.

## Startup Check

Before changing files in this package:

1. Read `README.md`.
2. Read `docs/00_MASTER_ARCHITECTURE.md`.
3. Read `docs/02_OPERATING_MODEL.md`.
4. Read the relevant worker file under `agents/` when worker behaviour is involved.
5. Read `runtime/active_worker.json` only as local execution state, never as task canon.
6. Read the controlling GitHub Issue/PR.
7. Run `python3 tools/aosctl.py validate --verbose`.
8. Run the relevant tests.
9. Inspect Git status and avoid unrelated changes.

## Rules

- Keep durable work state in the owning GitHub Issue/PR/repository.
- Keep reusable operating method in canonical `tbhrc/skills`.
- Use this package only for explicit Codex profile isolation, local wrapper execution, and the approved PR-review router.
- Use `tbhrc/ai-engine` as the privileged GitHub bridge when a cloud/controller agent needs access to these Mac-local profiles.
- Do not read, print, copy, move, upload, or commit any `auth.json`.
- Do not alter the other worker's Codex home.
- Do not create account cycling, quota switching, or automatic credential movement.
- Profile selection must be explicit. If the selected profile is unavailable or out of credits, fail closed and let the controller choose a different authorised provider/seat.
- Keep local edits bounded to the assigned workdir.
- Automation must use the fixed Codex permission-profile boundary: `default_permissions=":workspace"`, `approval_policy="never"`, explicit `-C`, ignored ambient user config, and ephemeral sessions. Do not reintroduce legacy `--sandbox` flags into automated C1/C2 execution.
- A Codex worker may produce local implementation/diffs/evidence, but must not deploy, publish, send messages, delete material data, change credentials, or mutate external production systems without the separate authority required by the owning workflow.
- Do not turn this repository into a second queue, tracker, or orchestration database.
- For the GitHub review router, an exact supported review command from a requester with verified write/maintain/admin repository permission is approval to post that review only.
- The GitHub review router must never execute pull-request code, silently fall back to another Codex profile, or impersonate the native OpenAI `@codex` GitHub bot.

## Generic Local Execution

`wrappers/delegate_to_codex.sh` is the existing local executor:

```text
--worker C1 -> CODEX_HOME=~/.codex-business
--worker C2 -> CODEX_HOME=~/.codex-david
```

For automated work orders it runs `codex exec` in the supplied workdir with an explicit `:workspace` permission profile, `approval_policy="never"`, ignored ambient user config, and an ephemeral session. The selected `CODEX_HOME` supplies authentication only. Execution evidence is written under `runtime/outputs/<TASK-ID>/`.

The automated executor must fail closed if the selected seat is unavailable. It must never silently rotate to the other profile.

GitHub-controlled general work-order exposure is owned by `tbhrc/ai-engine` and tracked in `tbhrc/ai-engine#44`; this launcher remains the profile-isolation/execution component rather than an independent remote control plane.

## GitHub Review Router

Explicit review routing is documented in `docs/04_GITHUB_REVIEW_ROUTER.md`.

Supported selectors are fixed:

```text
@codex-business review -> C1 -> ~/.codex-business
@codex-david review    -> C2 -> ~/.codex-david
```

The router runs from trusted default-branch code on a dedicated self-hosted runner and fetches PR metadata/diffs through the GitHub API. PR code is untrusted review input and must not be executed. The model runs inside an empty disposable `:workspace` directory under the same deterministic no-approval/ephemeral boundary used by general work orders.

Current proof state as of 3 September 2026:

- C2 real PR review: proven end to end.
- C1 authentication: proven.
- C1 real PR review/model execution: externally blocked by Business-account credit exhaustion; this is not a runner/auth defect.

Do not repeatedly retry C1 while that billing state remains current.

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

These files are runtime evidence. The owning GitHub Issue/PR remains the durable work record.

## Stop Conditions

Stop and report to the controlling GitHub work record when:

- the expected worker identity is missing or wrong;
- the selected profile is unavailable/out of credits and the task has not been explicitly rerouted;
- a task asks for credentials or `auth.json`;
- a destructive/external action is needed without the authority required by the owning workflow;
- tests fail for unrelated reasons;
- the requested change belongs in Skills, AI Engine, or another owning repository instead of this bridge.
