# Start Here

This package is the local Codex C1/C2 profile-isolation and execution bridge.

## 1. Bootstrap the two isolated Codex homes

```bash
cd codex-multi-profile-launcher
bash scripts/bootstrap.sh
```

## 2. Authenticate the profiles you need

```bash
bash scripts/auth-codex-business.sh   # C1 -> ~/.codex-business
bash scripts/auth-codex-david.sh      # C2 -> ~/.codex-david
```

Never copy authentication between profiles and never read/print `auth.json`.

## 3. Keep real work in GitHub

TBHRC durable work belongs in the owning GitHub repository and controlling Issue/PR. Reusable HOW belongs in `tbhrc/skills`. Remote privileged access to this Mac-local bridge belongs in `tbhrc/ai-engine`.

Use the current routing chain:

```text
GitHub work order
-> canonical Skill
-> controller/orchestrator chooses an authorised executor
-> if Mac-local Codex is required: tbhrc/ai-engine
-> explicit C1 or C2
-> this launcher
-> verified evidence back to GitHub
```

## 4. Local manual dispatch

For a bounded local worktree/task file:

```bash
bash wrappers/delegate_to_codex.sh \
  --worker C2 \
  --task-file "/absolute/path/to/task.md" \
  --workdir "/absolute/path/to/bounded/worktree"
```

Worker mapping is fixed:

```text
C1 = Codex Business = ~/.codex-business
C2 = Codex David    = ~/.codex-david
```

Do not use a permanent C1-first/C2-second hierarchy. The controller explicitly selects a profile based on task fit, permissions, current availability and remaining budget. The launcher never performs automatic account rotation or silent fallback.

For GitHub-controlled general work-order dispatch, follow `tbhrc/ai-engine#44`; do not invent a direct remote-control path in this repository.
