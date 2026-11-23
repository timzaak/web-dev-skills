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

    def findings(self, report: dict, **match: object) -> list[dict]:
        return [f for f in report["findings"] if all(f.get(k) == v for k, v in match.items())]

    def test_remove_candidates_and_keep_whitelist(self) -> None:
        self.write("src/app.ts", "\n".join([
            "// Now uses the cache as requested",
            "// 改为使用 Redis 缓存",
            "// See .ai/design/login/backend.md section 2",
            "// ==== handlers ====",
            "export const a = 1;",
            "",
        ]))
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
        report = self.run_audit()
        removals = {(f["file"], f["signals"][0]) for f in self.findings(report, category="remove-candidate")}
        self.assertEqual(removals, {
            ("src/app.ts", "change-narration"),
            ("src/app.ts", "workflow-ref"),
            ("src/app.ts", "section-banner"),
        })
        keeps = {f["signals"][0] for f in self.findings(report, category="likely-keep")}
        self.assertEqual(keeps, {"license-header", "todo", "traceability", "lint-directive"})
        self.assertEqual(len(self.findings(report, category="doc-comment")), 2)

    def test_density_flagging_and_threshold_override(self) -> None:
        self.write("src/dense.ts", "\n".join([
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
        self.write("src/sparse.ts", "\n".join(
            ["// fetch data", "// parse response", "// return result"]
            + [f"export const v{i} = {i};" for i in range(20)]
            + [""]
        ))
        report = self.run_audit()
        dense = next(d for d in report["density"] if d["file"] == "src/dense.ts")
        sparse = next(d for d in report["density"] if d["file"] == "src/sparse.ts")
        self.assertTrue(dense["flagged"])
        self.assertFalse(sparse["flagged"])
        self.assertEqual(len(self.findings(report, file="src/dense.ts", category="review-candidate")), 3)
        self.assertEqual(self.findings(report, file="src/sparse.ts", category="review-candidate"), [])

        strict = self.run_audit("--density-threshold", "0.05")
        self.assertEqual(len(self.findings(strict, file="src/sparse.ts", category="review-candidate")), 3)

    def test_existing_vs_added_scope_across_git_states(self) -> None:
        self.write("src/legacy.py", "# Blocklist per .ai/task/T-42.md\nVALUE = 1\n")
        self.command("git", "add", ".")
        self.command("git", "commit", "-m", "legacy")
        self.write("src/legacy.py", "# Blocklist per .ai/task/T-42.md\nVALUE = 2\n")
        self.write("src/staged.ts", "// Moved from utils.ts during refactor\nexport const s = 1;\n")
        self.command("git", "add", "src/staged.ts")
        self.write("docs/notes.md", "// Now uses the cache\n")

        report = self.run_audit()
        existing = self.findings(report, file="src/legacy.py", scope="existing", category="remove-candidate")
        staged = self.findings(report, file="src/staged.ts", scope="added", category="remove-candidate")
        self.assertEqual((len(existing), existing[0]["signals"]), (1, ["workflow-ref"]))
        self.assertEqual(len(staged), 1)
        self.assertEqual(self.findings(report, file="docs/notes.md"), [])


if __name__ == "__main__":
    unittest.main()
