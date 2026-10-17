from __future__ import annotations

import importlib.util
import subprocess
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
    def test_combined_demo_item_through_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            item = root / ".ai/task/feature/web-demo/dev/WD-D01-login.md"
            item.parent.mkdir(parents=True)
            content = (
                "id: WD-D01\nagent: web-demo-dev\n"
                "## Goal\nWrite and run the login story.\n"
                "## Work\nMaintain fixture and story.\n"
                "## Files\n`demo/e2e/login.e2e.ts`\n"
                "## Validation\n### Expected Test Manifest\n"
                "| File | Case | Source | Command |\n|---|---|---|---|\n"
                "| demo/e2e/login.e2e.ts | `login flow` | WD-D01 | "
                "`uv run scripts/web-demo-test-runner.py demo/e2e/login.e2e.ts` |\n"
                "## Handoff\n`unrelated handoff token`\n"
            )
            command = [
                sys.executable, str(SCRIPTS_DIR / "check-test-runner-coverage.py"),
                "feature", "--project-root", str(root), "--layer", "web-demo",
            ]
            for text, expected_code, expected_output in (
                (content, 0, "expected tests: 1"),
                (content.replace("`login flow`", ""), 1, "No expected tests found"),
                (content.replace("web-demo-test-runner.py demo/e2e/login.e2e.ts", "web-demo-test-runner.py demo/e2e/"),
                 1, "Full-suite command lacks escalation reason"),
                (content.replace("`uv run scripts/web-demo-test-runner.py demo/e2e/login.e2e.ts`", "pending command"),
                 1, "No runner files found"),
            ):
                with self.subTest(expected_output=expected_output):
                    item.write_text(text, encoding="utf-8")
                    result = subprocess.run(command, capture_output=True, text=True, check=False)
                    self.assertEqual(result.returncode, expected_code, result.stdout + result.stderr)
                    self.assertIn(expected_output, result.stdout)


if __name__ == "__main__":
    unittest.main()
