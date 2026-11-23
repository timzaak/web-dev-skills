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


def main_doc(stack: str = "frontend", status: str = "适用") -> str:
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
| {stack} | {stack}.md | {status} |
### 4.3 跨端契约（API 契约摘要）
| Operation ID | 方法 | 路径 | 用途 | 调用方 |
|---|---|---|---|---|
| createExport | POST | /api/exports | create | {stack} |
## 6. 测试与验收策略
## 7. 风险与验证动作
## 8. 文件影响范围（全量汇总）
| 文件 | 操作 | 说明 | 来源分端 |
|---|---|---|---|
| src/new.rs | CREATE | adjacent to src/lib.rs | backend |
| web/new.ts | CREATE | adjacent to web/index.ts | {stack} |
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


class DesignValidationTests(unittest.TestCase):
    def make_design(self, root: Path, stack: str = "frontend", child_content: str = FRONTEND) -> Path:
        (root / "src").mkdir(exist_ok=True)
        (root / "web").mkdir(exist_ok=True)
        (root / "src/lib.rs").write_text("", encoding="utf-8")
        (root / "web/index.ts").write_text("", encoding="utf-8")
        main = root / ".ai/design/sample.md"
        write(main, main_doc(stack))
        write(root / ".ai/design/sample/backend.md", BACKEND.replace("frontend", stack))
        write(root / f".ai/design/sample/{stack}.md", child_content)
        return main

    def test_valid_design_and_json_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = self.make_design(root)
            self.assertEqual(checker.validate(main, root), [])
            output = io.StringIO()
            with redirect_stdout(output):
                code = checker.main([str(main), "--repo-root", str(root), "--json"])
            self.assertEqual(code, 0)
            self.assertEqual(
                json.loads(output.getvalue())["design_documents"],
                [".ai/design/sample.md", ".ai/design/sample/backend.md", ".ai/design/sample/frontend.md"],
            )

    def test_core_structural_violations(self) -> None:
        cases = [
            ("missing_stack_doc", lambda r, m: (r / ".ai/design/sample/frontend.md").unlink(), "STACK_DOC_MISSING"),
            (
                "contract_mismatch",
                lambda r, m: write(r / ".ai/design/sample/frontend.md", FRONTEND.replace("/api/exports", "/api/wrong")),
                "CONTRACT_SIGNATURE_MISMATCH",
            ),
            (
                "create_parent_missing",
                lambda r, m: (
                    write(m, m.read_text(encoding="utf-8").replace("src/new.rs", "missing/new.rs")),
                    write(r / ".ai/design/sample/backend.md", BACKEND.replace("src/new.rs", "missing/new.rs")),
                ),
                "CREATE_PARENT_MISSING",
            ),
            (
                "impact_not_aggregated",
                lambda r, m: write(r / ".ai/design/sample/backend.md", BACKEND.replace("src/new.rs", "src/other.rs")),
                "IMPACT_NOT_AGGREGATED",
            ),
        ]
        for label, mutate, expected in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                main = self.make_design(root)
                mutate(root, main)
                self.assertIn(expected, {f.code for f in checker.validate(main, root)})

    def test_require_complete_state_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = self.make_design(root)
            state = root / ".ai/design/sample/.state.json"
            self.assertIn("DESIGN_GENERATION_INCOMPLETE", {f.code for f in checker.validate(main, root, require_complete=True)})
            write(state, '{"status":"in_progress"}')
            self.assertEqual(checker.validate(main, root), [])
            self.assertIn("DESIGN_GENERATION_INCOMPLETE", {f.code for f in checker.validate(main, root, require_complete=True)})
            write(state, '{"status":"complete"}')
            self.assertEqual(checker.validate(main, root, require_complete=True), [])

    def test_flutter_and_extension_stacks(self) -> None:
        flutter_doc = """
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
"""
        extension_doc = """
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
"""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = self.make_design(root, "flutter", flutter_doc)
            self.assertEqual(checker.validate(main, root), [])
            write(
                main.with_suffix("") / "flutter.md",
                flutter_doc.replace("## 10. 详细设计", "## 12. 详细设计").replace("## 12. 文件影响范围", "## 14. 文件影响范围"),
            )
            self.assertEqual(checker.validate(main, root), [])

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            main = self.make_design(root, "extension", extension_doc)
            self.assertEqual(checker.validate(main, root), [])
            self.assertIn(main.with_suffix("") / "extension.md", checker.design_documents(main))

    def test_shopify_contract_source_and_no_api_rules(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "app" / "routes").mkdir(parents=True)
            (root / "web").mkdir()
            main = root / ".ai/design/sample.md"
            stack = main.with_suffix("") / "shopify.md"
            write(main, SHOPIFY_MAIN)
            write(stack, SHOPIFY_STACK)
            self.assertEqual(checker.validate(main, root), [])

            # Client dependency validated against shopify.md as contract source
            write(
                main,
                SHOPIFY_MAIN.replace("| frontend | frontend.md | 不适用 |", "| frontend | frontend.md | 适用 |")
                + "| web/new.ts | CREATE | frontend client | frontend |\n",
            )
            client = FRONTEND.replace("createExport", "getCampaigns").replace("POST", "GET").replace("/api/exports", "/apps/campaign/campaigns")
            write(main.with_suffix("") / "frontend.md", client)
            self.assertEqual(checker.validate(main, root), [])
            write(main.with_suffix("") / "frontend.md", client.replace("/apps/campaign/campaigns", "/wrong"))
            self.assertIn("CONTRACT_SIGNATURE_MISMATCH", {f.code for f in checker.validate(main, root)})
            (main.with_suffix("") / "frontend.md").unlink()

            # Contract/heading failure modes
            for m_txt, s_txt, expected in (
                (SHOPIFY_MAIN, SHOPIFY_STACK.replace("/apps/campaign/campaigns", "/wrong"), "MAIN_CONTRACT_MISMATCH"),
                (SHOPIFY_MAIN, SHOPIFY_STACK.replace("| getCampaigns | GET | /apps/campaign/campaigns | - | items | 401 | storefront |\n", ""), "SHOPIFY_CONTRACT_EMPTY"),
                (SHOPIFY_MAIN, SHOPIFY_STACK.replace("## 8. 测试与验收", "## 8. 测试"), "STACK_HEADING_MISSING"),
                (SHOPIFY_MAIN.replace("| getCampaigns | GET | /apps/campaign/campaigns | list | storefront |\n", ""), SHOPIFY_STACK, "MAIN_CONTRACT_MISMATCH"),
            ):
                with self.subTest(expected=expected):
                    write(main, m_txt)
                    write(stack, s_txt)
                    self.assertIn(expected, {f.code for f in checker.validate(main, root)})

            # No-API feature requires explicit reason in both documents
            reason = "不适用：仅修改静态 block 展示，不新增、修改或消费接口。\n"
            no_api_main = SHOPIFY_MAIN.replace("| getCampaigns | GET | /apps/campaign/campaigns | list | storefront |\n", reason)
            no_api_stack = SHOPIFY_STACK.replace("| getCampaigns | GET | /apps/campaign/campaigns | - | items | 401 | storefront |\n", reason)
            write(main, no_api_main)
            write(stack, no_api_stack)
            self.assertEqual(checker.validate(main, root), [])
            write(main, no_api_main.replace(reason, ""))
            self.assertIn("MAIN_CONTRACT_EMPTY", {f.code for f in checker.validate(main, root)})
            write(main, no_api_main)
            write(stack, no_api_stack.replace(reason, "不适用\n"))
            self.assertIn("SHOPIFY_CONTRACT_EMPTY", {f.code for f in checker.validate(main, root)})


if __name__ == "__main__":
    unittest.main()
