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
| `C2` | Codex David | `~/.codex-david` | Authenticated; real model/review execution proven through the AI Engine Mac runner. |

The default `~/.codex` profile may coexist on the Mac. It is not the C2 alias.

## Existing Capabilities

### Local general executor

`wrappers/delegate_to_codex.sh` supports:

```text
explicit C1/C2 selection
-> exact CODEX_HOME for authentication
-> bounded task file + workdir
-> codex exec with strict deterministic automation policy
   -> --ignore-user-config
   -> --ephemeral
   -> explicit -C workdir
   -> default_permissions=":workspace"
   -> approval_policy="never"
   -> no legacy --sandbox mode
-> local status/summary/log/event evidence
```

The launcher fails closed on the selected identity and never rotates accounts.

### GitHub PR-review router

The review router uses the same hardened automated Codex boundary in an empty disposable review workspace.

```text
@codex-business review -> C1
@codex-david review    -> C2
```

It fetches PR metadata/diffs as data through GitHub's API, never checks out or executes PR code, and never silently falls back between profiles.

### General work-order integration

The GitHub-controlled general work-order adapter is owned by `tbhrc/ai-engine#44`.

Its target architecture is:

```text
owning GitHub work order
-> canonical Skill
-> explicit executor choice
-> trusted AI Engine workflow on main
-> existing Mac runner
-> exact C1/C2
-> trusted launcher main + hardened-policy preflight
-> bounded local worktree
-> fixed :workspace/no-approval/ephemeral Codex execution
-> private short-lived patch/result/evidence
-> controller verifies
-> owning repository performs normal branch/PR/apply/merge lifecycle
```

The Codex worker does **not** independently push, merge, deploy, send messages or mutate production systems.

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
- arbitrary remote shell control;
- ambient profile config as the authority source for automated execution.

## Security Boundary

For automation, the selected `CODEX_HOME` supplies authentication only. Trusted launcher code fixes the execution policy. Prompt instructions are defense in depth, not the filesystem/network boundary.

The production boundary must be backed by live Mac evidence that:

- the installed Codex CLI accepts the permission profile;
- work inside the assigned workspace can be written when required;
- unrelated sibling/home canaries cannot be read by the sandbox boundary;
- network is denied by the selected profile;
- no real credential/auth file is touched during proof.

That proof is tracked in `tbhrc/ai-engine#48`.

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
- permission/session policy where relevant;
- provider/budget failure if any;
- next action;
- verified outcome before close/merge.
