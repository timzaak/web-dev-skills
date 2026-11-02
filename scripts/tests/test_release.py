from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location("release_under_test", REPO_ROOT / "scripts/release.py")
assert SPEC and SPEC.loader
release = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = release
SPEC.loader.exec_module(release)


class PiReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="t-tools-release-pi-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.addCleanup(patch.stopall)
        patch.object(release, "REPO_ROOT", self.root).start()

    def write_json(self, name: str, data: dict) -> None:
        (self.root / name).write_text(json.dumps(data), encoding="utf-8")

    def configure(self, scripts: dict | None = None) -> None:
        self.write_json("package.json", {
            "name": "pi-example", "version": "0.1.0", "pi": {"skills": ["./skills"]},
            "scripts": scripts or {},
        })

    @unittest.skipUnless(shutil.which("npm") or shutil.which("npm.cmd"), "npm is required for version integration")
    def test_root_version_and_existing_npm_locks_stay_in_sync_on_repeat(self) -> None:
        # Lifecycle hooks must never run during this workflow-owned version bump.
        self.configure({"preversion": "node -e \"process.exit(31)\"", "postversion": "node -e \"process.exit(32)\""})
        for name in ("package-lock.json", "npm-shrinkwrap.json"):
            self.write_json(name, {"name": "pi-example", "version": "0.1.0", "lockfileVersion": 3, "packages": {"": {"name": "pi-example", "version": "0.1.0"}}})
        for _ in range(2):
            changes = release.update_version_files("0.2.0")
            self.assertEqual({c.path.name for c in changes}, {"package.json", "package-lock.json", "npm-shrinkwrap.json"})
            for name in ("package.json", "package-lock.json", "npm-shrinkwrap.json"):
                data = json.loads((self.root / name).read_text(encoding="utf-8"))
                self.assertEqual(data["version"], "0.2.0")
                if "packages" in data:
                    self.assertEqual(data["packages"][""]["version"], "0.2.0")
        self.assertFalse((self.root / "node_modules").exists())

    def test_project_resources_do_not_force_an_npm_package_release(self) -> None:
        (self.root / ".pi/skills").mkdir(parents=True)
        with self.assertRaisesRegex(RuntimeError, "No supported version files"):
            release.update_version_files("0.2.0")

    def test_root_version_failure_stops_before_commit(self) -> None:
        self.configure()
        with patch.object(release, "require_executable", return_value="npm"), patch.object(release, "run_cmd", return_value=subprocess.CompletedProcess([], 1)), patch.object(release, "git") as git:
            with self.assertRaisesRegex(RuntimeError, "Unable to update pi package version"):
                release.update_version_files("0.2.0")
            git.assert_not_called()

    def test_release_validation_uses_the_same_pi_checks_and_propagates_failure(self) -> None:
        self.configure({"typecheck": "tsc --noEmit"})
        with patch.object(release, "run_cmd", return_value=subprocess.CompletedProcess([], 1)) as run:
            with self.assertRaisesRegex(RuntimeError, "Validation failed"):
                release.run_validation()
            self.assertEqual(run.call_args.args[0][1:], ["run", "typecheck"])

    def test_root_metadata_is_staged_and_tag_is_owned_by_release(self) -> None:
        self.configure()
        self.write_json("package-lock.json", {"version": "0.2.0"})
        def git_result(*args, **kwargs):
            return subprocess.CompletedProcess(args, 1 if args[:3] == ("diff", "--cached", "--quiet") else 0, "abc123\n", "")
        with patch.object(release, "git", side_effect=git_result) as git:
            self.assertEqual(release.commit_tag_and_push("0.2.0", push=False), "abc123")
        calls = [call.args for call in git.call_args_list]
        self.assertIn(("add", "package.json", "package-lock.json"), calls)
        self.assertIn(("tag", "v0.2.0"), calls)
        self.assertFalse(any(call[0] == "push" for call in calls))

    def make_git_project(self) -> tuple[Path, str]:
        remote = self.root / "remote.git"
        project = self.root / "project"
        project.mkdir()
        self.command(self.root, "git", "init", "--bare", str(remote))
        self.root = project
        patch.object(release, "REPO_ROOT", project).start()
        self.command(project, "git", "init", "-b", "main")
        self.command(project, "git", "config", "user.name", "Release Test")
        self.command(project, "git", "config", "user.email", "release@example.invalid")
        self.command(project, "git", "config", "core.hooksPath", str(project / "no-hooks"))
        self.configure()
        self.write_json("package-lock.json", {"name": "pi-example", "version": "0.1.0", "lockfileVersion": 3, "packages": {"": {"version": "0.1.0"}}})
        self.command(project, "git", "add", ".")
        self.command(project, "git", "commit", "-m", "base")
        self.command(project, "git", "remote", "add", "origin", str(remote))
        self.command(project, "git", "push", "-u", "origin", "main")
        return remote, self.command(project, "git", "rev-parse", "HEAD")

    def command(self, cwd: Path, *args: str) -> str:
        result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    @unittest.skipUnless(shutil.which("npm") or shutil.which("npm.cmd"), "npm is required for release integration")
    def test_complete_local_release_commits_synchronized_metadata_and_one_v_tag(self) -> None:
        remote, base = self.make_git_project()
        with patch.object(sys, "argv", ["release.py", "0.2.0", "--no-push"]):
            self.assertEqual(release.main(), 0)
        self.assertEqual(self.command(self.root, "git", "tag", "--list"), "v0.2.0")
        self.assertEqual(self.command(self.root, "git", "status", "--porcelain"), "")
        for name in ("package.json", "package-lock.json"):
            data = json.loads(self.command(self.root, "git", "show", f"v0.2.0:{name}"))
            self.assertEqual(data["version"], "0.2.0")
        self.assertEqual(self.command(self.root, "git", "--git-dir", str(remote), "rev-parse", "refs/heads/main"), base)
        head = self.command(self.root, "git", "rev-parse", "HEAD")
        with patch.object(sys, "argv", ["release.py", "0.2.0", "--no-push"]):
            self.assertEqual(release.main(), 1)
        self.assertEqual(self.command(self.root, "git", "rev-parse", "HEAD"), head)
        self.assertEqual(self.command(self.root, "git", "tag", "--list"), "v0.2.0")

    @unittest.skipUnless(shutil.which("npm") or shutil.which("npm.cmd"), "npm is required for release integration")
    def test_failed_release_validation_preserves_changes_without_commit_or_tag(self) -> None:
        _, base = self.make_git_project()
        self.configure({"typecheck": "node -e \"process.exit(9)\""})
        self.command(self.root, "git", "add", "package.json")
        self.command(self.root, "git", "commit", "-m", "configure failing check")
        base = self.command(self.root, "git", "rev-parse", "HEAD")
        with patch.object(sys, "argv", ["release.py", "0.2.0", "--no-push"]):
            self.assertEqual(release.main(), 1)
        self.assertEqual(self.command(self.root, "git", "rev-parse", "HEAD"), base)
        self.assertEqual(self.command(self.root, "git", "tag", "--list"), "")
        self.assertEqual(json.loads((self.root / "package.json").read_text())["version"], "0.2.0")


if __name__ == "__main__":
    unittest.main()
