from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

SPEC = importlib.util.spec_from_file_location("demo_test_runner", SCRIPTS_DIR / "demo-test-runner.py")
assert SPEC and SPEC.loader
demo_test_runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = demo_test_runner
SPEC.loader.exec_module(demo_test_runner)


class RunLogRetentionTests(unittest.TestCase):
    def test_preparing_run_preserves_other_run_logs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            demo_dir = Path(temp_dir)
            previous_log = demo_dir / "test-results" / "runs" / "previous" / "playwright-output.log"
            previous_log.parent.mkdir(parents=True)
            previous_log.write_text("evidence", encoding="utf-8")

            current_dir = demo_test_runner.prepare_run_log_dir(demo_dir, "current")

            self.assertEqual(current_dir, demo_dir / "test-results" / "runs" / "current")
            self.assertEqual(previous_log.read_text(encoding="utf-8"), "evidence")

    def test_preparing_same_run_replaces_only_that_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            demo_dir = Path(temp_dir)
            stale_log = demo_dir / "test-results" / "runs" / "current" / "old.log"
            stale_log.parent.mkdir(parents=True)
            stale_log.write_text("stale", encoding="utf-8")

            current_dir = demo_test_runner.prepare_run_log_dir(demo_dir, "current")

            self.assertTrue(current_dir.is_dir())
            self.assertFalse(stale_log.exists())


if __name__ == "__main__":
    unittest.main()
