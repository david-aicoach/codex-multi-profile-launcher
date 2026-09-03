# Roadmap

## Stage 0 - Simplify

- keep this repository a profile-isolation/runtime bridge only;
- use the established `C1` and `C2` aliases consistently;
- keep GitHub Issues/PRs as durable work records;
- keep reusable operating method in `tbhrc/skills`;
- keep validation and tests passing.

Exit: docs, config, scripts and tests agree on the lean bridge boundary.

## Stage 1 - Reliable Local Profiles

- bootstrap `~/.codex-business` for C1;
- bootstrap `~/.codex-david` for C2;
- verify each profile can report login status;
- preserve profile isolation and never move credentials between homes.

Exit: both profiles can be started intentionally without credential mixing.

## Stage 2 - Local Task Execution

- use `delegate_to_codex.sh` for explicit C1/C2 task files;
- preserve output evidence under `runtime/outputs/`;
- keep one active task per selected profile unless real evidence supports more concurrency;
- keep lock files to prevent duplicate runs;
- return compact status/diff/test evidence to the controlling agent.

Exit: a bounded local task can be delegated explicitly to C1 or C2 and verified by the controller.

## Stage 3 - GitHub / AI Engine Adoption

- route work from canonical Skills + owning GitHub Issue/PR;
- keep provider/budget selection in the controller/orchestrator;
- expose Mac-local execution only through trusted `tbhrc/ai-engine` workflows;
- do not create an arbitrary remote shell or automatic account-rotation mechanism;
- initial general work-order lane returns local patch/result/evidence rather than independently pushing/deploying.

Tracking: `tbhrc/ai-engine#44` and `tbhrc/skills#224`.

Exit: an authorised controller can use the Mac/C1/C2 capability without David manually switching accounts while GitHub remains the durable control plane.

## Stage 4 - Optional Hardening

- add stronger validation for task/worktree inputs only where needed;
- improve result summaries and patch handoff;
- add tests for wrapper/dispatch failure modes;
- harden worktree isolation if real collisions occur;
- add capacity/status checks without converting them into hidden automatic profile fallback.

Exit: hardening exists only where repeated operational use proves it is needed.
