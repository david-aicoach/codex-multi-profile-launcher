# User Guide

## 1. Bootstrap

```bash
cd codex-multi-profile-launcher
bash scripts/bootstrap.sh
```

This creates the two isolated Codex homes if missing:

```text
~/.codex-business
~/.codex-david
```

It copies safe config files only. It does not create or copy credentials.

## 2. Authenticate Profiles

Authenticate `C1 / Codex Business`:

```bash
bash scripts/auth-codex-business.sh
```

Authenticate `C2 / Codex David`:

```bash
bash scripts/auth-codex-david.sh
```

Do not copy `auth.json` between homes. Do not place `auth.json` in this repo.

## 3. Check Status

```bash
bash scripts/status.sh
```

Login status proves authentication only. It does not prove that the account currently has model budget/credits.

## 4. Start an Interactive Profile

Start C1:

```bash
bash scripts/start-codex-business.sh
```

Start C2:

```bash
bash scripts/start-codex-david.sh
```

Profile selection is explicit. The controller decides which seat is appropriate based on task fit, permissions, current availability and remaining budget. The launcher never automatically rotates accounts.

## 4a. Use Dock Launchers

The macOS launcher apps are:

```text
~/Applications/Codex C1 Business.app
~/Applications/Codex C2 David.app
```

Drag either app to the Dock. These launchers keep both the Codex CLI home and desktop app data separate from the regular app and from each other.

Exact runtime aliases:

```text
C1 = Codex Business = ~/.codex-business
C2 = Codex David    = ~/.codex-david
```

The normal/default `~/.codex` profile is separate and is not the `C2` alias.

## 5. Run a Local Delegated Task

The durable task/work order should live in the owning GitHub repository as an Issue/PR. For a local Codex run, create or materialise the bounded task instructions/worktree locally, then invoke the wrapper explicitly:

```bash
bash wrappers/delegate_to_codex.sh \
  --worker C2 \
  --task-file "/absolute/path/to/task.md" \
  --workdir "/absolute/path/to/bounded/worktree"
```

Use `--worker C1` only when the controller has explicitly selected the Business identity.

The wrapper performs local workspace-write execution only. It is not authority to push, deploy, send messages or mutate external systems.

For remote/controller-driven GitHub dispatch to this Mac runtime, use the trusted AI Engine path being established in `tbhrc/ai-engine#44`. Do not expose a direct arbitrary-command bridge from this repository.

## 6. Read Results

The wrapper writes:

```text
runtime/outputs/<TASK-ID>/
  status.json
  summary.md
  run.log
  events.jsonl
  artifacts/
  error.md      # failure only
```

The controlling agent should inspect the result, verify changed files/tests as appropriate, then record the outcome and next action in the owning GitHub Issue/PR.

`runtime/outputs/` is execution evidence, not the durable task tracker.

## 7. Troubleshooting

If both workers appear to use the same account, check:

```bash
CODEX_HOME="$HOME/.codex-business" codex login status
CODEX_HOME="$HOME/.codex-david" codex login status
```

If a real C1 model call fails while login status succeeds, check the exact error before treating it as infrastructure failure. On 3 September 2026, C1 was authenticated but the Business workspace returned:

```text
ERROR: Your workspace is out of credits. Add credits to continue.
```

That state must fail closed; do not silently reroute inside the launcher.

If validation fails:

```bash
python3 tools/aosctl.py validate --verbose
```
