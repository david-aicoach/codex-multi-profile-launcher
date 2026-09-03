# GitHub PR Review Router

## Purpose

This feature adds **explicit** GitHub pull-request review routing to the two already-isolated Codex profiles:

| Command | Worker | Local Codex home |
|---|---|---|
| `@codex-business review` | C1 / Codex Business | `~/.codex-business` |
| `@codex-david review` | C2 / Codex David | `~/.codex-david` |

Slash aliases are also accepted: `/codex-business review` and `/codex-david review`.

This is not account rotation. The requested profile is deterministic, there is no quota inspection, and failure never falls back to the other profile.

## Security model

The trusted workflow runs on the repository default branch and uses a dedicated self-hosted runner labelled `codex-profile-router`. It does **not** checkout the pull-request branch and does **not** execute PR code. The router fetches PR metadata and the unified diff through the GitHub API, passes that data to Codex as untrusted review input, validates the model result, and posts a normal GitHub COMMENT review.

Important boundaries:

- `auth.json` is never read, copied, printed, uploaded, or stored in GitHub Actions secrets.
- Only `C1 -> ~/.codex-business` and `C2 -> ~/.codex-david` are allowed.
- GitHub comment text is parsed as data and is never interpolated into a shell command.
- A requester must pass the workflow association prefilter and the router's GitHub collaborator-permission check (`write`, `maintain`, or `admin`).
- The model's advisory `verdict` never becomes a GitHub APPROVE or REQUEST_CHANGES action automatically; the router always posts a COMMENT review.
- Automated model execution uses fixed trusted CLI arguments: `--strict-config`, `--ignore-user-config`, `--ephemeral`, `--skip-git-repo-check`, explicit `-C`, `default_permissions=":workspace"`, and `approval_policy="never"`.
- The disposable review directory is the only workspace root available to the model. No legacy `--sandbox read-only` flag is used.
- The native OpenAI `@codex` integration is unchanged.

## Supported commands

```text
@codex-david review
@codex-business review
/codex-david review
/codex-business review
```

Optional review modes:

```text
@codex-david security review
@codex-business review focus: authentication regressions
```

Commands must be a single line. Arbitrary CLI flags, worker IDs, paths, shell operators, and multiline payloads are rejected.

## Runner prerequisite

Use a trusted macOS/Linux runner under the same OS user that owns the existing Codex profiles. Give it the custom label:

```text
codex-profile-router
```

Before enabling the workflow, verify locally:

```bash
bash scripts/verify-review-runner.sh
```

The check uses `codex login status`; it does not inspect credential files.

For an organization-level runner, restrict the runner group to the repositories that are allowed to use the paid local Codex profiles. Do not expose this runner to arbitrary public repositories.

## Workflow architecture

```text
issue_comment on PR
  -> default-branch dispatcher
  -> author-association prefilter
  -> reusable trusted workflow
  -> dedicated self-hosted runner
  -> GitHub permission check
  -> fetch PR metadata + diff via API
  -> select exact C1/C2 CODEX_HOME
  -> codex login status
  -> codex exec in an empty disposable :workspace
       + strict config
       + ignored ambient user config
       + approval_policy=never
       + ephemeral session
  -> validate structured JSON result
  -> POST pull-request COMMENT review
```

The reusable workflow uses an immutable pinned `actions/checkout` commit and always checks out `tbhrc/codex-multi-profile-launcher` from `main`, not the PR branch. This prevents a fork PR from changing the router code that runs next to authenticated Codex profiles.

## Cross-repository rollout

The reusable workflow can service other TBHRC repositories. Copy `templates/codex-profile-review-caller.yml` into the target repository as `.github/workflows/codex-profile-review.yml`.

For production hardening across many repositories, pin the reusable workflow reference to a reviewed release tag or immutable commit SHA instead of `@main`.

The caller repository supplies its own scoped `GITHUB_TOKEN`; the central router does not need a personal access token.

## Review behavior

Codex receives:

- repository and PR metadata;
- base/head refs and SHAs;
- the PR unified diff;
- optional review focus;
- explicit instructions that the diff is untrusted data.

Codex runs from an empty temporary work directory under the built-in `:workspace` permission profile with network restricted by that profile and no interactive approval route. Ambient user config is ignored and the session is ephemeral. The target PR is never cloned or executed.

The router validates these result fields before posting:

```json
{
  "profile": "C2",
  "summary": "...",
  "verdict": "comment",
  "findings": [
    {
      "severity": "P1",
      "title": "...",
      "body": "...",
      "path": "src/file.py",
      "line": 42
    }
  ],
  "warnings": []
}
```

If inline placement cannot be proven, findings remain in the top-level PR review rather than guessing an inline diff position.

## Diff limit

The router currently sends up to 1.2 MB of unified diff text. Larger diffs are truncated and the final review is marked with a limitation warning. This keeps the router bounded and avoids silently sending unlimited PR content to one review call.

## Runtime evidence

Each run writes local, gitignored evidence under:

```text
runtime/outputs/GH-<owner>-<repo>-PR-<number>-<run-id>-<worker>/
  status.json
  summary.md
  events.jsonl
  run.log
  artifacts/
    pr-metadata.json
    review-result.raw.txt
    review-result.json
  error.md        # failure only
```

Successful `status.json` also records the permission profile, approval policy, ignored ambient user config, and ephemeral session policy. The PR diff itself is not persisted by the router.

## Failure behavior

If the selected profile is missing, logged out, out of credits, times out, returns invalid JSON, or fails for any other expected reason, the router posts a sanitized failure message and stops.

Example:

```text
Codex David review could not complete: Codex David local profile is not authenticated on this runner. No alternate Codex profile was used.
```

It never silently retries with the other paid account.

## Usage attribution verification

Repository code can prove which local `CODEX_HOME` was selected, but it cannot independently query ChatGPT Business billing attribution without relying on non-public account APIs. Verify first-use attribution from observed account usage and the durable routed profile evidence. Do not add quota scraping or automatic account switching.

## Tests

Run:

```bash
python3 tools/aosctl.py validate --verbose
python3 -m unittest discover -s tests -v
bash -n scripts/verify-review-runner.sh
```

The unit suite covers command routing, malformed input, shell-injection-shaped comments, arbitrary worker/path rejection, event parsing, exact C1/C2 mappings, the fixed least-privilege Codex invocation, structured result validation, profile mismatch, severity validation, no-findings output, and schema loading.
