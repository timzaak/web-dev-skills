import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "check-markdown-links.py"
SPEC = importlib.util.spec_from_file_location("template_link_checker", SCRIPT)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class TemplateLinkBoundariesTests(unittest.TestCase):
    def test_catalog_link_does_not_create_phantom_active_agent_reference(self):
        with tempfile.TemporaryDirectory() as temporary:
            catalog = Path(temporary) / "index.md"
            catalog.write_text("[agents/backend-dev.md](files/agents/backend-dev.md)\n"
                               "Read /agents/project-dev.md and ${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md\n",
                               encoding="utf-8")
            urls = [link.url for link in checker.extract_links_from_file(catalog)]
            self.assertEqual(urls, ["files/agents/backend-dev.md", "/agents/project-dev.md",
                                    "${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md"])

    def test_template_payload_is_checked_in_exported_runtime_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            catalog = root / "templates/project-profiles/example/index.md"
            source = catalog.parent / "files/agents/backend-dev.md"
            source.parent.mkdir(parents=True)
            catalog.write_text("catalog", encoding="utf-8")
            source.write_text("template source", encoding="utf-8")
            with patch.object(checker, "PROJECT_ROOT", root):
                self.assertEqual(checker.find_all_md_files(root), [catalog])

    def test_root_argument_validates_exported_references_and_reports_broken_links(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "README.md").write_text("[broken](${CLAUDE_PLUGIN_ROOT}/agents/missing.md)", encoding="utf-8")
            result = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPT), "--root", str(root)],
                                    capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = (root / ".ai/check-markdown-links-report.md").read_text(encoding="utf-8")
            self.assertIn("| 死链接数量 | 1 |", report)
            self.assertIn(str(root / "agents/missing.md"), report)
            invalid = subprocess.run([sys.executable, "-X", "utf8", str(SCRIPT), "--root", str(root / "absent")],
                                     capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(invalid.returncode, 2)


if __name__ == "__main__":
    unittest.main()
