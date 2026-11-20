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
SPEC = importlib.util.spec_from_file_location("resolve_under_test", REPO_ROOT / "scripts" / "resolve-ttools-source.py")
assert SPEC and SPEC.loader
resolve_source = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = resolve_source
SPEC.loader.exec_module(resolve_source)


def create_worktree(parent: Path, name: str = "tools-repo", *,
                    plugin_name: str = "t-tools", tracked_skill: bool = True) -> Path:
    root = parent / name
    root.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=root, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Resolve Test"], cwd=root, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "resolve-test@example.invalid"], cwd=root, capture_output=True, check=True)
    manifest = root / ".claude-plugin" / "plugin.json"
    manifest.parent.mkdir()
    manifest.write_text(json.dumps({"name": plugin_name}), encoding="utf-8")
    if tracked_skill:
        skill = root / "skills" / "t-skill" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("# Skill\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "base"], cwd=root, capture_output=True, check=True)
    return root


class ResolveSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="t-tools-resolve-test-")
        self.addCleanup(temporary.cleanup)
        self.parent = Path(temporary.name)
        self.worktree = create_worktree(self.parent)
        self.revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.worktree,
                                       capture_output=True, text=True, encoding="utf-8").stdout.strip()

    def run_script(self, *args: str, env_value: str | None = None) -> tuple[int, dict]:
        output = io.StringIO()
        environment = {"CLAUDE_PLUGIN_ROOT": env_value} if env_value is not None else {}
        with redirect_stdout(output), patch.dict("os.environ", environment, clear=False):
            code = resolve_source.main(list(args))
        return code, json.loads(output.getvalue())

    def test_resolves_explicit_argument(self) -> None:
        code, result = self.run_script(str(self.worktree))
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["root"], str(self.worktree.resolve()))
        self.assertEqual(result["revision"], self.revision)
        self.assertEqual(result["source"], f"argument:{self.worktree}")
        self.assertFalse(result["dirty"])

    def test_reports_dirty_worktree(self) -> None:
        (self.worktree / "skills" / "t-skill" / "SKILL.md").write_text("# Skill changed\n", encoding="utf-8")
        code, result = self.run_script(str(self.worktree))
        self.assertEqual(code, 0)
        self.assertTrue(result["dirty"])

    def test_falls_through_invalid_candidate_to_valid(self) -> None:
        code, result = self.run_script(str(self.parent / "missing"), str(self.worktree))
        self.assertEqual(code, 0)
        self.assertEqual(result["source"], f"argument:{self.worktree}")

    def test_rejects_non_git_directory(self) -> None:
        plain = self.parent / "plain"
        plain.mkdir()
        (plain / ".claude-plugin").mkdir()
        (plain / ".claude-plugin" / "plugin.json").write_text('{"name": "t-tools"}', encoding="utf-8")
        code, result = self.run_script(str(plain))
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "error")
        self.assertIn("not inside a Git worktree", result["candidates"][0]["reason"])

    def test_rejects_wrong_plugin_name(self) -> None:
        other = create_worktree(self.parent, "other-repo", plugin_name="other-plugin")
        code, result = self.run_script(str(other))
        self.assertEqual(code, 1)
        self.assertIn("not 't-tools'", result["candidates"][0]["reason"])

    def test_rejects_untracked_skill(self) -> None:
        other = create_worktree(self.parent, "untracked-repo", tracked_skill=False)
        skill = other / "skills" / "t-skill" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("# untracked\n", encoding="utf-8")
        code, result = self.run_script(str(other))
        self.assertEqual(code, 1)
        self.assertIn("not tracked by Git", result["candidates"][0]["reason"])

    def test_uses_plugin_root_environment_without_arguments(self) -> None:
        code, result = self.run_script(env_value=str(self.worktree))
        self.assertEqual(code, 0)
        self.assertEqual(result["source"], "env:CLAUDE_PLUGIN_ROOT")

    def test_all_candidates_invalid_reports_every_attempt(self) -> None:
        plain = self.parent / "plain2"
        plain.mkdir()
        code, result = self.run_script(str(plain), str(self.parent / "missing"))
        self.assertEqual(code, 1)
        self.assertEqual(len(result["candidates"]), 2)


if __name__ == "__main__":
    unittest.main()
