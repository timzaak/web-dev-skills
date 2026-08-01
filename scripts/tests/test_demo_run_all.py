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

SPEC = importlib.util.spec_from_file_location("demo_run_all", SCRIPTS_DIR / "demo-run-all.py")
assert SPEC and SPEC.loader
demo_run_all = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = demo_run_all
SPEC.loader.exec_module(demo_run_all)


def payload(*, status: str = "running", entries: list[dict[str, object]] | None = None) -> dict[str, object]:
    files = ["demo/e2e/a.e2e.ts", "demo/e2e/b.e2e.ts"]
    completed = entries or []
    return {
        "batch_status": status,
        "discovered_files": files,
        "entries": completed,
        "current_index": len(completed),
        "current_file": "",
    }


class ResumeStateTests(unittest.TestCase):
    def test_completed_batch_cannot_continue(self) -> None:
        state = payload(status="completed", entries=[{"test_file": "demo/e2e/a.e2e.ts", "status": "failed"}])
        with self.assertRaisesRegex(ValueError, "not running"):
            demo_run_all.determine_resume_index(state)

    def test_resume_uses_next_unfinished_file_not_last_failure(self) -> None:
        state = payload(entries=[{"test_file": "demo/e2e/a.e2e.ts", "status": "failed"}])
        self.assertEqual(demo_run_all.determine_resume_index(state), 1)

    def test_entries_must_be_discovered_prefix(self) -> None:
        state = payload(entries=[{"test_file": "demo/e2e/b.e2e.ts", "status": "passed"}])
        with self.assertRaisesRegex(ValueError, "completed prefix"):
            demo_run_all.determine_resume_index(state)


class FinalizeTests(unittest.TestCase):
    def test_incomplete_batch_is_not_finalized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "batch.json"
            report.write_text(json.dumps(payload()), encoding="utf-8")
            with patch.object(demo_run_all, "REPO_ROOT", Path(temp_dir)):
                result = demo_run_all.cmd_finalize(Namespace(json=report))
            self.assertEqual(result, 1)
            saved = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(saved["batch_status"], "running")

    def test_invalid_entry_order_is_not_finalized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "batch.json"
            state = payload(entries=[
                {"test_file": "demo/e2e/b.e2e.ts", "status": "passed"},
                {"test_file": "demo/e2e/a.e2e.ts", "status": "passed"},
            ])
            report.write_text(json.dumps(state), encoding="utf-8")
            with patch.object(demo_run_all, "REPO_ROOT", Path(temp_dir)):
                result = demo_run_all.cmd_finalize(Namespace(json=report))
            self.assertEqual(result, 1)

    def test_complete_valid_batch_is_finalized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report = root / "batch.json"
            state = payload(entries=[
                {"test_file": "demo/e2e/a.e2e.ts", "status": "passed", "exit_code": 0},
                {"test_file": "demo/e2e/b.e2e.ts", "status": "failed", "exit_code": 1},
            ])
            state["markdown_report"] = "batch.md"
            state["total_duration"] = 3.5
            report.write_text(json.dumps(state), encoding="utf-8")
            with patch.object(demo_run_all, "REPO_ROOT", root):
                result = demo_run_all.cmd_finalize(Namespace(json=report))
            self.assertEqual(result, 1)
            saved = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(saved["batch_status"], "completed")
            self.assertEqual(saved["total_files"], 2)
            self.assertTrue((root / "batch.md").exists())


if __name__ == "__main__":
    unittest.main()
