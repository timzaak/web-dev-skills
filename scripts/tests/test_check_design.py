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
    def test_flutter_design_uses_compact_template_headings(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = self.make_design(root)
            write(main, main_doc().replace("frontend", "flutter"))
            flutter = main.with_suffix("") / "flutter.md"
            write(flutter, '''
## 4. 用户体验流
### 6.1 API 依赖（只引用契约源）
| Operation ID | 方法 | 路径 |
|---|---|---|
| createExport | POST | /api/exports |
## 10. 详细设计（Flutter 最小实现映射）
## 12. 文件影响范围（Flutter 文件）
| 文件 | 操作 | 说明 |
|---|---|---|
| web/new.ts | CREATE | test fixture path |
''')
            self.assertEqual(checker.validate(main, root), [])
            old = flutter.read_text(encoding="utf-8").replace("## 10. 详细设计", "## 12. 详细设计").replace("## 12. 文件影响范围", "## 14. 文件影响范围")
            write(flutter, old)
            self.assertEqual(checker.validate(main, root), [])

    def test_extension_design_is_validated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = self.make_design(root)
            write(main, main_doc().replace("frontend", "extension"))
            extension = main.with_suffix("") / "extension.md"
            content = '''
## 4. 入口与交互
## 5. 权限与上下文
## 6. 消息与存储
### 6.1 API 依赖
| Operation ID | 方法 | 路径 |
|---|---|---|
| createExport | POST | /api/exports |
## 7. 测试与验收
## 9. 文件影响范围（扩展文件）
| 文件 | 操作 | 说明 |
|---|---|---|
| web/new.ts | CREATE | extension entry |
'''
            write(extension, content)
            self.assertEqual(checker.validate(main, root), [])
            self.assertIn(extension, checker.design_documents(main))
            write(extension, content.replace("/api/exports", "/api/wrong"))
            self.assertIn("CONTRACT_SIGNATURE_MISMATCH", {f.code for f in checker.validate(main, root)})
            write(extension, content.replace("web/new.ts", "web/other.ts"))
            self.assertIn("IMPACT_NOT_AGGREGATED", {f.code for f in checker.validate(main, root)})
            extension.unlink()
            self.assertIn("STACK_DOC_MISSING", {f.code for f in checker.validate(main, root)})

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

    def test_downstream_requires_complete_design_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = self.make_design(root)
            self.assertIn(
                "DESIGN_GENERATION_INCOMPLETE",
                {item.code for item in checker.validate(main, root, require_complete=True)},
            )
            write(root / ".ai/design/sample/.state.json", '{"status":"complete"}')
            self.assertEqual(checker.validate(main, root, require_complete=True), [])

    def test_json_output_exposes_documents(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = self.make_design(root)
            output = io.StringIO()
            with redirect_stdout(output):
                code = checker.main([str(main), "--repo-root", str(root), "--json"])
            result = json.loads(output.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(
                result["design_documents"],
                [
                    ".ai/design/sample.md",
                    ".ai/design/sample/backend.md",
                    ".ai/design/sample/frontend.md",
                ],
            )


SHOPIFY_MAIN = """
# Sample Shopify 技术设计（主文档）
## 1. 需求概述
## 2. 需求来源
### 2.4 决策追踪
### 2.5 设计覆盖矩阵
| Requirement / Story ID | 设计落点 | 契约/组件 | 测试与验收 | 文件影响 |
|---|---|---|---|---|
| REQ-001 | shopify §5 | getCampaigns | npm run test | app/routes/proxy.ts |
## 3. 现有实现分析
## 4. 总体方案
### 4.2 交付端范围
| 端 | 分端设计文档 | 状态 |
|---|---|---|
| backend | backend.md | 不适用（无独立后端） |
| frontend | frontend.md | 不适用 |
| shopify | shopify.md | 适用 |
### 4.3 跨端契约（API 契约摘要）
| Operation ID | 方法 | 路径 | 用途 | 调用方 |
|---|---|---|---|---|
| getCampaigns | GET | /apps/campaign/campaigns | list | storefront |
## 6. 测试与验收策略
## 7. 风险与验证动作
## 8. 文件影响范围（全量汇总）
| 文件 | 操作 | 说明 | 来源分端 |
|---|---|---|---|
| app/routes/proxy.ts | CREATE | app proxy route | shopify |
"""

SHOPIFY_STACK = """
# Shopify 分端设计
## 1. 目标与范围
## 2. 需求来源与决策追踪
## 3. 现有实现分析
## 4. 数据模型
## 5. 契约设计（app proxy / internal API）
| Operation ID | 方法 | 路径 | 请求字段 | 响应字段 | 错误行为 | 调用方 |
|---|---|---|---|---|---|---|
| getCampaigns | GET | /apps/campaign/campaigns | - | items | 401 | storefront |
## 6. admin 嵌入页
## 7. 扩展交付（extensions/）
## 8. 测试与验收
## 9. 风险与验证动作
## 10. 文件影响范围（Shopify 文件）
| 文件 | 操作 | 归属 phase | 说明 |
|---|---|---|---|
| app/routes/proxy.ts | CREATE | shopify-app | app proxy route |
"""


class ShopifyDesignTests(unittest.TestCase):
    def make_shopify_design(self, root: Path, stack_content: str = SHOPIFY_STACK) -> Path:
        (root / "app" / "routes").mkdir(parents=True, exist_ok=True)
        main = root / ".ai/design/sample.md"
        write(main, SHOPIFY_MAIN)
        write(main.with_suffix("") / "shopify.md", stack_content)
        return main

    def test_shopify_only_design_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = self.make_shopify_design(root)
            self.assertEqual(checker.validate(main, root), [])
            self.assertIn(
                main.with_suffix("") / "shopify.md",
                checker.design_documents(main),
            )

    def test_shopify_contract_mismatch_against_main_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = self.make_shopify_design(root, SHOPIFY_STACK.replace("/apps/campaign/campaigns", "/apps/campaign/wrong"))
            self.assertIn("MAIN_CONTRACT_MISMATCH", {f.code for f in checker.validate(main, root)})

    def test_shopify_empty_contract_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            empty = SHOPIFY_STACK.replace(
                "| getCampaigns | GET | /apps/campaign/campaigns | - | items | 401 | storefront |\n",
                "",
            )
            main = self.make_shopify_design(root, empty)
            self.assertIn("SHOPIFY_CONTRACT_EMPTY", {f.code for f in checker.validate(main, root)})

    def test_shopify_missing_heading_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            broken = SHOPIFY_STACK.replace("## 8. 测试与验收", "## 8. 测试")
            main = self.make_shopify_design(root, broken)
            self.assertIn("STACK_HEADING_MISSING", {f.code for f in checker.validate(main, root)})

    def test_shopify_existing_contract_requires_main_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = self.make_shopify_design(root)
            write(main, SHOPIFY_MAIN.replace(
                "| getCampaigns | GET | /apps/campaign/campaigns | list | storefront |\n", ""
            ))
            self.assertIn("MAIN_CONTRACT_MISMATCH", {f.code for f in checker.validate(main, root)})

    def test_shopify_no_api_feature_requires_reason_in_both_documents(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            reason = "不适用：仅修改静态 block 展示，不新增、修改或消费接口。\n"
            stack = SHOPIFY_STACK.replace(
                "| getCampaigns | GET | /apps/campaign/campaigns | - | items | 401 | storefront |\n", reason
            )
            main_text = SHOPIFY_MAIN.replace(
                "| getCampaigns | GET | /apps/campaign/campaigns | list | storefront |\n", reason
            )
            main = self.make_shopify_design(root, stack)
            write(main, main_text)
            write(main.with_suffix("") / ".state.json", '{"status":"complete"}')
            for _ in range(2):
                self.assertEqual(checker.validate(main, root, require_complete=True), [])
            write(main, main_text.replace(reason, ""))
            self.assertIn("MAIN_CONTRACT_EMPTY", {f.code for f in checker.validate(main, root)})
            write(main, main_text)
            for missing_reason in ("不适用\n", "不适用：\n- 其他说明\n"):
                write(main.with_suffix("") / "shopify.md", stack.replace(reason, missing_reason))
                self.assertIn("SHOPIFY_CONTRACT_EMPTY", {f.code for f in checker.validate(main, root)})

    def test_shopify_contract_source_validates_client_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = self.make_shopify_design(root)
            (root / "web").mkdir()
            write(main, SHOPIFY_MAIN.replace("| frontend | frontend.md | 不适用 |", "| frontend | frontend.md | 适用 |")
                  + "| web/new.ts | CREATE | frontend client | frontend |\n")
            client = FRONTEND.replace("createExport", "getCampaigns").replace("POST", "GET").replace("/api/exports", "/apps/campaign/campaigns")
            path = main.with_suffix("") / "frontend.md"
            write(path, client)
            self.assertEqual(checker.validate(main, root), [])
            write(path, client.replace("/apps/campaign/campaigns", "/wrong"))
            self.assertIn("CONTRACT_SIGNATURE_MISMATCH", {f.code for f in checker.validate(main, root)})


if __name__ == "__main__":
    unittest.main()
