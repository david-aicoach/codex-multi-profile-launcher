#!/usr/bin/env python3
"""Small, dependency-free utility for the Codex multi-profile launcher."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
ACTIVE_WORKER = RUNTIME / "active_worker.json"
VALID_WORKERS = {
    "C1": "Codex Business",
    "C2": "Codex David",
}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_dirs() -> None:
    for rel in ("outputs", "logs", "tmp", "worktrees"):
        (RUNTIME / rel).mkdir(parents=True, exist_ok=True)


def cmd_activate_worker(args: argparse.Namespace) -> None:
    if args.worker not in VALID_WORKERS:
        raise SystemExit(f"Invalid executable worker: {args.worker}")
    data = {
        "worker_id": args.worker,
        "worker_name": VALID_WORKERS[args.worker],
        "activated_at": now(),
        "codex_home": args.codex_home,
    }
    ACTIVE_WORKER.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f'Activated {data["worker_name"]} ({data["worker_id"]})')


def cmd_validate(args: argparse.Namespace) -> None:
    required = [
        "README.md",
        "AGENTS.md",
        "START_HERE_PROMPT.md",
        "docs/00_MASTER_ARCHITECTURE.md",
        "docs/01_USER_GUIDE.md",
        "docs/02_OPERATING_MODEL.md",
        "docs/03_BUILD_ROADMAP.md",
        "docs/04_GITHUB_REVIEW_ROUTER.md",
        "agents/claude-orchestrator/AGENT.md",
        "agents/codex-business/AGENT.md",
        "agents/codex-david/AGENT.md",
        "config/workers.yaml",
        "config/routing_rules.yaml",
        "config/project_config.toml",
        "config/codex-business.config.toml",
        "config/codex-david.config.toml",
        "prompts/00_CODEX_DAVID_BOOTSTRAP.md",
        "prompts/01_CODEX_BUSINESS_CONTINUE.md",
        "prompts/02_CLAUDE_ORCHESTRATOR.md",
        "prompts/github-pr-review.md",
        "schemas/result.schema.json",
        "schemas/github-review-result.schema.json",
        "scripts/launch-codex-business-desktop.sh",
        "scripts/launch-codex-david-desktop.sh",
        "scripts/start-codex-business.sh",
        "scripts/start-codex-david.sh",
        "scripts/verify-review-runner.sh",
        "wrappers/delegate_to_codex.sh",
        "references/SOURCE_NOTES.md",
        "tools/github_review_router.py",
        "tests/test_github_review_router.py",
        "templates/codex-profile-review-caller.yml",
        ".github/workflows/codex-profile-review.yml",
        ".github/workflows/codex-profile-review-reusable.yml",
        ".github/workflows/validate.yml",
    ]
    errors: list[str] = []
    for rel in required:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"missing: {rel}")
        elif path.is_file() and path.stat().st_size == 0:
            errors.append(f"empty: {rel}")
        elif args.verbose:
            print(f"ok: {rel}")

    for rel in (
        "schemas/result.schema.json",
        "schemas/github-review-result.schema.json",
        "runtime/active_worker.json",
    ):
        path = ROOT / rel
        if path.exists():
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"invalid JSON: {rel}: {exc}")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise SystemExit(1)

    print("Codex multi-profile launcher validation passed.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aosctl")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("activate-worker")
    p.add_argument("worker")
    p.add_argument("--codex-home", required=True)
    p.set_defaults(func=cmd_activate_worker)

    p = sub.add_parser("validate")
    p.add_argument("--verbose", action="store_true")
    p.set_defaults(func=cmd_validate)

    return parser


def main() -> None:
    ensure_dirs()
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
