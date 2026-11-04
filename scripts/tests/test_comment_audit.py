from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("comment_audit_under_test", REPO_ROOT / "scripts" / "comment-audit.py")
assert SPEC and SPEC.loader
audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = audit
SPEC.loader.exec_module(audit)


class CommentAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="t-tools-comment-audit-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "work"
        self.root.mkdir()
        self.command("git", "init", "-b", "main")
        self.command("git", "config", "user.name", "Audit Test")
        self.command("git", "config", "user.email", "audit-test@example.invalid")
        (self.root / "base.txt").write_text("base\n", encoding="utf-8")
        self.command("git", "add", ".")
        self.command("git", "commit", "-m", "base")
        self.addCleanup(patch.stopall)
        patch.object(audit, "REPO_ROOT", self.root).start()

    def command(self, *args: str) -> subprocess.CompletedProcess:
        result = subprocess.run(args, cwd=self.root, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def write(self, relpath: str, content: str) -> Path:
        target = self.root / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def run_audit(self, *extra: str) -> dict:
        output = io.StringIO()
        with redirect_stdout(output):
            code = audit.main([*extra])
        self.assertEqual(code, 0, output.getvalue())
        return json.loads(output.getvalue())

    def findings(self, report: dict, **match: str) -> list[dict]:
        return [f for f in report["findings"] if all(f.get(k) == v for k, v in match.items())]

    def test_no_changes_reports_empty(self) -> None:
        report = self.run_audit()
        self.assertEqual(report["summary"]["changed_source_files"], 0)
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["density"], [])

    def test_narration_and_workflow_refs_flagged_for_removal(self) -> None:
        self.write("src/app.ts", "\n".join([
            "export const a = 1;",
            "// Now uses the cache as requested",
            "export const b = 2;",
            "// 改为使用 Redis 缓存",
            "export const c = 3;",
            "// See .ai/design/login/backend.md section 2",
            "export const d = 4;",
            "",
        ]))
        report = self.run_audit()
        categories = [(f["text"], f["category"], f["signals"][0]) for f in report["findings"]]
        self.assertIn(("Now uses the cache as requested", "remove-candidate", "change-narration"), categories)
        self.assertIn(("改为使用 Redis 缓存", "remove-candidate", "change-narration"), categories)
        self.assertIn(
            ("See .ai/design/login/backend.md section 2", "remove-candidate", "workflow-ref"), categories,
        )

    def test_banner_comments_flagged(self) -> None:
        self.write("src/lib.rs", "\n".join([
            "fn main() {}",
            "// ==== handlers ====",
            "fn helper() {}",
            "// ----------------",
            "fn other() {}",
            "",
        ]))
        report = self.run_audit()
        self.assertEqual(len(self.findings(report, category="remove-candidate", signals=["section-banner"])), 2)

    def test_keep_categories_survive(self) -> None:
        self.write("src/lib.rs", "\n".join([
            "// Copyright (c) 2026 Example Corp. SPDX-License-Identifier: MIT",
            "//! Crate-level docs.",
            "/// Sums two values.",
            "fn sum(a: u32, b: u32) -> u32 {",
            "    // TODO(tim): remove once v2 migration lands",
            "    a + b",
            "}",
            "// Regression guard for US-142 checkout total",
            "// eslint-disable-next-line no-console",
            "",
        ]))
        self.write("tools/run.py", "\n".join([
            "# TODO: revisit after launch",
            "# noqa: E501",
            "print('hi')",
            "",
        ]))
        report = self.run_audit()
        keeps = {f["signals"][0] for f in self.findings(report, category="likely-keep")}
        self.assertIn("license-header", keeps)
        self.assertIn("todo", keeps)
        self.assertIn("traceability", keeps)
        self.assertIn("lint-directive", keeps)
        self.assertEqual(self.findings(report, category="remove-candidate"), [])
        docs = self.findings(report, category="doc-comment")
        self.assertEqual(len(docs), 2)

    def test_density_flags_plain_comments_for_review(self) -> None:
        self.write("src/state.ts", "\n".join([
            "export function load() {",
            "  // fetch the data",
            "  const res = await fetch('/api');",
            "  // parse the response",
            "  const json = await res.json();",
            "  // return the result",
            "  return json;",
            "}",
            "",
        ]))
        report = self.run_audit()
        entry = next(d for d in report["density"] if d["file"] == "src/state.ts")
        self.assertTrue(entry["flagged"])
        self.assertEqual(entry["added_comments"], 3)
        self.assertEqual(entry["added_code"], 5)
        self.assertEqual(len(self.findings(report, category="review-candidate")), 3)

    def test_low_comment_density_not_flagged(self) -> None:
        self.write("src/util.ts", "\n".join([
            "// Rate limit comes from the billing plan, not config.",
            "export const LIMIT = 10;",
            "export const other = 2;",
            "export const more = 3;",
            "export const extra = 4;",
            "",
        ]))
        report = self.run_audit()
        entry = next(d for d in report["density"] if d["file"] == "src/util.ts")
        self.assertFalse(entry["flagged"])
        self.assertEqual(self.findings(report, category="review-candidate"), [])
        self.assertEqual(self.findings(report, category="remove-candidate"), [])
        self.assertEqual(self.findings(report, category="doc-comment"), [])
        self.assertEqual(self.findings(report, category="likely-keep"), [])

    def test_existing_violations_reported_in_changed_files(self) -> None:
        self.write("src/legacy.py", "\n".join([
            "# Blocklist per .ai/task/T-42.md",
            "VALUE = 1",
            "",
        ]))
        self.command("git", "add", ".")
        self.command("git", "commit", "-m", "legacy")
        self.write("src/legacy.py", "\n".join([
            "# Blocklist per .ai/task/T-42.md",
            "VALUE = 2",
            "",
        ]))
        report = self.run_audit()
        matches = self.findings(report, scope="existing", category="remove-candidate")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["signals"], ["workflow-ref"])
        self.assertEqual(matches[0]["line"], 1)

    def test_staged_changes_count_as_added(self) -> None:
        self.write("src/staged.ts", "\n".join([
            "export const s = 1;",
            "// Moved from utils.ts during refactor",
            "export const t = 2;",
            "",
        ]))
        self.command("git", "add", ".")
        report = self.run_audit()
        matches = self.findings(report, category="remove-candidate")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["scope"], "added")
        self.assertEqual(matches[0]["line"], 2)

    def test_untracked_file_scanned_as_fully_added(self) -> None:
        self.write("src/new_module.ts", "\n".join([
            "// Moved from utils.ts during refactor",
            "export const x = 1;",
            "",
        ]))
        report = self.run_audit()
        matches = self.findings(report, category="remove-candidate")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["scope"], "added")
        self.assertEqual(matches[0]["file"], "src/new_module.ts")

    def test_non_source_files_ignored(self) -> None:
        self.write("docs/notes.md", "// Now uses the cache\n# 改为使用缓存\n")
        report = self.run_audit()
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["density"], [])

    def test_deleted_file_skipped(self) -> None:
        target = self.write("src/gone.ts", "export const g = 1;\n")
        self.command("git", "add", ".")
        self.command("git", "commit", "-m", "add gone")
        target.unlink()
        report = self.run_audit()
        self.assertEqual(report["findings"], [])

    def test_density_threshold_override(self) -> None:
        lines = ["// fetch data", "// parse response", "// return result"]
        lines += [f"export const v{idx} = {idx};" for idx in range(20)]
        lines.append("")
        self.write("src/edge.ts", "\n".join(lines))
        default_report = self.run_audit()
        self.assertEqual(self.findings(default_report, category="review-candidate"), [])
        strict_report = self.run_audit("--density-threshold", "0.05")
        self.assertEqual(len(self.findings(strict_report, category="review-candidate")), 3)

    def test_git_failure_exits_nonzero(self) -> None:
        broken = tempfile.TemporaryDirectory(prefix="t-tools-comment-audit-broken-")
        self.addCleanup(broken.cleanup)
        patch.object(audit, "REPO_ROOT", Path(broken.name)).start()
        output = io.StringIO()
        with redirect_stdout(output):
            code = audit.main([])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
