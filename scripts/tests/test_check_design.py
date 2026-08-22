from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check-design.py"
SPEC = importlib.util.spec_from_file_location("check_design", SCRIPT)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def main_doc(frontend_status: str = "适用") -> str:
    return f"""
# Sample 技术设计（主文档）
## 1. 需求概述
## 2. 需求来源
### 2.4 决策追踪
### 2.5 设计覆盖矩阵
| Requirement / Story ID | 设计落点 | 契约/组件 | 测试与验收 | 文件影响 |
|---|---|---|---|---|
| REQ-001 | backend §4 | createExport | cargo test | src/new.rs |
## 3. 现有实现分析
## 4. 总体方案
### 4.2 交付端范围
| 端 | 分端设计文档 | 状态 |
|---|---|---|
| backend | backend.md | 适用 |
| frontend | frontend.md | {frontend_status} |
| flutter | flutter.md | 不适用（无移动端） |
### 4.3 跨端契约（API 契约摘要）
| Operation ID | 方法 | 路径 | 用途 | 调用方 |
|---|---|---|---|---|
| createExport | POST | /api/exports | create | frontend |
## 6. 测试与验收策略
## 7. 风险与验证动作
## 8. 文件影响范围（全量汇总）
| 文件 | 操作 | 说明 | 来源分端 |
|---|---|---|---|
| src/new.rs | CREATE | adjacent to src/lib.rs | backend |
| web/new.ts | CREATE | adjacent to web/index.ts | frontend |
"""


BACKEND = """
# Backend
## 4. API 接口设计
### 4.1 接口清单
| Operation ID | 方法 | 路径 | 用途 | 权限/身份 | 调用方 |
|---|---|---|---|---|---|
| createExport | POST | /api/exports | create | user | frontend |
## 9. 详细设计
## 12. 文件影响范围（后端文件）
| 文件 | 操作 | 说明 |
|---|---|---|
| src/new.rs | CREATE | adjacent to src/lib.rs |
"""


FRONTEND = """
# Frontend
## 4. 用户体验流
### 5.3 页面结构 / 线框说明
### 6.1 API 依赖（只引用契约源）
| Operation ID | 方法 | 路径 | 使用的请求字段 | 使用的响应字段 | 用途 |
|---|---|---|---|---|---|
| createExport | POST | /api/exports | format | id | create |
## 9. 详细设计（前端最小实现映射）
## 11. 文件影响范围（前端文件）
| 文件 | 操作 | 说明 |
|---|---|---|
| web/new.ts | CREATE | adjacent to web/index.ts |
"""


class DesignValidationTests(unittest.TestCase):
    def make_design(self, root: Path, frontend: str = FRONTEND) -> Path:
        (root / "src").mkdir()
        (root / "web").mkdir()
        (root / "src/lib.rs").write_text("", encoding="utf-8")
        (root / "web/index.ts").write_text("", encoding="utf-8")
        main = root / ".ai/design/sample.md"
        write(main, main_doc())
        write(root / ".ai/design/sample/backend.md", BACKEND)
        write(root / ".ai/design/sample/frontend.md", frontend)
        return main

    def test_valid_design_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            findings = checker.validate(self.make_design(root), root)
            self.assertEqual(findings, [])

    def test_missing_applicable_document_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = self.make_design(root)
            (root / ".ai/design/sample/frontend.md").unlink()
            codes = {item.code for item in checker.validate(main, root)}
            self.assertIn("STACK_DOC_MISSING", codes)

    def test_contract_signature_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            frontend = FRONTEND.replace("/api/exports", "/api/wrong")
            codes = {item.code for item in checker.validate(self.make_design(root, frontend), root)}
            self.assertIn("CONTRACT_SIGNATURE_MISMATCH", codes)

    def test_create_parent_must_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = self.make_design(root)
            content = main.read_text(encoding="utf-8").replace("src/new.rs", "missing/new.rs")
            main.write_text(content, encoding="utf-8")
            backend = root / ".ai/design/sample/backend.md"
            backend.write_text(backend.read_text(encoding="utf-8").replace("src/new.rs", "missing/new.rs"), encoding="utf-8")
            codes = {item.code for item in checker.validate(main, root)}
            self.assertIn("CREATE_PARENT_MISSING", codes)

    def test_child_impact_must_be_aggregated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = self.make_design(root)
            backend = root / ".ai/design/sample/backend.md"
            backend.write_text(backend.read_text(encoding="utf-8").replace("src/new.rs", "src/other.rs"), encoding="utf-8")
            codes = {item.code for item in checker.validate(main, root)}
            self.assertIn("IMPACT_NOT_AGGREGATED", codes)

    def test_incomplete_state_is_optional_during_generation_and_required_downstream(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = self.make_design(root)
            write(root / ".ai/design/sample/.state.json", '{"status":"in_progress"}')
            self.assertNotIn(
                "DESIGN_GENERATION_INCOMPLETE",
                {item.code for item in checker.validate(main, root)},
            )
            self.assertIn(
                "DESIGN_GENERATION_INCOMPLETE",
                {item.code for item in checker.validate(main, root, require_complete=True)},
            )

    def test_fingerprint_covers_applicable_design_documents(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = self.make_design(root)
            before = checker.design_fingerprint(main)
            frontend = root / ".ai/design/sample/frontend.md"
            frontend.write_text(frontend.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
            self.assertNotEqual(before, checker.design_fingerprint(main))

    def test_json_output_exposes_fingerprint_and_documents(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = self.make_design(root)
            output = io.StringIO()
            with redirect_stdout(output):
                code = checker.main([str(main), "--repo-root", str(root), "--json"])
            result = json.loads(output.getvalue())
            self.assertEqual(code, 0)
            self.assertTrue(result["design_fingerprint"].startswith("sha256:"))
            self.assertEqual(
                result["design_documents"],
                [
                    ".ai/design/sample.md",
                    ".ai/design/sample/backend.md",
                    ".ai/design/sample/frontend.md",
                ],
            )


if __name__ == "__main__":
    unittest.main()
