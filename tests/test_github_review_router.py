import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import github_review_router as router  # noqa: E402


class CommandParsingTests(unittest.TestCase):
    def test_david_routes_to_c2(self):
        cmd = router.parse_review_command("@codex-david review")
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.worker_id, "C2")
        self.assertEqual(cmd.review_type, "standard")

    def test_business_routes_to_c1(self):
        cmd = router.parse_review_command("@codex-business review")
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.worker_id, "C1")

    def test_slash_alias(self):
        cmd = router.parse_review_command("/codex-david security review")
        self.assertEqual(cmd.worker_id, "C2")
        self.assertEqual(cmd.review_type, "security")

    def test_focus_is_preserved(self):
        cmd = router.parse_review_command("@codex-business review focus: regressions in auth")
        self.assertEqual(cmd.focus, "regressions in auth")

    def test_unrelated_comment_is_ignored(self):
        self.assertIsNone(router.parse_review_command("looks good"))

    def test_multiline_and_shell_injection_are_rejected(self):
        bad = [
            "@codex-david review\nrm -rf ~",
            "@codex-david review; rm -rf ~",
            "@codex-david review && env",
            "@codex-david review $(cat ~/.codex-david/auth.json)",
            "@codex-david review > /tmp/x",
        ]
        for value in bad:
            with self.subTest(value=value):
                self.assertIsNone(router.parse_review_command(value))

    def test_no_arbitrary_worker_or_home(self):
        self.assertIsNone(router.parse_review_command("@codex-c3 review"))
        self.assertIsNone(router.parse_review_command("@codex-david review --codex-home=/tmp/x"))


class EventTests(unittest.TestCase):
    def test_non_pr_event_is_ignored(self):
        event = {"issue": {"number": 2}, "comment": {"body": "@codex-david review"}}
        self.assertIsNone(router.parse_event(event, "1"))

    def test_pr_event_parses(self):
        event = {
            "repository": {"full_name": "tbhrc/example"},
            "issue": {"number": 3, "pull_request": {"url": "x"}},
            "comment": {"id": 9, "body": "@codex-business review", "user": {"login": "tbhrc"}},
        }
        ctx = router.parse_event(event, "123")
        self.assertEqual(ctx.repository, "tbhrc/example")
        self.assertEqual(ctx.command.worker_id, "C1")


class SecurityInvocationTests(unittest.TestCase):
    def test_exact_profile_mapping(self):
        self.assertEqual(router.WORKERS["C2"]["home"], "~/.codex-david")
        self.assertEqual(router.WORKERS["C1"]["home"], "~/.codex-business")

    def test_review_exec_uses_permission_profile_not_legacy_sandbox(self):
        workdir = Path("/tmp/review-work")
        raw_result = Path("/tmp/review-result.json")
        command = router.secure_exec_command(workdir, raw_result)
        self.assertEqual(command[:2], ["codex", "exec"])
        self.assertIn("--strict-config", command)
        self.assertIn("--ignore-user-config", command)
        self.assertIn("--ephemeral", command)
        self.assertIn("--skip-git-repo-check", command)
        self.assertIn("-C", command)
        self.assertEqual(command[command.index("-C") + 1], str(workdir))
        self.assertIn('default_permissions=":workspace"', command)
        self.assertIn('approval_policy="never"', command)
        self.assertNotIn("--sandbox", command)
        self.assertEqual(command[-1], "-")


class ResultValidationTests(unittest.TestCase):
    def valid_result(self):
        return {
            "profile": "C2",
            "summary": "Found one issue.",
            "verdict": "comment",
            "findings": [
                {
                    "severity": "P1",
                    "title": "Broken guard",
                    "body": "The new branch bypasses authorization.",
                    "path": "src/auth.py",
                    "line": 42,
                }
            ],
            "warnings": [],
        }

    def test_valid_result(self):
        result = router.parse_and_validate_result(json.dumps(self.valid_result()), "C2")
        self.assertEqual(result["findings"][0]["severity"], "P1")

    def test_markdown_fenced_json_is_tolerated(self):
        text = "```json\n" + json.dumps(self.valid_result()) + "\n```"
        result = router.parse_and_validate_result(text, "C2")
        self.assertEqual(result["profile"], "C2")

    def test_wrong_profile_fails_closed(self):
        with self.assertRaises(router.RouterError):
            router.parse_and_validate_result(json.dumps(self.valid_result()), "C1")

    def test_invalid_severity_fails(self):
        data = self.valid_result()
        data["findings"][0]["severity"] = "P9"
        with self.assertRaises(router.RouterError):
            router.parse_and_validate_result(json.dumps(data), "C2")

    def test_boolean_line_is_not_accepted_as_integer(self):
        data = self.valid_result()
        data["findings"][0]["line"] = True
        with self.assertRaises(router.RouterError):
            router.parse_and_validate_result(json.dumps(data), "C2")

    def test_no_findings_rendering(self):
        data = self.valid_result()
        data["findings"] = []
        cmd = router.parse_review_command("@codex-david review")
        rendered = router.render_review(data, cmd, False)
        self.assertIn("No blocking P0-P2", rendered)
        self.assertIn("C2 / Codex David", rendered)

    def test_schema_file_is_valid_json(self):
        schema = json.loads((ROOT / "schemas" / "github-review-result.schema.json").read_text())
        self.assertEqual(schema["type"], "object")


if __name__ == "__main__":
    unittest.main()
