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
    def test_discovers_web_and_flutter_demo_runner_items_independently(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = root / ".ai" / "task" / "feature"
            web = base / "web-demo" / "dev" / "WD-D02-runner.md"
            flutter = base / "flutter-demo" / "dev" / "FD-D02-runner.md"
            web.parent.mkdir(parents=True)
            flutter.parent.mkdir(parents=True)
            web.write_text(
                "## Expected Test Manifest\n- `login flow`\n"
                "## Validation\nuv run scripts/web-demo-test-runner.py demo/e2e/login.e2e.ts --grep 'login flow'\n",
                encoding="utf-8",
            )
            flutter.write_text(
                "## Expected Test Manifest\n- `password login`\n"
                "## Validation\nuv run scripts/flutter-demo-test-runner.py patrol_test/auth/login_test.dart --device emulator-5554\n",
                encoding="utf-8",
            )
            self.assertEqual(coverage.find_runner_files(root, "feature", "web-demo"), [web])
            self.assertEqual(coverage.find_runner_files(root, "feature", "flutter-demo"), [flutter])
            self.assertEqual(coverage.infer_layer(web), "web-demo")
            self.assertEqual(coverage.infer_layer(flutter), "flutter-demo")
            self.assertTrue(coverage.check_runner(root, web, dynamic=False).commands)
            self.assertTrue(coverage.check_runner(root, flutter, dynamic=False).commands)


if __name__ == "__main__":
    unittest.main()
