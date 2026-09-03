# Source Notes

Historical local task-workspace and Larry orchestration pointers in this repository are retired.

Current TBHRC navigation:

- reusable operating methods: `tbhrc/skills`
- durable work state: the owning GitHub repository and controlling Issue/PR
- cross-repository execution lifecycle: `tbhrc/skills/github-agent-workflow`
- multi-agent/provider routing: `tbhrc/skills/github-multi-agent-orchestrator`
- Mac runner operations: `tbhrc/skills/gh-mac-runner-operator-maintenance`
- privileged runtime infrastructure: `tbhrc/ai-engine`

This launcher retains only the local Codex profile-isolation/runtime capability:

```text
C1 / Codex Business -> ~/.codex-business
C2 / Codex David    -> ~/.codex-david
```

General GitHub-controlled C1/C2 work-order exposure is tracked in `tbhrc/ai-engine#44`. Canonical provider-failover discovery is tracked in `tbhrc/skills#224`.
