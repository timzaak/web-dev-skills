---
name: t-run
description: Execute phased task plans by dispatching work to specialized sub-agents for backend, frontend, miniapp, Flutter, or demo phases.
argument-hint: "[任务名称] [--phase <backend|frontend|miniapp|flutter|demo>]"
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

## Input Contract

上游输入（来自 `/t-task` 产出）：
- `.ai/task/[feature]/.state.json` — 任务状态文件（必须存在且可解析）
  - 目标阶段必须已规划（`phases[phase]`、`tasks[phase]` 和对应阶段目录存在）
- `.ai/task/[feature]/<phase>/index.md` — 阶段总览
- `.ai/task/[feature]/<phase>/<slot>.md` — Slot manifest
- `.ai/task/[feature]/<phase>/<slot>/<ITEM-ID>-*.md` — Item 文件

## Output Contract

下游产出：
- 更新的 `.state.json` — item/slot/phase 状态变更
  - item 失败后写入 `last_error`
- item agent 执行产生的代码文件变更（由各 agent 自行产出）

## Purpose
- 读取 `.ai/task/[feature]/.state.json`。
- 按当前 phase 的 item DAG 选择可执行 item，但始终串行调度单个 sub agent。
- `/t-run` 的执行单元、slot 顺序、失败处理、所需上下文统一参考 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md`。
- `index.md` 和 slot manifest 只作为上下文和导航，不作为直接执行输入。
- backend 的 OpenAPI 导出与前端 API 生成验收由 `backend-accept` 负责。

## Args
| 参数 | 说明 |
|---|---|
| `[feature]` | 功能名 |
| `--phase <backend\|frontend\|miniapp\|flutter\|demo>` | 仅执行指定阶段；未指定时执行 `.state.json` 的当前阶段 |

## Preconditions
- `.ai/task/[feature]/.state.json` 必须存在且可解析。
- 目标阶段必须是 supported phase，且存在于当前任务 active phases 中；未启用 miniapp/Flutter 的项目不得执行对应 phase。
- 目标阶段必须已规划，且 `phases[phase]`、`tasks[phase]` 和当前阶段目录存在。
- 当前阶段目录必须存在。
- 当前阶段必须包含：
  - `index.md`
  - 对应 slot manifest：backend/frontend/miniapp/flutter 为 `dev.md`, `test.md`, `accept.md`；demo 为 `dev.md`, `accept.md`
  - 对应 item 目录和 item 文件

## Shared Contracts

- 状态结构与聚合规则：`${CLAUDE_PLUGIN_ROOT}/protocols/task-state-contract.md`
- phase/slot/item 执行规则：`${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md`

## Item Selection
按 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 选择可执行 item：

- 只执行 `pending` 或 `failed` item
- 依赖未满足不得跳过
- 同时存在多个可执行 item 时按 manifest 顺序或 item ID 字典序
- 若 DAG 成环、依赖缺失或 item 文件缺失，立即终止并提示重新运行 `/t-task-check`

## Sub Agent Context Contract
每个 item 必须按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 通过 `Agent` tool 启动，`subagent_type` 为 item 文件中的 `agent` 字段值。传入 prompt 必须包含最小上下文（见下方）。

最小上下文、可选增强上下文以及 backend-test 额外要求统一参考：

- `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md`
- `${CLAUDE_PLUGIN_ROOT}/protocols/backend-test-execution.md`

backend/test 特例：
- 必须读取 `test_item_type`，只允许 `authoring` 或 `runner`。
- 缺少 `test_item_type` 时拒绝执行，提示先运行 `/t-task-check` 或重建/修正 item。
- `authoring`：只编写或调整场景测试并做编译验证。
- `runner`：按 `${CLAUDE_PLUGIN_ROOT}/protocols/backend-test-execution.md`，在全部相关 authoring item 完成后集中执行定向测试、失败分类、生产代码修复委派和重测。
- `runner` 执行前必须从 `Expected Test Manifest`、变更文件和 package/module/test name 推导最小可靠定向命令；item 只给出全量 `uv run scripts/backend-test.py --` 且没有升级原因时，拒绝执行并提示重新运行 `/t-task-check` 或修正 item。
- 同一 item 同时包含“写新场景测试”和“修复生产代码直到通过”时拒绝执行。
- item 正文使用 `Goal / Work / Files / Validation / Handoff` 五个章节；执行 agent 以这些章节作为目标、动作、路径、验证和交接依据。

## State Transition
- 读取状态并确定执行范围。
- 依据 `${CLAUDE_PLUGIN_ROOT}/protocols/task-state-contract.md` 与 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 校验状态与 DAG。
- 执行 item 前不更新状态；中断恢复时，重新选择仍为 `pending` 或 `failed` 且依赖满足的 item。
- item 成功后写入：
   - `tasks[phase][slot].items[item_id].status = completed`
- item 失败后写入：
   - `tasks[phase][slot].items[item_id].status = failed`
   - `tasks[phase][slot].items[item_id].last_error = <summary>`
   - `tasks[phase][slot].status = failed`
   - `phases[phase].status = failed`
   - 停止依赖该 item 的后续执行
- 每个 item 完成或失败后重新聚合 slot 和 phase 状态。
- 若当前 item 成功且仍有可执行 item，则返回 Item Selection，继续串行选择下一个 item。
- backend 阶段在 `accept` slot 全部 completed 后聚合为 completed。

## Forbidden
- 直接执行 `dev.md`、`test.md`、`accept.md`。
- 只传 `index.md` 或 slot manifest 就开始执行。
- 忽略 item DAG，按文件名随意执行。
- 依赖未完成时执行下游 item。
- 同一 DAG 层并发执行多个 item。
- 一次启动多个 sub agents 或批量下发多个 item。
- 当前 item 未完成时，预取、提前执行或跨 slot 执行其他 item。
- 对 `backend-test` 直接下发"先跑全量 `uv run scripts/backend-test.py --`"而不做变更分析。
- backend/test runner 在未证明定向范围不可靠或门禁要求时执行全量 `uv run scripts/backend-test.py --`。

## Failure
- 状态文件缺失/损坏：终止并提示先运行 `/t-task [feature] --phase [phase]`。
- 依赖不满足：阻塞后续依赖 item。
- 状态写入失败：重试一次，失败则终止。
- agent 超时或编译级联错误：标记 item 为 `failed`，写入 `last_error`。
- 阶段未启用：提示当前项目未启用该阶段，并展示 `.state.json.phases` 中的 active phases。
- 阶段未生成：提示先运行 `/t-task [feature] --phase [phase]`。
- item 文件缺失或 DAG 非法：提示重建该阶段任务目录。
- item 缺少 `Goal/Work/Files/Validation/Handoff` 五章节：提示重新运行 `/t-task-check`；若确认为旧格式任务，重新运行 `/t-task [feature] --phase [phase]` 生成。

## Examples
```bash
# 按阶段执行
/t-run sample-feature --phase backend
```

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
dependencies:
  BE-D01: completed, file=.ai/task/sample-feature/backend/dev/BE-D01-domain-models.md
```
