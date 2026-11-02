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


class PiAreaTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="t-tools-push-pi-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.addCleanup(patch.stopall)
        patch.object(push, "REPO_ROOT", self.root).start()

    def configure_package(self, scripts: dict[str, str], *, manifest: bool = True, keyword: bool = False) -> None:
        data: dict[str, object] = {"scripts": scripts}
        if manifest:
            data["pi"] = {"extensions": ["./extensions/*.ts"]}
        if keyword:
            data["keywords"] = ["pi-package"]
        (self.root / "package.json").write_text(json.dumps(data), encoding="utf-8")

    def test_root_files_map_to_pi_when_manifest_or_keyword_exists(self) -> None:
        self.configure_package({"type-check": "tsc --noEmit"})
        self.assertEqual(
            push.detect_areas(["package.json", "extensions/hello.ts", "skills/review/SKILL.md"]),
            {"pi"},
        )
        self.configure_package({"type-check": "tsc --noEmit"}, manifest=False, keyword=True)
        self.assertEqual(push.detect_areas(["extensions/hello.ts"]), {"pi"})

    def test_root_files_map_to_no_area_without_pi_markers(self) -> None:
        self.configure_package({"type-check": "tsc --noEmit"}, manifest=False)
        self.assertEqual(push.detect_areas(["README.md", "src/hello.ts"]), set())

    def test_conventional_resources_and_last_resource_deletion_are_detected(self) -> None:
        self.configure_package({"type-check": "tsc --noEmit"}, manifest=False)
        resource = self.root / "extensions/hello.ts"
        resource.parent.mkdir()
        resource.write_text("export default () => {};", encoding="utf-8")
        self.assertEqual(push.detect_areas(["README.md"]), {"pi"})
        resource.unlink()
        self.assertEqual(push.detect_areas(["extensions/hello.ts"]), {"pi"})
        self.assertEqual(push.detect_areas(["README.md"]), set())

    def test_project_resources_without_a_package_are_detected_even_on_deletion(self) -> None:
        self.assertEqual(push.detect_areas([".pi/extensions/hello.ts"]), {"pi"})
        self.assertEqual(push.detect_areas([".pi/skills/review/SKILL.md"]), {"pi"})
        self.assertEqual(push.pi_steps([".pi/skills/review/SKILL.md"]), [])
        with self.assertRaisesRegex(RuntimeError, "pi code changes require"):
            push.pi_steps([".pi/extensions/hello.ts"])

    def test_project_resource_config_is_checked_and_workflow_state_is_excluded(self) -> None:
        (self.root / ".pi/extensions").mkdir(parents=True)
        self.assertEqual(push.detect_areas(["package.json", ".pi/settings.json"]), {"pi"})
        self.assertEqual(push.detect_areas([".ai/task/feature/.state.json"]), set())

    def test_demo_and_backend_files_keep_their_own_areas(self) -> None:
        self.configure_package({"type-check": "tsc --noEmit"})
        self.assertEqual(
            push.detect_areas(["demo/e2e/a.e2e.ts", "backend/src/main.rs", "extensions/hello.ts"]),
            {"demo", "backend", "pi"},
        )

    def test_shopify_root_takes_precedence_over_pi(self) -> None:
        (self.root / "shopify.app.toml").write_text('name = "x"\n', encoding="utf-8")
        self.configure_package({"type-check": "tsc --noEmit"})
        self.assertEqual(push.detect_areas(["app/routes/x.tsx"]), {"shopify"})
        self.assertEqual(push.detect_areas(["app/routes/x.tsx", ".pi/extensions/tool.ts"]), {"shopify", "pi"})

    def test_pi_area_fingerprint_excludes_other_areas(self) -> None:
        self.assertEqual(
            push.area_pathspecs("pi"),
            [".", ":(exclude)backend/", ":(exclude)frontend/", ":(exclude)demo/", ":(exclude).ai/"],
        )

    def test_pi_code_steps_require_checks_but_text_assets_do_not(self) -> None:
        self.assertEqual(push.pi_steps([".pi/skills/review/SKILL.md"]), [])
        self.configure_package({"build": "tsc"})
        with self.assertRaisesRegex(RuntimeError, "type-check"):
            push.pi_steps(["extensions/tool.ts"])
        self.configure_package({})
        self.assertEqual(push.pi_steps(["skills/review/SKILL.md", "prompts/review.md", "themes/dark.json"]), [])

    def test_pi_text_diff_skips_types_even_with_an_existing_script(self) -> None:
        self.configure_package({"type-check": "tsc --noEmit"})
        self.assertEqual(push.pi_steps(["skills/review/SKILL.md"]), [])
        self.assertEqual(len(push.pi_steps(["package.json"])), 1)
        self.configure_package({})
        self.assertEqual(push.pi_steps(["frontend/src/app.ts", "demo/setup.ts", "skills/review/SKILL.md"]), [])

    def test_pi_code_falls_back_to_existing_compiler_without_installing(self) -> None:
        self.configure_package({})
        compiler = self.root / "node_modules/typescript/bin/tsc"
        compiler.parent.mkdir(parents=True)
        compiler.write_text("", encoding="utf-8")
        (self.root / "tsconfig.json").write_text("{}", encoding="utf-8")
        steps = push.pi_steps(["extensions/tool.ts"])
        self.assertEqual(steps[0].command[1:], [str(compiler), "--noEmit"])
        (self.root / "tsconfig.json").unlink()
        with self.assertRaisesRegex(RuntimeError, "tsconfig.json"):
            push.pi_steps(["extensions/tool.ts"])

    def test_pi_ci_failure_does_not_cache_a_success_and_retry_reruns(self) -> None:
        self.configure_package({"type-check": "tsc --noEmit"})
        with patch.object(push, "load_ci_cache", return_value={}), patch.object(push, "area_fingerprint", return_value="hash"), patch.object(push, "save_ci_cache") as save:
            with patch.object(push, "run_cmd", return_value=subprocess.CompletedProcess([], 1)):
                with self.assertRaisesRegex(RuntimeError, "Local CI failed"):
                    push.run_ci({"pi"}, ci_session="retry", files=["extensions/tool.ts"])
            save.assert_not_called()
            with patch.object(push, "run_cmd", return_value=subprocess.CompletedProcess([], 0)) as run:
                push.run_ci({"pi"}, ci_session="retry", files=["extensions/tool.ts"])
                run.assert_called_once()
            self.assertEqual(save.call_args.args[1]["pi"]["status"], "passed")

    def test_pi_unchanged_success_uses_session_cache(self) -> None:
        with patch.object(push, "load_ci_cache", return_value={"pi": {"status": "passed", "fingerprint": "hash"}}), patch.object(push, "area_fingerprint", return_value="hash"), patch.object(push, "pi_steps") as build:
            push.run_ci({"pi"}, ci_session="cached", files=["extensions/tool.ts"])
            build.assert_not_called()

    def test_invalid_manifest_stops_detection_instead_of_skipping_ci(self) -> None:
        (self.root / "package.json").write_text("{broken", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            push.detect_areas(["extensions/tool.ts"])

    def test_pi_steps_accept_any_type_check_alias_and_optional_lint_build(self) -> None:
        for script in ("type-check:pi", "typecheck:pi", "type-check", "typecheck", "check"):
            with self.subTest(script=script):
                self.configure_package({script: "tsc --noEmit"})
                steps = push.pi_steps()
                self.assertEqual([s.command[1:] for s in steps], [["run", script]])
                self.assertTrue(all(step.cwd == self.root for step in steps))
        self.configure_package({"lint": "biome check .", "type-check": "tsc --noEmit", "build": "tsc"})
        steps = push.pi_steps()
        self.assertEqual([s.command[1:] for s in steps], [["run", "lint"], ["run", "type-check"], ["run", "build"]])

    def test_pi_specific_check_is_preferred_without_replacing_the_app_check(self) -> None:
        self.configure_package({"type-check": "tsc -p tsconfig.app.json", "type-check:pi": "tsc -p tsconfig.pi.json"})
        steps = push.pi_steps([".pi/extensions/tool.ts"])
        self.assertEqual(steps[0].command[1:], ["run", "type-check:pi"])


if __name__ == "__main__":
    unittest.main()
