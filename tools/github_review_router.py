#!/usr/bin/env python3
"""Route GitHub PR reviews to one explicit, isolated Codex profile."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
PROMPT = ROOT / "prompts" / "github-pr-review.md"
WORKERS = {
    "C1": {"name": "Codex Business", "home": "~/.codex-business"},
    "C2": {"name": "Codex David", "home": "~/.codex-david"},
}
COMMANDS = {
    "@codex-business": "C1", "/codex-business": "C1",
    "@codex-david": "C2", "/codex-david": "C2",
}
PERMISSIONS = {"write", "maintain", "admin"}
VERDICTS = {"comment", "approve", "request_changes"}
SEVERITIES = {"P0", "P1", "P2", "P3"}
MAX_DIFF = 1_200_000
MAX_BODY = 60_000
COMMAND_RE = re.compile(
    r"^(?P<command>@codex-(?:david|business)|/codex-(?:david|business))\s+"
    r"(?P<mode>review|security\s+review)(?:\s+focus:\s*(?P<focus>[^\r\n]{1,200}))?$"
)


class RouterError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReviewCommand:
    worker_id: str
    worker_name: str
    trigger: str
    review_type: str
    focus: str | None = None


@dataclass(frozen=True)
class EventContext:
    repository: str
    pr_number: int
    comment_id: int
    commenter: str
    command: ReviewCommand
    run_id: str


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def split_repo(repository: str) -> tuple[str, str]:
    parts = repository.split("/", 1)
    if len(parts) != 2 or not all(parts):
        raise RouterError("Repository name is invalid.")
    return parts[0], parts[1]


def parse_review_command(body: str) -> ReviewCommand | None:
    if not isinstance(body, str):
        return None
    body = body.strip()
    if not body or "\n" in body or "\r" in body:
        return None
    match = COMMAND_RE.fullmatch(body)
    if not match:
        return None
    trigger = match.group("command")
    worker_id = COMMANDS.get(trigger)
    if not worker_id:
        return None
    focus = (match.group("focus") or "").strip() or None
    mode = "security" if match.group("mode").startswith("security") else "standard"
    return ReviewCommand(worker_id, WORKERS[worker_id]["name"], body, mode, focus)


def parse_event(event: dict[str, Any], run_id: str) -> EventContext | None:
    issue, comment = event.get("issue") or {}, event.get("comment") or {}
    if not issue.get("pull_request"):
        return None
    command = parse_review_command(comment.get("body", ""))
    if command is None:
        return None
    repository = ((event.get("repository") or {}).get("full_name") or "").strip()
    commenter = ((comment.get("user") or {}).get("login") or "").strip()
    pr_number, comment_id = issue.get("number"), comment.get("id")
    if not repository or not commenter or not isinstance(pr_number, int) or not isinstance(comment_id, int):
        raise RouterError("GitHub event is missing required pull-request metadata.")
    return EventContext(repository, pr_number, comment_id, commenter, command, str(run_id or "manual"))


def api(method: str, path: str, token: str, *, accept="application/vnd.github+json", payload=None):
    if not token:
        raise RouterError("GitHub token is unavailable to the review router.")
    headers = {
        "Accept": accept,
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "codex-profile-review-router",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"https://api.github.com{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read()
            content_type = response.headers.get("content-type", "")
    except urllib.error.HTTPError as exc:
        raise RouterError(f"GitHub API request failed with HTTP {exc.code}.") from None
    except urllib.error.URLError:
        raise RouterError("GitHub API request could not be completed.") from None
    return json.loads(raw.decode() or "null") if "json" in content_type else raw.decode(errors="replace")


def permission(repository: str, username: str, token: str) -> str:
    owner, repo = split_repo(repository)
    user = urllib.parse.quote(username)
    data = api("GET", f"/repos/{owner}/{repo}/collaborators/{user}/permission", token)
    return str((data or {}).get("permission") or "none").lower()


def pr_metadata(repository: str, number: int, token: str) -> dict[str, Any]:
    owner, repo = split_repo(repository)
    data = api("GET", f"/repos/{owner}/{repo}/pulls/{number}", token)
    return {
        "number": number,
        "title": str(data.get("title") or ""),
        "author": str((data.get("user") or {}).get("login") or ""),
        "base_ref": str((data.get("base") or {}).get("ref") or ""),
        "base_sha": str((data.get("base") or {}).get("sha") or ""),
        "head_ref": str((data.get("head") or {}).get("ref") or ""),
        "head_sha": str((data.get("head") or {}).get("sha") or ""),
        "head_repo": str(((data.get("head") or {}).get("repo") or {}).get("full_name") or ""),
        "draft": bool(data.get("draft")),
    }


def pr_diff(repository: str, number: int, token: str) -> tuple[str, bool]:
    owner, repo = split_repo(repository)
    text = api("GET", f"/repos/{owner}/{repo}/pulls/{number}", token, accept="application/vnd.github.v3.diff")
    if not isinstance(text, str):
        raise RouterError("GitHub returned an invalid pull-request diff.")
    raw = text.encode()
    return (text, False) if len(raw) <= MAX_DIFF else (raw[:MAX_DIFF].decode(errors="ignore"), True)


def react(repository: str, comment_id: int, content: str, token: str) -> None:
    owner, repo = split_repo(repository)
    api("POST", f"/repos/{owner}/{repo}/issues/comments/{comment_id}/reactions", token, payload={"content": content})


def comment(repository: str, number: int, body: str, token: str) -> None:
    owner, repo = split_repo(repository)
    api("POST", f"/repos/{owner}/{repo}/issues/{number}/comments", token, payload={"body": body[:MAX_BODY]})


def post_review(repository: str, number: int, body: str, token: str) -> None:
    owner, repo = split_repo(repository)
    # Always COMMENT; model verdict is advisory and cannot approve/request changes automatically.
    api("POST", f"/repos/{owner}/{repo}/pulls/{number}/reviews", token, payload={"body": body[:MAX_BODY], "event": "COMMENT"})


def profile_home(worker_id: str) -> Path:
    if worker_id not in WORKERS:
        raise RouterError("Requested Codex worker is not allowlisted.")
    path = Path(os.path.expanduser(WORKERS[worker_id]["home"])).resolve()
    if Path.home().resolve() not in path.parents:
        raise RouterError("Configured Codex profile path is outside the runner user home.")
    return path


def verify_profile(worker_id: str) -> Path:
    home = profile_home(worker_id)
    name = WORKERS[worker_id]["name"]
    if not home.is_dir():
        raise RouterError(f"{name} local profile is not ready on this runner.")
    if shutil.which("codex") is None:
        raise RouterError("Codex CLI is not installed on the self-hosted runner.")
    env = os.environ.copy(); env["CODEX_HOME"] = str(home)
    try:
        result = subprocess.run(["codex", "login", "status"], cwd=ROOT, env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise RouterError(f"{name} authentication status could not be verified.") from None
    if result.returncode:
        raise RouterError(f"{name} local profile is not authenticated on this runner.")
    return home


def build_prompt(command: ReviewCommand, repository: str, pr: dict[str, Any], diff: str, truncated: bool) -> str:
    if not PROMPT.is_file():
        raise RouterError("Review prompt template is missing.")
    focus = command.focus or "No additional focus requested."
    metadata = dict(pr, repository=repository, review_type=command.review_type,
                    focus=focus, diff_truncated=truncated)
    notice = ("WARNING: GitHub diff exceeded the router size limit and was truncated. State this limitation in warnings."
              if truncated else "The supplied GitHub diff was not truncated by the router.")
    text = PROMPT.read_text()
    for key, value in {
        "{{PROFILE}}": command.worker_id, "{{PROFILE_NAME}}": command.worker_name,
        "{{REVIEW_TYPE}}": command.review_type, "{{FOCUS}}": focus,
        "{{TRUNCATION_NOTICE}}": notice,
        "{{PR_METADATA_JSON}}": json.dumps(metadata, indent=2), "{{PR_DIFF}}": diff,
    }.items():
        text = text.replace(key, value)
    return text


def extract_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines(); text = "\n".join(lines[1:-1]).strip()
    first, last = text.find("{"), text.rfind("}")
    if first < 0 or last < first:
        raise RouterError("Codex review output was not valid structured JSON.")
    return text[first:last + 1]


def parse_and_validate_result(text: str, expected_worker: str) -> dict[str, Any]:
    try:
        data = json.loads(extract_json(text))
    except json.JSONDecodeError:
        raise RouterError("Codex review output was not valid structured JSON.") from None
    if not isinstance(data, dict) or set(data) != {"profile", "summary", "verdict", "findings", "warnings"}:
        raise RouterError("Codex review output contains unexpected or missing top-level fields.")
    if data["profile"] != expected_worker:
        raise RouterError("Codex review output reported the wrong routed profile.")
    if not isinstance(data["summary"], str) or not data["summary"].strip() or data["verdict"] not in VERDICTS:
        raise RouterError("Codex review output contains an invalid summary or verdict.")
    if not isinstance(data["findings"], list) or not isinstance(data["warnings"], list) or not all(isinstance(w, str) for w in data["warnings"]):
        raise RouterError("Codex review output contains invalid findings or warnings.")
    clean = []
    for item in data["findings"]:
        if not isinstance(item, dict) or set(item) != {"severity", "title", "body", "path", "line"}:
            raise RouterError("Codex review output contains an invalid finding.")
        if item["severity"] not in SEVERITIES or not isinstance(item["title"], str) or not item["title"].strip() or not isinstance(item["body"], str) or not item["body"].strip():
            raise RouterError("Codex review output contains an incomplete finding.")
        if item["path"] is not None and not isinstance(item["path"], str):
            raise RouterError("Codex review output contains an invalid file path.")
        if item["line"] is not None and (not isinstance(item["line"], int) or isinstance(item["line"], bool) or item["line"] <= 0):
            raise RouterError("Codex review output contains an invalid line number.")
        clean.append({"severity": item["severity"], "title": item["title"].strip(),
                      "body": item["body"].strip(), "path": item["path"].strip() if isinstance(item["path"], str) and item["path"].strip() else None,
                      "line": item["line"]})
    return {"profile": data["profile"], "summary": data["summary"].strip(), "verdict": data["verdict"],
            "findings": clean, "warnings": [w.strip() for w in data["warnings"] if w.strip()]}


def run_codex(worker_id: str, prompt: str, output: Path) -> dict[str, Any]:
    home, name = verify_profile(worker_id), WORKERS[worker_id]["name"]
    artifacts = output / "artifacts"; artifacts.mkdir(parents=True, exist_ok=True)
    workdir = RUNTIME / "tmp" / f"review-{output.name}"; workdir.mkdir(parents=True, exist_ok=True)
    raw_result = artifacts / "review-result.raw.txt"
    env = os.environ.copy(); env.update(CODEX_HOME=str(home), CODEX_BRIDGE_WORKER_ID=worker_id, CODEX_BRIDGE_WORKER_NAME=name)
    started = now()
    try:
        with (output / "events.jsonl").open("w") as out, (output / "run.log").open("w") as err:
            result = subprocess.run(["codex", "exec", "-", "--sandbox", "read-only", "--json",
                                     "--output-last-message", str(raw_result)], input=prompt, text=True,
                                    cwd=workdir, env=env, stdout=out, stderr=err, timeout=1800, check=False)
    except subprocess.TimeoutExpired:
        raise RouterError(f"{name} review exceeded the execution timeout.") from None
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    if result.returncode or not raw_result.is_file():
        raise RouterError(f"{name} review failed before producing a usable result.")
    parsed = parse_and_validate_result(raw_result.read_text(), worker_id)
    (artifacts / "review-result.json").write_text(json.dumps(parsed, indent=2) + "\n")
    (output / "status.json").write_text(json.dumps({
        "task_id": output.name, "worker_id": worker_id, "worker_name": name, "status": "success",
        "started_at": started, "finished_at": now(), "exit_code": 0,
        "artifacts": ["artifacts/review-result.json"], "errors": [], "tests": [], "review_recommended": False,
    }, indent=2) + "\n")
    return parsed


def render_review(result: dict[str, Any], command: ReviewCommand, truncated: bool) -> str:
    lines = [f"### {command.worker_name} Review", "", result["summary"], ""]
    if result["findings"]:
        lines += ["#### Findings", ""]
        for finding in result["findings"]:
            location = f" — `{finding['path']}`" if finding["path"] else ""
            if location and finding["line"]: location += f":{finding['line']}"
            lines += [f"- **{finding['severity']} — {finding['title']}**{location}", f"  {finding['body']}"]
    else:
        lines += ["No blocking P0-P2 findings were identified in the supplied diff.", ""]
    warnings = list(result["warnings"])
    if truncated and not any("trunc" in w.lower() for w in warnings):
        warnings.append("The PR diff exceeded the router size limit and was truncated before review.")
    if warnings:
        lines += ["", "#### Limitations", ""] + [f"- {w}" for w in warnings]
    lines += ["", "---", f"Routed profile: **{command.worker_id} / {command.worker_name}**",
              f"Trigger: `{command.trigger}`",
              "This is an explicitly routed Codex CLI review, not the native OpenAI `@codex` GitHub review bot."]
    return "\n".join(lines)[:MAX_BODY]


def task_id(ctx: EventContext) -> str:
    run = re.sub(r"[^A-Za-z0-9_.-]+", "-", ctx.run_id)[:64]
    return f"GH-{ctx.repository.replace('/', '-')}-PR-{ctx.pr_number}-{run}-{ctx.command.worker_id}"[:160]


def handle_event(event_path: Path, token: str, run_id: str) -> int:
    ctx = parse_event(json.loads(event_path.read_text()), run_id)
    if ctx is None:
        print("No supported Codex profile review command found; nothing to do."); return 0
    requester_permission = permission(ctx.repository, ctx.commenter, token)
    if requester_permission not in PERMISSIONS:
        print("Review command ignored because requester lacks write-level repository permission."); return 0
    try:
        react(ctx.repository, ctx.comment_id, "eyes", token)
    except RouterError:
        pass
    output = RUNTIME / "outputs" / task_id(ctx); output.mkdir(parents=True, exist_ok=True)
    try:
        pr = pr_metadata(ctx.repository, ctx.pr_number, token)
        diff, truncated = pr_diff(ctx.repository, ctx.pr_number, token)
        artifacts = output / "artifacts"; artifacts.mkdir(parents=True, exist_ok=True)
        (artifacts / "pr-metadata.json").write_text(json.dumps({"repository": ctx.repository, "pull_request": pr,
            "worker_id": ctx.command.worker_id, "worker_name": ctx.command.worker_name,
            "review_type": ctx.command.review_type, "focus": ctx.command.focus,
            "requester_permission": requester_permission}, indent=2) + "\n")
        result = run_codex(ctx.command.worker_id, build_prompt(ctx.command, ctx.repository, pr, diff, truncated), output)
        body = render_review(result, ctx.command, truncated)
        (output / "summary.md").write_text(body + "\n")
        post_review(ctx.repository, ctx.pr_number, body, token)
        try: react(ctx.repository, ctx.comment_id, "+1", token)
        except RouterError: pass
        print(f"Posted {ctx.command.worker_name} review for {ctx.repository}#{ctx.pr_number}."); return 0
    except RouterError as exc:
        message = f"{ctx.command.worker_name} review could not complete: {exc} No alternate Codex profile was used."
        try: comment(ctx.repository, ctx.pr_number, message, token)
        except RouterError: pass
        (output / "error.md").write_text(f"# Review failure\n\n{exc}\n")
        (output / "status.json").write_text(json.dumps({"task_id": output.name, "worker_id": ctx.command.worker_id,
            "worker_name": ctx.command.worker_name, "status": "failed", "finished_at": now(), "exit_code": 1,
            "artifacts": [], "errors": [str(exc)], "tests": [], "review_recommended": True}, indent=2) + "\n")
        print(message, file=sys.stderr); return 1


def main() -> None:
    parser = argparse.ArgumentParser(prog="github_review_router")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("parse-command"); p.add_argument("--body", required=True)
    p = sub.add_parser("validate-result"); p.add_argument("--path", required=True); p.add_argument("--worker", choices=sorted(WORKERS), required=True)
    p = sub.add_parser("handle-event"); p.add_argument("--event-path", required=True)
    args = parser.parse_args()
    if args.command == "parse-command":
        parsed = parse_review_command(args.body)
        if parsed is None: raise SystemExit(2)
        print(json.dumps(parsed.__dict__, indent=2))
    elif args.command == "validate-result":
        print(json.dumps(parse_and_validate_result(Path(args.path).read_text(), args.worker), indent=2))
    else:
        raise SystemExit(handle_event(Path(args.event_path), os.environ.get("GITHUB_TOKEN", ""), os.environ.get("GITHUB_RUN_ID", "manual")))


if __name__ == "__main__":
    main()
