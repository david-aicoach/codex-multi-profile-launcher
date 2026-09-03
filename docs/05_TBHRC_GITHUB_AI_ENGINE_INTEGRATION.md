# TBHRC GitHub + AI Engine Integration

## Purpose

This document records how the Codex C1/C2 launcher fits into the current TBHRC human + AI operating architecture.

The launcher is a **runtime adapter**, not a task/orchestration system.

## Canonical Ownership

```text
tbhrc/skills
= reusable HOW, provider routing and operating intelligence

domain repository + GitHub Issue/PR
= work objective, decisions, acceptance and durable evidence

github-multi-agent-orchestrator / github-agent-workflow
= executor selection + lifecycle

tbhrc/ai-engine
= privileged access to trusted runtimes that cloud agents cannot safely reach directly

codex-multi-profile-launcher
= C1/C2 profile isolation + local Codex execution/review adapter
```

## Identity Registry

| Alias | Identity | CODEX_HOME | Status on 3 Sep 2026 |
|---|---|---|---|
| `C1` | Codex Business | `~/.codex-business` | Authenticated; real execution currently externally blocked by Business workspace credit exhaustion. |
| `C2` | Codex David | `~/.codex-david` | Authenticated; real PR-review execution proven through AI Engine Mac runner. |

The default `~/.codex` profile may coexist on the Mac. It is not the C2 alias.

## Existing Capabilities

### Local general executor

`wrappers/delegate_to_codex.sh` already supports:

```text
explicit C1/C2 selection
-> exact CODEX_HOME
-> bounded task file + workdir
-> codex exec --sandbox workspace-write --json
-> local status/summary/log/event evidence
```

This is real local execution capability.

### GitHub PR-review router

The review router is separately proven through the dedicated `codex-profile-router` self-hosted runner in `tbhrc/ai-engine`.

```text
@codex-business review -> C1
@codex-david review    -> C2
```

It never checks out or executes PR code and never silently falls back between profiles.

### Missing integration at audit start

At the start of the 3 September 2026 integration audit, AI Engine exposed:

- Mac local execution proof;
- profile login-status adapter;
- PR-review router;

but **not** a GitHub-controlled general work-order adapter for `delegate_to_codex.sh`.

That gap is tracked in:

- `tbhrc/ai-engine#44` — general C1/C2 work-order dispatch;
- `tbhrc/skills#224` — provider-failover/Skill routing awareness;
- this repo `#5` — removal of stale Larry/legacy-task-system assumptions.

## Required Routing Behaviour

Provider/seat selection happens in the controller, never inside the launcher:

```text
controller observes task + permissions + current capacity/budget
-> explicitly selects C1 or C2
-> launcher runs only that profile
-> success OR fail closed
-> controller may then explicitly choose a different authorised provider/seat
```

Never implement:

- hidden quota cycling;
- automatic account rotation;
- silent C1 <-> C2 fallback;
- credential copying;
- shared `auth.json`;
- arbitrary remote shell control.

## General Dispatch Target Architecture

The bounded target in `tbhrc/ai-engine#44` is:

```text
owning GitHub work order
-> canonical Skill
-> explicit executor choice
-> trusted AI Engine workflow on main
-> existing Mac runner
-> explicit C1/C2
-> bounded local worktree
-> local Codex workspace-write
-> patch/result/evidence only
-> controller verifies
-> owning repository performs normal branch/PR/apply/merge lifecycle
```

Version 1 of that lane should **not** let the Codex worker independently push, merge, deploy, send messages or mutate production systems.

## VPS Relationship

The VPS is a sibling privileged-runtime lane, not part of this launcher.

```text
VPS operations
-> tbhrc/skills/gh-vps-operator-maintenance
-> tbhrc/ai-engine trusted Actions -> strict SSH
-> authorised VPS
```

The Mac runner/Codex lane and VPS lane meet only at the common AI Engine privileged-runtime boundary and canonical Skills routing graph.

## Return Path

Every meaningful run returns to the owning GitHub Issue/PR with:

- selected executor (`C1`/`C2` or other provider);
- execution status;
- diff/files/artifacts where relevant;
- checks/tests;
- provider/budget failure if any;
- next action;
- verified outcome before close/merge.
