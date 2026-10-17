from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
SPEC = importlib.util.spec_from_file_location(
    "flutter_demo_run_all", SCRIPTS_DIR / "flutter-demo-run-all.py"
)
assert SPEC and SPEC.loader
batch = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = batch
SPEC.loader.exec_module(batch)


class DiscoveryTests(unittest.TestCase):
    def test_discovers_nested_patrol_tests_and_excludes_results(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            patrol = root / "patrol_test"
            (patrol / "auth").mkdir(parents=True)
            wanted = patrol / "auth" / "login_test.dart"
            wanted.write_text("", encoding="utf-8")
            ignored = patrol / "test-results" / "generated_test.dart"
            ignored.parent.mkdir()
            ignored.write_text("", encoding="utf-8")
            with patch.object(batch, "PATROL_DIR", patrol):
                self.assertEqual(batch.discover_test_files(), [wanted])


class BatchStateTests(unittest.TestCase):
    def test_checkpoint_record_and_finalize(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = root / "batch.json"
            batch.write_json(report, {
                "batch_status": "running",
                "discovered_files": ["patrol_test/login_test.dart"],
                "entries": [],
                "current_index": 0,
                "current_file": "",
            })
            with patch.object(batch, "REPO_ROOT", root):
                self.assertEqual(batch.cmd_checkpoint(Namespace(json=report, index=0)), 0)
                self.assertEqual(batch.cmd_record(Namespace(
                    json=report, status="passed", exit_code=0, duration=1.0,
                    run_id="r1", logs="patrol_test/test-results/runs/r1",
                    error="", fixed=False,
                )), 0)
                self.assertEqual(batch.cmd_finalize(Namespace(json=report)), 0)
            saved = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(saved["batch_status"], "completed")
            self.assertEqual(saved["passed_files"], 1)
            self.assertTrue(report.with_suffix(".md").exists())


if __name__ == "__main__":
    unittest.main()
