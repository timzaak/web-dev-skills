---
name: t-run
description: Execute phased task plans for backend, frontend, miniapp, Flutter, Web Demo, or Flutter Demo.
argument-hint: "[任务名称] [--phase <backend|frontend|miniapp|flutter|web-demo|flutter-demo>]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Task
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
  - Write
  - Bash
  - Agent
---

# 任务执行

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`

执行时以当前 item 的成功标准和最小必要验证为目标；遇到冲突、缺失上下文或无法判断的语义问题时停止并说明。

## 前置条件

- `.ai/task/[feature]/.state.json` 必须存在且可解析；目标阶段必须是 supported phase 且存在于当前任务 active phases（未启用 miniapp/Flutter 的项目不得执行对应 phase），并已规划（`phases[phase]`、`tasks[phase]` 和对应阶段目录存在）。
- 当前阶段目录必须包含：`index.md`、对应 slot manifest（backend/frontend/miniapp/flutter 为 `dev.md`, `test.md`, `accept.md`；web-demo/flutter-demo 为 `dev.md`, `accept.md`）、对应 item 目录和 item 文件。

## 共享契约

执行单元、slot 顺序、item 选择（含启动归一化）、agent 最小上下文、backend/test 特殊规则和失败处理统一参考：

- `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md`
- `${CLAUDE_PLUGIN_ROOT}/protocols/task-state-contract.md`
- `${CLAUDE_PLUGIN_ROOT}/protocols/backend-test-execution.md`

## 参数

| 参数 | 说明 |
|---|---|
| `[feature]` | 功能名 |
| `--phase <backend\|frontend\|miniapp\|flutter\|web-demo\|flutter-demo>` | 仅执行指定阶段；未指定时执行 `.state.json` 的当前阶段 |

## Input Contract

上游输入（来自 `/t-task` 产出）：

- `.ai/task/[feature]/.state.json` — 任务状态文件（必须存在且可解析）
- `.ai/task/[feature]/<phase>/index.md` — 阶段总览
- `.ai/task/[feature]/<phase>/<slot>.md` — Slot manifest（slot 内 item 执行顺序的真源）
- `.ai/task/[feature]/<phase>/<slot>/<ITEM-ID>-*.md` — Item 文件（`Goal / Work / Files / Validation / Handoff` 五章节，即执行依据）

`index.md` 和 slot manifest 不作为直接执行单元。backend 的 OpenAPI 导出与前端 API 生成验收由 `backend-accept` 负责。

## 执行循环

1. 读取状态并确定执行范围，按共享契约校验状态与执行顺序。
2. 完成校验后、启动任何 agent 前，将目标 phase 中全部 `generated` item 归一化为 `pending`，重新聚合对应 slot/phase 并一次性写回 `.state.json`（保留其他状态不变）；归一化写回失败时按状态写入失败处理，不得启动 agent。
3. 按共享契约选择第一个 `pending` 或 `failed` item，通过 `Agent` tool 启动 `subagent_type` 为 item `agent` 字段值的 sub agent（调度规则见 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md`，最小上下文按 task-phase-execution 的 Agent Context）。

   最小上下文示例：

   ```text
   # 调用 backend-dev item 时的最小上下文
   feature: sample-feature
   phase: backend
   slot: dev
   item_id: BE-D02
   agent: backend-dev
   agent_spec: ${CLAUDE_PLUGIN_ROOT}/agents/backend-dev.md
   item_file: .ai/task/sample-feature/backend/dev/BE-D02-domain-models.md
   slot_manifest: .ai/task/sample-feature/backend/dev.md
   phase_index: .ai/task/sample-feature/backend/index.md
   previous_items:
     BE-D01: completed, file=.ai/task/sample-feature/backend/dev/BE-D01-domain-models.md, handoff=<必要片段>
   ```

4. item 成功后写入 `tasks[phase][slot].items[item_id].status = completed`；失败后写入 `status = failed`、`last_error = <summary>`，并把 `tasks[phase][slot].status` 与 `phases[phase].status` 聚合为 `failed`，停止当前 phase 的后续执行。
5. 每个 item 完成或失败后重新聚合 slot 和 phase 状态；item 成功且仍有可执行 item 时回到步骤 3 继续串行执行。backend 阶段在 `accept` slot 全部 completed 后聚合为 completed。

## backend/test 特例

- item 缺少 `test_item_type` 或类型非法时拒绝执行，提示先运行 `/t-task-check` 或重建/修正 item。
- `authoring`：只编写或调整场景测试并做编译验证。
- `runner`：按 `${CLAUDE_PLUGIN_ROOT}/protocols/backend-test-execution.md` 执行；item 只给出全量 `uv run scripts/backend-test.py --` 且没有升级原因时拒绝执行。
- 同一 item 同时包含"写新场景测试"和"修复生产代码直到通过"时拒绝执行。

## 禁止事项

- 直接执行 `dev.md`、`test.md`、`accept.md`，或只传 `index.md` / slot manifest 就开始执行。
- 忽略 manifest 顺序，按文件名或 `.state.json` 对象顺序执行。
- 一次启动多个 sub agent、批量下发多个 item，或当前 item 未完成时预取、提前执行、跨 slot 执行其他 item。

## 失败处理

- 状态文件缺失/损坏：终止并提示先运行 `/t-task [feature] --phase [phase]`。
- 前序 item 失败：停止当前 phase，修复后从该 item 恢复。
- 状态写入失败：重试一次，失败则终止。
- agent 超时或编译级联错误：标记 item 为 `failed`，写入 `last_error`。
- 阶段未启用：提示当前项目未启用该阶段，并展示 `.state.json.phases` 中的 active phases。
- 阶段未生成：提示先运行 `/t-task [feature] --phase [phase]`。
- item 文件缺失或 manifest 顺序非法：提示重建该阶段任务目录。
- item 缺少五章节：提示重新运行 `/t-task-check`；若确认为旧格式任务，重新运行 `/t-task [feature] --phase [phase]` 生成。
