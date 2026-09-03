# Controller / Orchestrator Bridge Note

This file is retained at its historical path for compatibility. It no longer defines a Larry-specific Claude Code control plane.

TBHRC orchestration now lives in GitHub and canonical Skills:

```text
founder/user request
-> owning GitHub repository + Issue/PR
-> canonical Skill in tbhrc/skills
-> github-agent-workflow / github-multi-agent-orchestrator
-> authorised controller chooses executor
-> tbhrc/ai-engine when trusted Mac-local execution is required
-> explicit C1 or C2 through this bridge
-> verified evidence returned to the owning work record
```

The controller owns:

- user/founder intent;
- work-order and repository routing;
- provider/seat choice based on task fit, permissions, availability and budget;
- deciding whether local Codex dispatch is worth the boundary/cold-start cost;
- explicit `C1` or `C2` selection;
- verification of the result;
- applying authorised durable changes through the owning repository workflow;
- final synthesis and handoff.

This bridge owns only Codex profile isolation and bounded local execution.

Do not duplicate the Skill Bank, GitHub Issue state, provider routing policy, or durable work tracker here.

Canonical references:

- https://github.com/tbhrc/skills/tree/main/human-ai-operations-map
- https://github.com/tbhrc/skills/tree/main/github-agent-workflow
- https://github.com/tbhrc/skills/tree/main/github-multi-agent-orchestrator
- https://github.com/tbhrc/skills/tree/main/gh-mac-runner-operator-maintenance
- https://github.com/tbhrc/ai-engine
