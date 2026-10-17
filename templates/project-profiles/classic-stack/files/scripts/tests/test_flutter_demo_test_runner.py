from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

SPEC = importlib.util.spec_from_file_location(
    "flutter_demo_test_runner", SCRIPTS_DIR / "flutter-demo-test-runner.py"
)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def make_project(root: Path) -> Path:
    (root / "pubspec.yaml").write_text(
        "name: sample\ndev_dependencies:\n  patrol: 4.7.0\npatrol:\n  app_name: sample\n",
        encoding="utf-8",
    )
    (root / "pubspec.lock").write_text("packages:\n  patrol:\n", encoding="utf-8")
    test_file = root / "patrol_test" / "auth" / "login_test.dart"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("void main() {}\n", encoding="utf-8")
    return test_file


class ProjectValidationTests(unittest.TestCase):
    def test_accepts_story_file_inside_patrol_test(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = make_project(root)
            self.assertEqual(
                runner.validate_project(root, "patrol_test/auth/login_test.dart"),
                target.resolve(),
            )

    def test_rejects_target_outside_patrol_test(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_project(root)
            outside = root / "test" / "login_test.dart"
            outside.parent.mkdir()
            outside.write_text("void main() {}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "inside patrol_test"):
                runner.validate_project(root, str(outside))


class DeviceSelectionTests(unittest.TestCase):
    def test_selects_the_only_android_device(self) -> None:
        devices = [{"id": "emulator-5554", "targetPlatform": "android-x64", "isSupported": True}]
        with patch.object(runner, "android_devices", return_value=devices):
            self.assertEqual(runner.select_android_device(Path.cwd(), ""), "emulator-5554")

    def test_multiple_android_devices_require_explicit_id(self) -> None:
        devices = [
            {"id": "a", "targetPlatform": "android-x64"},
            {"id": "b", "targetPlatform": "android-arm64"},
        ]
        with patch.object(runner, "android_devices", return_value=devices):
            with self.assertRaisesRegex(ValueError, "Multiple Android devices"):
                runner.select_android_device(Path.cwd(), "")

    def test_requested_non_android_device_is_rejected(self) -> None:
        with patch.object(runner, "android_devices", return_value=[]):
            with self.assertRaisesRegex(ValueError, "not a supported Android"):
                runner.select_android_device(Path.cwd(), "chrome")


class EnvironmentAndSecretTests(unittest.TestCase):
    def test_environment_scripts_must_be_a_pair(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "flutter-demo-start.py").write_text("", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "as a pair"):
                runner.lifecycle_scripts(root)

    def test_sensitive_dart_define_is_masked(self) -> None:
        self.assertEqual(runner.masked_define("API_TOKEN=value"), "API_TOKEN=***")
        self.assertEqual(runner.masked_define("REALM_ID=demo"), "REALM_ID=demo")


class RunnerResultTests(unittest.TestCase):
    @staticmethod
    def _completed(code: int = 0) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(["command"], code, "", "")

    def test_success_writes_patrol_log_and_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_project(root)
            output = io.StringIO()
            with (
                patch.object(runner, "REPO_ROOT", root),
                patch.object(runner.shutil, "which", return_value="patrol"),
                patch.object(runner, "_run", return_value=self._completed()),
                patch.object(runner, "select_android_device", return_value="emulator-5554"),
                patch.object(runner.subprocess, "run", return_value=self._completed()),
                redirect_stdout(output),
            ):
                code = runner.main([
                    "patrol_test/auth/login_test.dart", "--run-id", "run-1",
                    "--dart-define", "API_TOKEN=sensitive",
                ])
            self.assertEqual(code, 0)
            self.assertIn("API_TOKEN=***", output.getvalue())
            self.assertNotIn("API_TOKEN=sensitive", output.getvalue())
            self.assertIn('"platform":"android"', output.getvalue())
            self.assertTrue(
                (root / "patrol_test/test-results/runs/run-1/patrol-output.log").exists()
            )

    def test_timeout_returns_124_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_project(root)
            output = io.StringIO()
            with (
                patch.object(runner, "REPO_ROOT", root),
                patch.object(runner.shutil, "which", return_value="patrol"),
                patch.object(runner, "_run", return_value=self._completed()),
                patch.object(runner, "select_android_device", return_value="emulator-5554"),
                patch.object(
                    runner.subprocess,
                    "run",
                    side_effect=subprocess.TimeoutExpired(["patrol"], 1),
                ),
                redirect_stdout(output),
            ):
                code = runner.main([
                    "patrol_test/auth/login_test.dart", "--run-id", "run-timeout", "--timeout", "1"
                ])
            self.assertEqual(code, 124)
            self.assertIn('"exitCode":124', output.getvalue())


if __name__ == "__main__":
    unittest.main()
