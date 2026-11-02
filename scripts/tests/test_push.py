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

    def test_runtime_cursor_write_does_not_block_pending_recovery(self) -> None:
        self.create_failed_push()
        runtime = self.root / ".ai" / "super-run" / "demo" / ".state.json"
        runtime.parent.mkdir(parents=True)
        runtime.write_text('{"status":"in_progress"}\n', encoding="utf-8")
        code, output = self.run_script()
        self.assertEqual(code, 0, output)
        self.assertEqual(self.remote_head(), push.current_head())

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
            code, output = self.run_script()
        self.assertEqual(code, 1)
        self.assertIn("Commit hooks changed", output)
        self.assertEqual(self.remote_head(), self.base_head)


class ShopifyAreaTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="t-tools-push-shopify-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.addCleanup(patch.stopall)
        patch.object(push, "REPO_ROOT", self.root).start()

    def test_root_files_map_to_shopify_only_when_app_toml_exists(self) -> None:
        (self.root / "shopify.app.toml").write_text('name = "x"\n', encoding="utf-8")
        areas = push.detect_areas(
            ["shopify.app.toml", "app/routes/app._index.tsx", "extensions/theme/blocks.liquid", "prisma/schema.prisma"]
        )
        self.assertEqual(areas, {"shopify"})

    def test_demo_files_stay_in_demo_area_for_shopify_projects(self) -> None:
        (self.root / "shopify.app.toml").write_text('name = "x"\n', encoding="utf-8")
        self.assertEqual(push.detect_areas(["demo/e2e/smoke.e2e.ts"]), {"demo"})
        self.assertEqual(
            push.detect_areas(["demo/e2e/a.e2e.ts", "app/routes/x.tsx"]),
            {"demo", "shopify"},
        )

    def test_root_files_map_to_no_area_without_app_toml(self) -> None:
        areas = push.detect_areas(["README.md", "app/routes/x.tsx"])
        self.assertEqual(areas, set())

    def test_shopify_area_fingerprint_excludes_demo(self) -> None:
        self.assertEqual(
            push.area_pathspecs("shopify"),
            [".", ":(exclude)backend/", ":(exclude)frontend/", ":(exclude)demo/", ":(exclude).ai/"],
        )
        self.assertEqual(push.area_pathspecs("frontend"), ["frontend/"])

    def test_shopify_steps_require_app_toml(self) -> None:
        with self.assertRaises(RuntimeError):
            push.shopify_steps()
        (self.root / "shopify.app.toml").write_text('name = "x"\n', encoding="utf-8")
        (self.root / "package.json").write_text(
            '{"scripts": {"build": "react-router build"}}', encoding="utf-8"
        )
        with self.assertRaisesRegex(RuntimeError, "typecheck"):
            push.shopify_steps()

    def configure_app(self, scripts: dict[str, str], *, extension: bool = False) -> None:
        (self.root / "shopify.app.toml").write_text('name = "x"\n', encoding="utf-8")
        (self.root / "package.json").write_text(json.dumps({"scripts": scripts}), encoding="utf-8")
        if extension:
            path = self.root / "extensions/theme/shopify.extension.toml"
            path.parent.mkdir(parents=True)
            path.write_text('type = "theme"\n', encoding="utf-8")

    def test_template_typecheck_is_used_and_legacy_name_supported(self) -> None:
        for script in ("typecheck", "type-check"):
            with self.subTest(script=script):
                self.configure_app({script: "react-router typegen && tsc --noEmit", "build": "react-router build"})
                steps = push.shopify_steps()
                self.assertEqual([s.command[1:] for s in steps], [["run", script], ["run", "build"]])

    def test_extensions_run_cli_build_after_application_checks(self) -> None:
        self.configure_app({"typecheck": "tsc --noEmit", "build": "react-router build", "shopify": "shopify"}, extension=True)
        steps = push.shopify_steps()
        self.assertEqual(steps[-1].command[1:], ["run", "shopify", "--", "app", "build"])
        self.assertEqual(steps[-1].cwd, self.root)
        with patch.object(push, "run_cmd", return_value=subprocess.CompletedProcess([], 1)):
            with self.assertRaisesRegex(RuntimeError, "Shopify extensions build failed"):
                push.run_steps("shopify", [steps[-1]])

    def test_extension_cli_and_application_build_cannot_be_missing(self) -> None:
        self.configure_app({"typecheck": "tsc --noEmit"})
        with self.assertRaisesRegex(RuntimeError, "build"):
            push.shopify_steps()
        self.configure_app({"typecheck": "tsc --noEmit", "build": "react-router build"}, extension=True)
        with self.assertRaisesRegex(RuntimeError, "shopify"):
            push.shopify_steps()


if __name__ == "__main__":
    unittest.main()
