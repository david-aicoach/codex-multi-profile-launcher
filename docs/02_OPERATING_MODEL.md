# Operating Model

## Principle

**GitHub routes the work. Skills define the reusable method. AI Engine exposes trusted local runtime when required. This repository only selects and runs an explicit Codex profile.**

Do not build a second queue, second tracker, second Skill Bank, or second orchestration identity here.

## Current TBHRC Control Plane

```text
request
-> canonical Skill in tbhrc/skills
-> owning repository + controlling GitHub Issue/PR
-> authorised controller/agent
-> can normal GitHub/connector/API/MCP/provider capability execute safely?
   YES -> execute directly
   NO, trusted local runtime needed -> tbhrc/ai-engine
       -> Mac self-hosted runner
       -> explicit C1 or C2 selection
       -> this launcher / Codex CLI isolation
-> verify result
-> durable evidence back to the owning GitHub work record
```

Canonical references:

- `tbhrc/skills/human-ai-operations-map`
- `tbhrc/skills/github-agent-workflow`
- `tbhrc/skills/github-multi-agent-orchestrator`
- `tbhrc/skills/gh-mac-runner-operator-maintenance`
- `tbhrc/ai-engine`

## Codex Worker Identities

| Worker | Identity | Codex home | Use |
|---|---|---|---|
| `C1` | Codex Business | `~/.codex-business` | An authorised Business-seat executor when task fit and live capacity justify it. |
| `C2` | Codex David | `~/.codex-david` | An authorised David-seat executor when task fit and live capacity justify it. |

The normal/default `~/.codex` profile may exist independently. It is not the `C2` alias.

Do not make C1 or C2 a permanent first-choice hierarchy. Provider/seat selection belongs to the controller and is based on task fit, permissions, current availability and remaining budget.

## Dispatch Fit

Good local Codex dispatch:

- clear owning GitHub work order;
- clear input and output expectation;
- bounded project/worktree;
- implementation-heavy or mechanical work where a separate executor is useful;
- local-only work that does not require the Codex worker to hold production authority;
- independent analysis/review where the selected profile has capacity.

Poor local Codex dispatch:

- a quick question the controller can answer directly;
- ambiguous strategy requiring ongoing founder judgement;
- work already executable through a simpler authorised GitHub/connector/API route;
- anything requiring credential inspection or movement;
- production deployment, message sending, destructive external mutation, or other side effects unless a separate governing workflow explicitly authorises and performs them.

## Explicit Selection and Budget Failover

The launcher never chooses an account based on quota and never silently changes identities.

```text
controller observes provider/seat state
-> controller explicitly chooses C1 or C2
-> launcher runs only that identity
-> selected identity succeeds OR fails closed
-> if it fails/out of credits, controller decides whether to use another authorised provider/seat
```

This separation is deliberate:

- **orchestrator/provider routing** owns capacity and budget decisions;
- **this bridge** owns identity isolation and exact profile execution.

## Generic Local Executor

`wrappers/delegate_to_codex.sh` supports bounded local workspace-write execution.

Example contract:

```bash
bash wrappers/delegate_to_codex.sh \
  --worker C2 \
  --task-file /absolute/path/to/task.md \
  --workdir /absolute/path/to/bounded/worktree
```

The wrapper:

1. maps `C1`/`C2` to the exact `CODEX_HOME`;
2. validates the task file/workdir;
3. locks the task to avoid duplicate local runs;
4. activates the selected worker;
5. runs `codex exec --sandbox workspace-write --json`;
6. writes summary/status/log/event evidence under `runtime/outputs/<TASK-ID>/`.

This is a **local executor**, not a GitHub-wide dispatch control plane. The trusted GitHub bridge that allows remote/controller agents to use it belongs to `tbhrc/ai-engine` and is tracked in `tbhrc/ai-engine#44` until live-proven.

## Approval and Authority Rules

A Codex worker may perform local, reversible work in its assigned workdir.

It must not independently:

- deploy or publish;
- send messages;
- delete material data;
- change credentials/authentication;
- inspect or move `auth.json`;
- mutate external production systems;
- push/merge outside the authority granted by the owning GitHub workflow.

The controlling agent/workflow applies the relevant canonical Skill, verifies the Codex result and performs any authorised durable/external action through the correct system.

## Review Router

The PR-review router is a separate narrow capability:

```text
@codex-business review -> C1 -> ~/.codex-business
@codex-david review    -> C2 -> ~/.codex-david
```

It reads PR metadata/diffs through the GitHub API and never checks out/executes PR code.

As of 3 September 2026:

- C2 review execution is live-proven.
- C1 authentication is live-proven.
- C1 real execution is externally blocked by Business workspace credit exhaustion and must fail closed with no fallback.

## Evidence and Return Path

After every meaningful local Codex run, the controller should record in the owning GitHub Issue/PR:

- worker used: `C1` or `C2`;
- status;
- relevant files/diff/artifacts;
- tests/checks run;
- output/evidence location;
- any provider/budget failure;
- next action.

`runtime/outputs/` is execution evidence only. GitHub remains the durable operating record.
