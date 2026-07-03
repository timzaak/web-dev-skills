---
name: t-backend-test-run
description: Run targeted Java Spring Boot backend tests, diagnose failures, delegate production-code fixes, and retest without weakening scenario-test semantics.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Task
  - Agent
---

# 后端测试执行

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`

本 skill 只负责 backend/test 集中 runner item 的测试执行、失败诊断、生产代码修复编排和重测。它不编写新场景测试，不改变业务验收语义。场景测试 authoring 属于 `backend-test` authoring item。

## 读取顺序

执行前按顺序读取：

- 当前 runner item 文件
- `${CLAUDE_PLUGIN_ROOT}/guides/backend/testing.md`
- `${CLAUDE_PLUGIN_ROOT}/protocols/backend-test-execution.md`
- `${CLAUDE_PLUGIN_ROOT}/protocols/tests-to-run-contract.md`

规则：

- 后端测试入口和命令形态以 `${CLAUDE_PLUGIN_ROOT}/guides/backend/testing.md` 为准。
- runner 的范围收敛、失败分类、委派和升级策略以 `${CLAUDE_PLUGIN_ROOT}/protocols/backend-test-execution.md` 为准。

## 核心流程

- 用 `git status` 和 `git diff --name-only` 分析改动范围。
- 读取 runner item 的 `Expected Test Manifest`；如果缺失，则从 authoring item 的 handoff 中重建预期测试清单，并报告 manifest 缺口。
- 执行测试前，运行或等价模拟 `uv run scripts/check-test-runner-coverage.py <feature> --layer backend`，确认文档中的后端命令会选中全部预期测试。
- 根据 `${CLAUDE_PLUGIN_ROOT}/protocols/backend-test-execution.md` 选择能覆盖 runner 所依赖全部 authoring item 的最窄可靠命令。
- 使用 `uv run scripts/backend-test.py -- [filter]` 运行定向测试；除非拆成多条命令能明显提升失败恢复性，否则按同一业务场景或 package/module 合并执行。
- 将失败分类为编译失败、运行时失败、断言失败、环境问题或语义不清。
- 生产代码问题委派给 `backend-dev`，并附带场景测试写入限制。
- 重新运行定向命令。
- 只有用户明确要求，或定向范围已经无法可靠覆盖时，才升级为全量测试。

## 语义安全

runner 只能修复机械性测试问题，例如 import、模块注册、helper 调用签名或明显路径错误。

runner 不得修改：

- 场景测试断言
- 状态码预期
- 权限预期
- 业务规则预期

如果测试语义可能有误，必须停止，并使用 `${CLAUDE_PLUGIN_ROOT}/protocols/backend-test-execution.md` 中的 stop report。

## 委派契约

委派给 `backend-dev` 时，按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 调用 `Agent(subagent_type="backend-dev")`。prompt 中包含：

```markdown
任务：在生产代码中修复这个后端测试失败。

测试命令：`<command>`
失败测试：`<test_name>`
失败信息：`<message>`
相关文档：`<User Story/PRD paths>`
判断为实现问题的原因：`<diagnosis>`

Hard constraints:
- Do not modify `backend/**/src/test/**` scenario/integration test files.
- Do not weaken or rewrite scenario/integration tests to match broken production behavior.
- Do not change scenario-test assertions, status-code expectations, permission expectations, or business-rule expectations.
- If a test semantics change seems required, return `requires_test_semantics_change` with evidence instead of editing tests.
```

## 报告

报告必须包含：预期测试数量、被命令选中的测试数量、缺失测试（如有）、已执行命令、通过/失败结果、已应用修复、变更文件、语义冲突，以及是否升级到全量测试。
