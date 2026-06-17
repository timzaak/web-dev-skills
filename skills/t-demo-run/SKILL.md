---
name: t-demo-run
description: Run a single demo E2E test file, diagnose failures, dispatch fixes to agents, and re-run until pass.
argument-hint: "[测试文件路径]"
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
  - Agent
---

# 单文件 Demo 测试运行与修复

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`

## 目标
- 先对一个测试文件整体执行。
- 整体失败时，再按用例粒度顺序执行。
- 单个用例失败时先诊断，再分发到对应 agent 修复。
- 修复后必须执行相关后端/前端补测，不能只跑 Demo。
- 输出可恢复的任务状态与机器可解析结果。

## 使用方式
```bash
/t-demo-run demo/e2e/super-admin/super-admin-comprehensive-demo.e2e.ts
```

## 执行流程
- 参数校验。
- 测试文件必须存在且扩展名为 `.e2e.ts`。

- 运行前清理。
```bash
uv run scripts/cleanup-demo.py
```

- 先运行整个测试文件。
```bash
uv run scripts/demo-test-runner.py "[测试文件]" --run-id [RUN_ID]
```

- 若整个测试文件通过：
  - 不再拆分用例运行。
  - 直接输出结果 JSON。

- 若整个测试文件失败，列出测试用例。
```bash
uv run scripts/demo-test-runner.py "[测试文件]" --list-tests
```

- 为每个用例创建任务并顺序执行。
```bash
uv run scripts/demo-test-runner.py "[测试文件]" --run-id [RUN_ID] --grep "[测试标题]"
```

- 单用例失败修复循环（最多 6 次）。
- 先通过 `Agent(subagent_type="demo-diagnose")` 启动诊断 subagent，传入 testFile、runId、testCaseTitle，生成结构化诊断。
- 按诊断结果通过 `Agent` tool 分发到对应修复 subagent：`Agent(subagent_type="demo-dev")` / `Agent(subagent_type="frontend-dev")` / `Agent(subagent_type="backend-dev")` / `Agent(subagent_type="miniapp-dev")`。
- 读取修复 agent 返回的 `tests_to_run`（必填）并校验字段：
  - `layer`: `backend|frontend|miniapp|demo`
  - `command`: 可直接执行命令
  - `reason`: 关联说明
  - `required`: 是否必须通过（默认 `true`）
- 执行补测（按层顺序串行）：`backend -> frontend -> miniapp -> demo`。
- 补测命令必须来自允许入口：
  - 后端：`uv run scripts/backend-test.py -- [filter]`
  - 前端：`cd frontend && npm run test:run -- [pattern]`
  - 小程序：`cd miniapp && npm run typecheck` 或 `cd miniapp && npm run build:weapp`
  - Demo：`uv run scripts/demo-test-runner.py "[测试文件]" --run-id [RUN_ID] --grep "[测试标题]"`
- miniapp 补测只在目标项目存在 `miniapp/` 或诊断报告明确归因到小程序交付线时执行；未启用 miniapp 的项目跳过该层。
- 若 agent 未返回 `tests_to_run`：
  - 记录契约缺失（P1）
  - 执行最小兜底补测（按改动层至少 1 条 backend/frontend/miniapp 相关测试）
- 重新运行当前用例验证修复（即 `demo` 层验证）。

- 结果输出。
- 最后一行必须输出机器可解析 JSON，格式固定为：
```text
Result: {"success":"true|false","fixed":"true|false","logs":"demo/test-results/runs/[RUN_ID]","exit_code":0,"test_file":"demo/e2e/...","run_id":"[RUN_ID]","error":""}
```
- 字段含义：
  - `success`: 最终 Demo 验证是否通过。
  - `fixed`: 本次是否经历失败后修复并通过；首次整体通过时为 `false`。
  - `logs`: 本次运行主日志目录，优先使用 `demo-test-runner.py` 返回的 `logs`。
  - `exit_code`: 最终 Demo 验证退出码。
  - `test_file`: 输入测试文件路径。
  - `run_id`: 本次运行 ID。
  - `error`: 失败时的简要错误；成功时为空字符串。
- 不再额外要求自然语言“最终总结”；必要说明只保留为失败诊断、修复记录或 `error` 字段。

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
- 必须先整体运行测试文件；只有整体失败时才拆分用例。
- 拆分后的用例执行必须串行。
- 每个失败用例必须有诊断记录。
- 每次修复后必须先执行相关层补测，再执行 Demo 验证。
- 必须输出最后一行 `Result: {...}`。
