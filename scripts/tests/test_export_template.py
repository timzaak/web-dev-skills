from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("export_template", Path(__file__).resolve().parents[1] / "export-template.py")
exporter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exporter)


class ExportTemplateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "source"
        self.root.mkdir()
        self.output = Path(self.temp.name) / "exported"
        self.run_git("init")
        self.run_git("config", "user.email", "template@example.invalid")
        self.run_git("config", "user.name", "Template Test")
        self.run_git("config", "core.hooksPath", str(Path(self.temp.name) / "no-hooks"))
        (self.root / "protocols").mkdir()
        (self.root / "protocols/state.md").write_text("matched historical contract\n", encoding="utf-8")
        (self.root / "agent.md").write_text("original agent\n", encoding="utf-8")
        self.run_git("add", ".")
        self.run_git("commit", "-m", "baseline")
        self.revision = self.run_git("rev-parse", "HEAD").stdout.strip()
        self.profile = self.root / exporter.CATALOG / "sample"
        (self.profile / "files").mkdir(parents=True)
        (self.profile / "files/agent.md").write_text("template customization\n", encoding="utf-8")
        self.manifest = dict(schema_version=1, id="sample", description="sample", upstream_revision=self.revision,
                             source_paths=["agent.md"])
        self.save_manifest()

    def run_git(self, *args):
        result = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def save_manifest(self):
        (self.profile / "template.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def test_export_uses_pinned_contract_and_current_payload(self):
        self.run_git("config", "core.autocrlf", "true")
        (self.root / "protocols/state.md").write_text("incompatible current contract\n", encoding="utf-8")
        result = exporter.export_template(self.root, "sample", self.output)
        self.assertEqual(result["status"], "exported")
        self.assertEqual((self.output / "protocols/state.md").read_text(encoding="utf-8"), "matched historical contract\n")
        self.assertEqual((self.output / "protocols/state.md").read_bytes(), b"matched historical contract\n")
        self.assertEqual((self.output / "agent.md").read_text(encoding="utf-8"), "template customization\n")
        self.assertFalse((self.output / ".git").exists())

    def test_dry_run_does_not_create_output(self):
        self.assertEqual(exporter.export_template(self.root, "sample", self.output, dry_run=True)["status"], "planned")
        self.assertFalse(self.output.exists())

    def test_repeat_export_preserves_changes_and_unrelated_files(self):
        exporter.export_template(self.root, "sample", self.output)
        (self.output / "notes.txt").write_text("user notes", encoding="utf-8")
        self.assertEqual(exporter.export_template(self.root, "sample", self.output)["status"], "unchanged")
        (self.output / "agent.md").write_text("user edit", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "preserved"):
            exporter.export_template(self.root, "sample", self.output)
        self.assertEqual((self.output / "agent.md").read_text(encoding="utf-8"), "user edit")
        self.assertEqual((self.output / "notes.txt").read_text(encoding="utf-8"), "user notes")

    def test_existing_project_and_source_repository_are_rejected(self):
        self.output.mkdir()
        (self.output / "AGENTS.md").write_text("existing project", encoding="utf-8")
        with self.assertRaises(ValueError):
            exporter.export_template(self.root, "sample", self.output)
        for target in (self.root, self.root / "generated", self.root.parent):
            with self.subTest(target=target), self.assertRaises(ValueError):
                exporter.export_template(self.root, "sample", target)

    def test_missing_baseline_and_payload_are_rejected(self):
        self.manifest["upstream_revision"] = "0" * 40
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "baseline unavailable"):
            exporter.export_template(self.root, "sample", self.output)
        self.manifest["upstream_revision"] = self.revision
        self.save_manifest()
        (self.profile / "files/agent.md").unlink()
        with self.assertRaisesRegex(ValueError, "Missing"):
            exporter.export_template(self.root, "sample", self.output)
        self.assertFalse(self.output.exists())

    def test_invalid_paths_and_unknown_template_are_rejected(self):
        for name in ("../outside", "/absolute", "C:/outside", ".git/config", "a/../outside", "a\\outside"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                exporter.safe_name(name)
        self.manifest["source_paths"] = ["agent.md", "agent.md"]
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            exporter.load_manifest(self.root, "sample")
        with self.assertRaisesRegex(ValueError, "Unknown"):
            exporter.load_manifest(self.root, "unknown")

    def test_failed_staging_does_not_leave_partial_output(self):
        with patch.object(Path, "write_bytes", side_effect=OSError("simulated disk failure")):
            with self.assertRaises(OSError):
                exporter.export_template(self.root, "sample", self.output)
        self.assertFalse(self.output.exists())
        self.assertEqual(exporter.export_template(self.root, "sample", self.output)["status"], "exported")


if __name__ == "__main__":
    unittest.main()
