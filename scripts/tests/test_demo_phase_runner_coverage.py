from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
SPEC = importlib.util.spec_from_file_location("runner_coverage", SCRIPTS_DIR / "check-test-runner-coverage.py")
assert SPEC and SPEC.loader
coverage = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = coverage
SPEC.loader.exec_module(coverage)


class DemoPhaseCoverageTests(unittest.TestCase):
    def test_cli_validates_manifest_and_full_suite_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            item = root / ".ai/task/feature/web-demo/dev/WD-D01-login.md"
            item.parent.mkdir(parents=True)
            content = (
                "## Validation\n### Expected Test Manifest\n"
                "| File | Case | Source | Command |\n|---|---|---|---|\n"
                "| demo/e2e/login.e2e.ts | `login flow` | WD-D01 | "
                "`uv run scripts/web-demo-test-runner.py demo/e2e/login.e2e.ts` |\n"
            )
            command = [
                sys.executable, str(SCRIPTS_DIR / "check-test-runner-coverage.py"),
                "feature", "--project-root", str(root), "--layer", "web-demo", "--no-dynamic",
            ]
            for text, expected_code, expected_output in (
                (content, 0, "expected tests: 1"),
                (content.replace("`login flow`", ""), 1, "No expected tests found"),
                (content.replace("demo/e2e/login.e2e.ts", "demo/e2e/"), 1, "Full-suite command lacks escalation reason"),
            ):
                with self.subTest(expected_output=expected_output):
                    item.write_text(text, encoding="utf-8")
                    result = subprocess.run(command, capture_output=True, text=True, check=False)
                    self.assertEqual(result.returncode, expected_code, result.stdout + result.stderr)
                    self.assertIn(expected_output, result.stdout)

    def test_multi_stack_layer_discovery_and_full_suite_detection(self) -> None:
        stacks = [
            ("extension", "extension/test/EX-T02-runner.md", "cd extension && npm run test:run -- lib/msg.test.ts", "cd extension && npm run test:run"),
            ("shopify-app", "shopify-app/test/SA-T02-runner.md", "npm run test -- src/proxy.test.ts", "npm run test"),
            ("shopify-extension", "shopify-extension/test/SX-T01-runner.md", "npm run test -- ext/settings.test.ts", "npm run test"),
            ("extension-demo", "extension-demo/dev/ED-D02-runner.md", "uv run scripts/web-demo-test-runner.py demo/e2e/extension/settings.e2e.ts --no-auto-env", "uv run scripts/web-demo-test-runner.py demo/e2e/extension/ --mode fast"),
            ("flutter-demo", "flutter-demo/dev/FD-D02-runner.md", "uv run scripts/flutter-demo-test-runner.py patrol_test/auth/login_test.dart --device emu", None),
        ]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for layer, rel, targeted, full_suite in stacks:
                with self.subTest(layer=layer):
                    runner = root / ".ai" / "task" / "feature" / rel
                    runner.parent.mkdir(parents=True, exist_ok=True)
                    runner.write_text(f"## Expected Test Manifest\n- `case`\n## Validation\n{targeted}\n", encoding="utf-8")
                    self.assertEqual(coverage.find_runner_files(root, "feature", layer), [runner])
                    self.assertEqual(coverage.infer_layer(runner), layer)
                    self.assertEqual(coverage.check_runner(root, runner, dynamic=False).errors, [])
                    if full_suite:
                        runner.write_text(f"## Expected Test Manifest\n- `case`\n## Validation\n{full_suite}\n", encoding="utf-8")
                        self.assertTrue(any("Full-suite command lacks" in e for e in coverage.check_runner(root, runner, dynamic=False).errors))


if __name__ == "__main__":
    unittest.main()
