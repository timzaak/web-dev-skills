from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("check_design", Path(__file__).resolve().parents[1] / "check-design.py")
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class DesignValidationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "src").mkdir()
        self.main = self.root / ".ai/design/sample.md"
        self.content = "\n".join(checker.MAIN_HEADINGS)
        self.content = self.content.replace("### 2.5 设计覆盖矩阵", """### 2.5 设计覆盖矩阵
| Requirement | Design | Contract | Validation | Impact |
| --- | --- | --- | --- | --- |
| REQ-1 | §4 | none | actual project command | src/job.py |
""")
        self.content = self.content.replace("### 4.2 交付端范围", """### 4.2 交付端范围
| 模块 ID | 文档 | 状态 |
| --- | --- | --- |
| processor | processor.md | 适用 |
""")
        self.content = self.content.replace("### 4.3 跨端契约", "### 4.3 跨端契约\n不适用：独立处理器，不消费公共契约。")
        self.content += """
| 文件 | 操作 | 说明 | 来源 |
| --- | --- | --- | --- |
| src/job.py | CREATE | existing src | processor |
"""
        write(self.main, self.content)
        self.module = self.main.with_suffix("") / "processor.md"
        write(self.module, """# Processor
## 8. 文件影响范围
| 文件 | 操作 | 说明 |
| --- | --- | --- |
| src/job.py | CREATE | existing src |
""")
        self.state = self.module.parent / ".state.json"
        self.valid_state = dict(status="complete", applicable_stacks=["processor"], completed_stacks=["processor"], failed_stack=None)
        write(self.state, json.dumps(self.valid_state))

    def codes(self, complete=False):
        return {f.code for f in checker.validate(self.main, self.root, complete)}

    def test_custom_module_and_complete_state(self):
        self.assertEqual(self.codes(True), set())
        self.assertEqual(checker.design_documents(self.main), [self.main, self.module])

    def test_module_named_main_still_aggregates_separate_document(self):
        write(self.main, self.content.replace("processor", "main"))
        write(self.module.parent / "main.md", self.module.read_text(encoding="utf-8").replace("src/job.py", "src/other.py"))
        self.assertIn("IMPACT_NOT_AGGREGATED", self.codes())

    def test_small_project_can_keep_design_in_main(self):
        write(self.main, self.content.replace("processor.md", "main"))
        self.assertEqual(self.codes(True), set())
        self.assertEqual(checker.design_documents(self.main), [self.main])

    def test_missing_module_and_unaggregated_impacts(self):
        self.module.unlink()
        self.assertIn("MODULE_DOC_MISSING", self.codes())
        write(self.module, """## 8. 文件影响范围
| 文件 | 操作 |
| --- | --- |
| src/other.py | CREATE |
""")
        self.assertIn("IMPACT_NOT_AGGREGATED", self.codes())

    def test_invalid_scope_is_rejected(self):
        for row in ("| ../escape | ../escape.md | 适用 |", "| processor | processor.md | 待定 |",
                    "| processor | processor.md | 适用 |\n| processor | main | 适用 |"):
            with self.subTest(row=row):
                write(self.main, self.content.replace("| processor | processor.md | 适用 |", row))
                self.assertIn("DELIVERY_SCOPE_INVALID", self.codes())

    def test_state_mismatch_and_malformed_json_are_rejected(self):
        for state in ([], {}, dict(self.valid_state, completed_stacks=[]), dict(self.valid_state, applicable_stacks=[False]),
                      dict(self.valid_state, failed_stack="processor"), dict(self.valid_state, status="in_progress")):
            with self.subTest(state=state):
                write(self.state, json.dumps(state))
                self.assertTrue(self.codes(True))
        write(self.state, "{broken")
        self.assertIn("DESIGN_STATE_INVALID", self.codes(True))

    def test_paths_and_skill_directory_exception(self):
        self.assertTrue(checker.validate_path(self.root, self.main, "../outside.py", "CREATE"))
        self.assertTrue(checker.validate_path(self.root, self.main, "absent/job.py", "CREATE"))
        self.assertTrue(checker.validate_path(self.root, self.main, "src/missing.py", "DELETE"))
        self.assertEqual(checker.validate_path(self.root, self.main, ".claude/skills/new/SKILL.md", "CREATE"), [])

    def test_cli_json_and_missing_source_failure(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = checker.main([str(self.main), "--repo-root", str(self.root), "--require-complete", "--json"])
        result = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(len(result["design_documents"]), 2)
        self.main.unlink()
        self.assertIn("DESIGN_DOC_MISSING", self.codes(True))


if __name__ == "__main__":
    unittest.main()
