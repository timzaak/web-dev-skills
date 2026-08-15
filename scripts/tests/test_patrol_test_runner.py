from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
SPEC = importlib.util.spec_from_file_location(
    "patrol_test_runner", SCRIPTS_DIR / "patrol-test-runner.py"
)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def make_project(root: Path) -> list[Path]:
    (root / "pubspec.yaml").write_text(
        "name: sample\npatrol:\n  test_directory: patrol_test\n",
        encoding="utf-8",
    )
    auth = root / "patrol_test" / "auth" / "login_test.dart"
    profile = root / "patrol_test" / "profile_test.dart"
    helper = root / "patrol_test" / "auth" / "test_support.dart"
    generated = root / "patrol_test" / "test-results" / "generated_test.dart"
    for path in (auth, profile, helper, generated):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    return [auth, profile]


class DiscoveryTests(unittest.TestCase):
    def test_discovers_only_test_files_outside_results(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            expected = make_project(root)
            self.assertEqual(runner.discover_tests(root), expected)

    def test_expands_comma_separated_targets_without_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            expected = make_project(root)
            targets = runner.expand_targets(
                root,
                ["patrol_test/auth/login_test.dart,patrol_test/profile_test.dart", "patrol_test/auth/login_test.dart"],
            )
            self.assertEqual(targets, expected)


class DeviceTests(unittest.TestCase):
    def test_requires_device_when_platform_has_multiple_candidates(self) -> None:
        devices = [
            runner.Device("a", "A", "android-x64", True),
            runner.Device("b", "B", "android-arm64", False),
        ]
        with self.assertRaisesRegex(ValueError, "Multiple android devices"):
            runner.select_device(devices, "android", "")

    def test_physical_ios_forces_release_mode(self) -> None:
        device = runner.Device("iphone", "iPhone", "ios", False)
        self.assertEqual(runner.resolve_mode("debug", device), "release")


class CommandTests(unittest.TestCase):
    def test_bundled_command_uses_repeated_targets_in_one_invocation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            targets = make_project(root)
            device = runner.Device("emulator-5554", "Pixel", "android-x64", True)
            command = runner.build_command("patrol", device, "debug", targets, root, ["--tags=smoke"])
            self.assertEqual(command.count("--target"), 2)
            self.assertEqual(command[:4], ["patrol", "test", "--device", "emulator-5554"])
            self.assertIn("--tags=smoke", command)

    def test_parse_result_uses_process_exit_code_and_summary(self) -> None:
        output = """Test summary:
Total: 2
Successful: 2
Failed: 0
Skipped: 0
Duration: 12s
"""
        result = runner.parse_result("bundle", 0, output)
        self.assertTrue(result.passed)
        self.assertEqual((result.total, result.successful, result.duration), (2, 2, "12s"))


class MainTests(unittest.TestCase):
    def test_default_runs_all_targets_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_project(root)
            device = runner.Device("emulator-5554", "Pixel", "android-x64", True)
            success = runner.TestResult("bundle", 0, total=2, successful=2)
            with (
                patch.object(runner, "REPO_ROOT", root),
                patch.object(runner.shutil, "which", return_value="patrol"),
                patch.object(runner, "flutter_devices", return_value=[device]),
                patch.object(runner, "run_patrol", return_value=success) as run,
            ):
                self.assertEqual(runner.main([]), 0)
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0].count("--target"), 2)


if __name__ == "__main__":
    unittest.main()

