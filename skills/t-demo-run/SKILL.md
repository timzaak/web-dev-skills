---
name: t-demo-run
context: fork
description: >
  运行单个 Demo 测试文件并按失败类型触发诊断与修复，支持任务状态跟踪与恢复。
argument-hint: [测试文件路径]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Task
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
  - Write
---

# 单文件 Demo 测试运行与修复

运行时边界统一参考：`protocols/runtime-boundaries.md`

## 目标
- 对一个测试文件按用例粒度执行。
- 失败时先诊断，再分发到对应 agent 修复。
- 修复后必须执行相关后端/前端补测，不能只跑 Demo。
- 输出可恢复的任务状态与最终汇总。

## 使用方式
```bash
/t-demo-run demo/e2e/super-admin/super-admin-comprehensive-demo.e2e.ts
```

## 执行流程
1. 参数校验。
- 测试文件必须存在且扩展名为 `.e2e.ts`。

2. 运行前清理。
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/cleanup-demo.py
```

3. 列出测试用例。
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-test-runner.py "[测试文件]" --list-tests
```

4. 为每个用例创建任务并顺序执行。
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-test-runner.py "[测试文件]" --run-id [RUN_ID] --grep "[测试标题]"
```

5. 失败修复循环（最多 6 次）。
- 先调用 `demo-diagnose` 生成结构化诊断。
- 按诊断结果分发：`demo-dev` / `frontend-dev` / `backend-dev`。
- 读取修复 agent 返回的 `tests_to_run`（必填）并校验字段：
  - `layer`: `backend|frontend|demo`
  - `command`: 可直接执行命令
  - `reason`: 关联说明
  - `required`: 是否必须通过（默认 `true`）
- 执行补测（按层顺序串行）：`backend -> frontend -> demo`。
- 补测命令必须来自允许入口：
  - 后端：`uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- [filter]`
  - 前端：`cd frontend && npm run test:run -- [pattern]`
  - Demo：`uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-test-runner.py "[测试文件]" --run-id [RUN_ID] --grep "[测试标题]"`
- 若 agent 未返回 `tests_to_run`：
  - 记录契约缺失（P1）
  - 执行最小兜底补测（按改动层至少 1 条 backend/frontend 相关测试）
- 重新运行当前用例验证修复（即 `demo` 层验证）。

6. 汇总输出。
- 控制台输出通过/修复/失败统计。
- 写入 `.ai/quality/demo-run-[name]-[YYYYMMDD-HHMMSS].md`。
- 报告必须包含：
  - `fix_attempts`
  - `related_tests`（命令、层级、结果、耗时、reason）
  - `demo_result`
  - `overall_risk`（当补测失败但 Demo 通过时标记"通过但高风险"）

## 恢复机制
当流程中断时：
- 读取 `TaskList`。
- 找到 `pending` 且依赖已满足的任务继续执行。

## 失败处理
- 环境启动失败：停止并记录错误。
- 无可用修复方案：标记该用例失败，继续下一个。
- 达到最大重试次数：标记失败并继续。
- 补测失败：记录失败与风险，不阻断本用例修复循环，继续 Demo 重跑与后续尝试。

## 质量门禁
- 单次执行只处理一个测试文件。
- 用例执行必须串行。
- 每个失败用例必须有诊断记录。
- 每次修复后必须先执行相关层补测，再执行 Demo 验证。
- 必须输出最终汇总。

## 相关引用
- `agents/demo-diagnose.md`
- `agents/demo-dev.md`
- `agents/backend-dev.md`
- `agents/frontend-dev.md`
- `protocols/tests-to-run-contract.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/demo/index.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/demo/common-failures.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/demo/selector-repair.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/demo/test-maintenance.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/demo/e2e-testing.md`
