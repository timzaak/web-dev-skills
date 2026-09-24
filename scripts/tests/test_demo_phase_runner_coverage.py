from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
SPEC = importlib.util.spec_from_file_location(
    "runner_coverage", SCRIPTS_DIR / "check-test-runner-coverage.py"
)
assert SPEC and SPEC.loader
coverage = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = coverage
SPEC.loader.exec_module(coverage)


class DemoPhaseCoverageTests(unittest.TestCase):
    def test_extension_runner_discovery_and_full_suite_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runner = root / ".ai/task/feature/extension/test/EX-T02-runner.md"
            runner.parent.mkdir(parents=True)
            content = (
                "## Expected Test Manifest\n- `rejects invalid sender`\n"
                "## Validation\ncd extension && npm run test:run -- lib/messaging.test.ts\n"
            )
            runner.write_text(content, encoding="utf-8")
            self.assertEqual(coverage.find_runner_files(root, "feature", "extension"), [runner])
            self.assertEqual(coverage.find_runner_files(root, "feature", None), [runner])
            self.assertEqual(coverage.infer_layer(runner), "extension")
            self.assertEqual(coverage.check_runner(root, runner, dynamic=False).errors, [])
            runner.write_text(content.replace(" -- lib/messaging.test.ts", ""), encoding="utf-8")
            errors = coverage.check_runner(root, runner, dynamic=False).errors
            self.assertTrue(any("Full-suite command lacks" in error for error in errors))
            runner.write_text(content.replace("cd extension && npm run test:run -- lib/messaging.test.ts", ""), encoding="utf-8")
            self.assertIn("No test runner command found.", coverage.check_runner(root, runner, dynamic=False).errors)

    def test_discovers_web_extension_and_flutter_demo_runner_items_independently(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = root / ".ai" / "task" / "feature"
            web = base / "web-demo" / "dev" / "WD-D02-runner.md"
            extension = base / "extension-demo" / "dev" / "ED-D02-runner.md"
            flutter = base / "flutter-demo" / "dev" / "FD-D02-runner.md"
            web.parent.mkdir(parents=True)
            extension.parent.mkdir(parents=True)
            flutter.parent.mkdir(parents=True)
            web.write_text(
                "## Expected Test Manifest\n- `login flow`\n"
                "## Validation\nuv run scripts/web-demo-test-runner.py demo/e2e/login.e2e.ts --grep 'login flow'\n",
                encoding="utf-8",
            )
            extension.write_text(
                "## Expected Test Manifest\n- `settings flow`\n"
                "## Validation\nuv run scripts/web-demo-test-runner.py demo/e2e/extension/settings.e2e.ts --no-auto-env --grep 'settings flow'\n",
                encoding="utf-8",
            )
            flutter.write_text(
                "## Expected Test Manifest\n- `password login`\n"
                "## Validation\nuv run scripts/flutter-demo-test-runner.py patrol_test/auth/login_test.dart --device emulator-5554\n",
                encoding="utf-8",
            )
            self.assertEqual(coverage.find_runner_files(root, "feature", "web-demo"), [web])
            self.assertEqual(coverage.find_runner_files(root, "feature", "extension-demo"), [extension])
            self.assertEqual(coverage.find_runner_files(root, "feature", "flutter-demo"), [flutter])
            self.assertEqual(coverage.infer_layer(web), "web-demo")
            self.assertEqual(coverage.infer_layer(extension), "extension-demo")
            self.assertEqual(coverage.infer_layer(flutter), "flutter-demo")
            self.assertTrue(coverage.check_runner(root, web, dynamic=False).commands)
            self.assertEqual(coverage.check_runner(root, extension, dynamic=False).errors, [])
            self.assertTrue(coverage.is_full_suite_command(
                "uv run scripts/web-demo-test-runner.py demo/e2e/extension/ --mode fast", "extension-demo"
            ))
            self.assertTrue(coverage.check_runner(root, flutter, dynamic=False).commands)


if __name__ == "__main__":
    unittest.main()
