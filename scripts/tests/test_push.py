from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("push_under_test", REPO_ROOT / "scripts" / "push.py")
assert SPEC and SPEC.loader
push = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = push
SPEC.loader.exec_module(push)


class PushRecoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="t-tools-push-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "work"
        self.remote = Path(temporary.name) / "remote.git"
        self.root.mkdir()
        self.command("git", "init", "--bare", str(self.remote))
        self.command("git", "init", "-b", "main")
        self.command("git", "config", "user.name", "Push Test")
        self.command("git", "config", "user.email", "push-test@example.invalid")
        self.command("git", "config", "core.hooksPath", str(Path(temporary.name) / "no-hooks"))
        self.source = self.root / "sample.txt"
        self.source.write_text("base\n", encoding="utf-8")
        self.command("git", "add", ".")
        self.command("git", "commit", "-m", "base")
        self.command("git", "remote", "add", "origin", str(self.remote))
        self.command("git", "push", "-u", "origin", "main")
        self.base_head = self.command("git", "rev-parse", "HEAD").stdout.strip()
        self.addCleanup(patch.stopall)
        patch.object(push, "REPO_ROOT", self.root).start()

    def command(self, *args: str) -> subprocess.CompletedProcess:
        result = subprocess.run(args, cwd=self.root, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def run_script(self, *extra: str, session: str = "recovery") -> tuple[int, str]:
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            code = push.main(["--ci-session", session, "--message", "phase implementation", *extra])
        return code, output.getvalue()

    def remote_head(self) -> str:
        return self.command("git", "--git-dir", str(self.remote), "rev-parse", "refs/heads/main").stdout.strip()

    def fail_push(self, *args: str, capture: bool = False):
        if args[0] == "push":
            return subprocess.CompletedProcess(args, 1, "", "simulated transport failure")
        return self.original_git(*args, capture=capture)

    def create_failed_push(self) -> str:
        self.source.write_text("implementation\n", encoding="utf-8")
        self.original_git = push.git
        with patch.object(push, "git", side_effect=self.fail_push):
            code, _ = self.run_script()
        self.assertEqual(code, 1)
        head = push.current_head()
        self.assertNotEqual(head, self.base_head)
        self.assertEqual(self.remote_head(), self.base_head)
        self.assertEqual(self.command("git", "status", "--short").stdout, "")
        return head

    def test_failed_push_retries_existing_commit_without_creating_another(self) -> None:
        head = self.create_failed_push()
        code, output = self.run_script()
        self.assertEqual(code, 0, output)
        self.assertEqual(push.current_head(), head)
        self.assertEqual(self.remote_head(), head)
        self.assertEqual(push.load_push_record("recovery")["status"], "completed")

    def test_clean_tree_with_new_session_pushes_unpublished_commit(self) -> None:
        head = self.create_failed_push()
        code, output = self.run_script(session="fresh-retry")
        self.assertEqual(code, 0, output)
        self.assertEqual(self.remote_head(), head)

    def test_repeated_transport_failure_keeps_pending_record(self) -> None:
        self.create_failed_push()
        with patch.object(push, "git", side_effect=self.fail_push):
            code, _ = self.run_script()
        self.assertEqual(code, 1)
        self.assertEqual(push.load_push_record("recovery")["status"], "pending")
        self.assertEqual(self.remote_head(), self.base_head)

    def test_check_only_runs_ci_without_commit_or_push(self) -> None:
        self.source.write_text("implementation\n", encoding="utf-8")
        with patch.object(push, "run_ci") as ci:
            code, output = self.run_script("--check-only")
        self.assertEqual(code, 0, output)
        ci.assert_called_once()
        self.assertIn("Validated worktree fingerprint: sha256:", output)
        self.assertEqual(push.current_head(), self.base_head)
        self.assertEqual(self.remote_head(), self.base_head)
        self.assertIsNone(push.load_push_record("recovery"))

    def test_modified_accepted_input_stops_before_commit(self) -> None:
        accepted = push.worktree_fingerprint()
        self.source.write_text("unaccepted\n", encoding="utf-8")
        code, _ = self.run_script("--expected-fingerprint", accepted)
        self.assertEqual(code, 1)
        self.assertEqual(push.current_head(), self.base_head)
        self.assertEqual(self.remote_head(), self.base_head)

    def test_ci_modification_requires_new_acceptance(self) -> None:
        self.source.write_text("implementation\n", encoding="utf-8")
        accepted = push.worktree_fingerprint()
        with patch.object(push, "run_ci", side_effect=lambda *args, **kwargs: self.source.write_text("ci fix\n", encoding="utf-8")):
            code, output = self.run_script("--expected-fingerprint", accepted)
        self.assertEqual(code, 1)
        self.assertIn("Local CI modified", output)
        self.assertEqual(push.current_head(), self.base_head)
        self.assertEqual(self.remote_head(), self.base_head)

    def test_runtime_cursor_write_does_not_invalidate_accepted_code(self) -> None:
        accepted = push.worktree_fingerprint()
        runtime = self.root / ".ai" / "super-run" / "demo" / ".state.json"
        runtime.parent.mkdir(parents=True)
        runtime.write_text('{"status":"in_progress"}\n', encoding="utf-8")
        self.assertEqual(push.worktree_fingerprint(), accepted)
        code, output = self.run_script("--expected-fingerprint", accepted)
        self.assertEqual(code, 0, output)
        self.assertEqual(self.remote_head(), push.current_head())
        self.assertEqual(push.worktree_fingerprint(), accepted)

    def test_interruption_after_commit_recovers_from_committing_record(self) -> None:
        self.source.write_text("implementation\n", encoding="utf-8")
        save = push.save_push_record
        def interrupt(session: str, record: dict) -> None:
            if record["status"] == "pending":
                raise RuntimeError("simulated interruption after git commit")
            save(session, record)
        with patch.object(push, "save_push_record", side_effect=interrupt):
            code, _ = self.run_script()
        self.assertEqual(code, 1)
        head = push.current_head()
        self.assertNotEqual(head, self.base_head)
        self.assertEqual(push.load_push_record("recovery")["status"], "committing")
        code, output = self.run_script()
        self.assertEqual(code, 0, output)
        self.assertEqual(push.current_head(), head)
        self.assertEqual(self.remote_head(), head)

    def test_code_change_after_failed_push_requires_revalidation(self) -> None:
        self.create_failed_push()
        self.source.write_text("later edit\n", encoding="utf-8")
        code, output = self.run_script()
        self.assertEqual(code, 1)
        self.assertIn("Code changed", output)
        self.assertEqual(self.remote_head(), self.base_head)

    def test_retry_enforces_callers_expected_fingerprint(self) -> None:
        self.create_failed_push()
        code, output = self.run_script("--expected-fingerprint", "sha256:" + "0" * 64)
        self.assertEqual(code, 1)
        self.assertIn("accepted fingerprint", output)
        self.assertEqual(self.remote_head(), self.base_head)

    def test_changed_push_target_preserves_pending_commit(self) -> None:
        self.create_failed_push()
        self.command("git", "config", "branch.main.merge", "refs/heads/other")
        code, output = self.run_script()
        self.assertEqual(code, 1)
        self.assertIn("Push target changed", output)
        self.assertEqual(push.load_push_record("recovery")["status"], "pending")

    def test_remote_descendant_confirms_original_commit(self) -> None:
        head = self.create_failed_push()
        self.command("git", "push", "origin", "main")
        other = self.root.parent / "other"
        self.command("git", "clone", "--branch", "main", str(self.remote), str(other))
        for key, value in (("user.name", "Other"), ("user.email", "other@example.invalid")):
            self.command("git", "-C", str(other), "config", key, value)
        (other / "later.txt").write_text("later\n", encoding="utf-8")
        self.command("git", "-C", str(other), "add", ".")
        self.command("git", "-C", str(other), "commit", "-m", "later remote commit")
        self.command("git", "-C", str(other), "push")
        remote_head = self.remote_head()
        code, output = self.run_script()
        self.assertEqual(code, 0, output)
        self.assertEqual(push.current_head(), head)
        self.assertEqual(self.remote_head(), remote_head)

    def test_unconfirmed_remote_keeps_record_pending(self) -> None:
        self.source.write_text("implementation\n", encoding="utf-8")
        with patch.object(push, "remote_contains", return_value=False):
            code, output = self.run_script()
        self.assertEqual(code, 1)
        self.assertIn("Remote has not confirmed", output)
        self.assertEqual(push.load_push_record("recovery")["status"], "pending")
        code, output = self.run_script()
        self.assertEqual(code, 0, output)
        self.assertEqual(self.remote_head(), push.current_head())

    def test_invalid_recovery_record_is_preserved(self) -> None:
        path = push.push_record_path("recovery")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{broken", encoding="utf-8")
        code, _ = self.run_script()
        self.assertEqual(code, 1)
        self.assertEqual(path.read_text(encoding="utf-8"), "{broken")

    def test_commit_hook_code_change_is_not_pushed(self) -> None:
        self.source.write_text("implementation\n", encoding="utf-8")
        original_git = push.git
        def hook(*args: str, capture: bool = False):
            if args[0] == "commit":
                self.source.write_text("hook change\n", encoding="utf-8")
                original_git("add", "sample.txt")
            return original_git(*args, capture=capture)
        with patch.object(push, "git", side_effect=hook):
            code, output = self.run_script("--expected-fingerprint", push.worktree_fingerprint())
        self.assertEqual(code, 1)
        self.assertIn("Commit hooks changed", output)
        self.assertEqual(self.remote_head(), self.base_head)


if __name__ == "__main__":
    unittest.main()
