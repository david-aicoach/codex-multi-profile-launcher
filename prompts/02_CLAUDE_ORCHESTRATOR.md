# Controller / Orchestrator Bridge Prompt

Use this bridge only when a canonical TBHRC work order benefits from a separate local Codex executor and the controller has explicitly selected a profile.

Current control plane:

```text
owning GitHub Issue/PR
-> canonical Skill
-> github-agent-workflow / github-multi-agent-orchestrator
-> controller chooses executor based on task fit, permissions, availability and budget
-> tbhrc/ai-engine when Mac-local execution is required
-> explicit C1 or C2
-> this bridge
-> verified evidence back to GitHub
```

Worker aliases:

```text
C1 = Codex Business = ~/.codex-business
C2 = Codex David    = ~/.codex-david
```

Do not treat C1 or C2 as a permanent hierarchy. Do not automatically rotate accounts or silently fall back.

For a local bounded task:

```bash
bash wrappers/delegate_to_codex.sh \
  --worker C2 \
  --task-file "/absolute/path/to/task.md" \
  --workdir "/absolute/path/to/bounded/worktree"
```

After the run:

1. inspect `runtime/outputs/<TASK-ID>/`;
2. verify the changed files/diff and tests/checks;
3. record the selected worker and outcome in the owning GitHub Issue/PR;
4. apply any durable/external change only through the authority of the owning workflow.

For GitHub-controlled remote dispatch, use `tbhrc/ai-engine#44`; do not invent an arbitrary remote-command path in this repository.
