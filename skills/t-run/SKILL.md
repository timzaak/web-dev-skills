---
name: t-run
context: fork
argument-hint: [任务名称] [--phase <backend|frontend|miniapp|demo>]
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
---

# 任务执行

运行时边界统一参考：`protocols/runtime-boundaries.md`

## Input Contract

上游输入（来自 `/t-task` 产出）：
- `.ai/task/[feature]/.state.json` — 任务状态文件（必须存在且可解析）
  - 不得包含旧状态字段或 `agents` 根字段
  - 目标阶段必须已生成（`phases[phase].generated_at` 非空）
- `.ai/task/[feature]/<phase>/index.md` — 阶段总览
- `.ai/task/[feature]/<phase>/<slot>.md` — Slot manifest
- `.ai/task/[feature]/<phase>/<slot>/<ITEM-ID>-*.md` — Item 文件

前置阶段状态要求：
- `frontend` 依赖 `backend == completed`
- `miniapp` 是可选阶段，启用时依赖 `frontend == completed`
- `demo` 依赖 active phases 中排在它之前的最后一个交付阶段 completed

## Output Contract

下游产出（供后续阶段或 `/t-backend-finalize` 使用）：
- 更新的 `.state.json` — item/slot/phase 状态变更
  - item 完成后写入 `completed_at` 和 `handoff_summary`
  - item 失败后写入 `last_error`
- item agent 执行产生的代码文件变更（由各 agent 自行产出）

## Purpose
- 读取 `.ai/task/[feature]/.state.json`。
- 按当前 phase 的 item DAG 选择可执行 item，但始终串行调度单个 sub agent。
- `/t-run` 的执行单元、slot 顺序、失败处理、所需上下文统一参考 `protocols/task-phase-execution.md`。
- `index.md` 和 slot manifest 只作为上下文和导航，不作为直接执行输入。
- backend 的 `finalize.md` 不由 `/t-run` 执行。

## Args
| 参数 | 说明 |
|---|---|
| `[feature]` | 功能名 |
| `--phase <backend\|frontend\|miniapp\|demo>` | 仅执行指定阶段；未指定时执行 `.state.json` 的当前阶段 |

## Preconditions
- `.ai/task/[feature]/.state.json` 必须存在且可解析。
- `.state.json` 不得包含旧状态字段或 `agents` 根字段。
- 目标阶段必须是 supported phase，且存在于当前任务 active phases 中；未启用 miniapp 的项目不得执行 `--phase miniapp`。
- 目标阶段必须已生成，且 `phases[phase].generated_at` 非空。
- 前置阶段依赖统一参考 `protocols/task-phase-execution.md`。
- 当前阶段目录必须存在。
- 当前阶段必须包含：
  - `index.md`
  - 对应 slot manifest：backend/frontend/miniapp 为 `dev.md`, `test.md`, `accept.md`；demo 为 `dev.md`, `accept.md`
  - 对应 item 目录和 item 文件
  - backend 阶段额外要求 `finalize.md`

## Shared Contracts

- 状态结构与聚合规则：`protocols/task-state-contract.md`
- phase/slot/item 执行规则：`protocols/task-phase-execution.md`

## Item Selection
按 `protocols/task-phase-execution.md` 选择可执行 item：

- 只执行 `pending` 或 `failed` item
- 依赖未满足不得跳过
- 同时存在多个可执行 item 时按 manifest 顺序或 item ID 字典序
- 若 DAG 成环、依赖缺失或 item 文件缺失，立即终止并提示重新运行 `/t-task-check`

## Sub Agent Context Contract
最小上下文、可选增强上下文以及 backend-test 额外要求统一参考：

- `protocols/task-phase-execution.md`
- `protocols/backend-test-execution.md`

## Recovery Protocol

- 状态写入失败：重试写入 2 次，仍失败则终止
- agent 超时：标记 item 为 `failed`，下次 `/t-run` 重试
- 编译级联错误：标记 `failed` 并注明 `compilation cascade`
- 连续 3 次同一 item 失败、DAG 环路、scope 明显不匹配时转人工介入
- 若上游 item 无 `handoff_summary`，可降级启动，但必须显式标注 handoff 缺失

## State Transition
1. 读取状态并确定执行范围。
2. 依据 `protocols/task-state-contract.md` 与 `protocols/task-phase-execution.md` 校验状态与 DAG。
3. 执行 item 前检查当前 phase 是否已有任何 item 为 `running`：
   - 若存在，立即终止，不启动新 agent。
   - 提示先确认该 item 的真实执行结果，并恢复或修正 `.state.json` 后再重试。
4. 执行 item 前写入：
   - `tasks[phase][slot].items[item_id].status = running`
   - `tasks[phase][slot].items[item_id].started_at = <timestamp>`
   - `tasks[phase][slot].status = running`
   - `phases[phase].status = running`
5. item 成功后写入：
   - `tasks[phase][slot].items[item_id].status = completed`
   - `tasks[phase][slot].items[item_id].completed_at = <timestamp>`
   - `tasks[phase][slot].items[item_id].handoff_summary = <summary>`
6. item 失败后写入：
   - `tasks[phase][slot].items[item_id].status = failed`
   - `tasks[phase][slot].items[item_id].last_error = <summary>`
   - `tasks[phase][slot].status = failed`
   - `phases[phase].status = failed`
   - 停止依赖该 item 的后续执行
7. 每个 item 完成或失败后重新聚合 slot 和 phase 状态。
8. 若当前 item 成功且仍有可执行 item，则返回 Item Selection，继续串行选择下一个 item。
9. backend 阶段在 `accept` slot 全部 completed 后停止，并提示执行 `/t-backend-finalize [feature]`。

## Forbidden
- 生成或依赖旧状态字段。
- 生成或依赖 `agents` 根字段。
- 直接执行 `dev.md`、`test.md`、`accept.md`。
- 只传 `index.md` 或 slot manifest 就开始执行。
- 忽略 item DAG，按文件名随意执行。
- 依赖未完成时执行下游 item。
- 同一 DAG 层并发执行多个 item。
- 一次启动多个 sub agents 或批量下发多个 item。
- 当前 item 未完成并写回状态时，预取、提前执行或跨 slot 执行其他 item。
- 对 `backend-test` 直接下发"先跑全量 `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py`"而不做变更分析。
- backend `accept` 完成后自动执行 `finalize.md`。

## Failure
- 状态文件缺失/损坏：终止并提示先运行 `/t-task [feature] --phase [phase]`。
- 状态文件包含旧结构字段：终止并提示删除旧任务目录后重新运行 `/t-task`。
- 依赖不满足：阻塞后续依赖 item。
- 状态写入失败：重试一次，失败则终止。
- 阶段校验失败：提示先完成前置阶段。
- 阶段未启用：提示当前项目未启用该阶段，并展示 `.state.json.phases` 中的 active phases。
- 阶段未生成：提示先运行 `/t-task [feature] --phase [phase]`。
- item 文件缺失或 DAG 非法：提示重建该阶段任务目录。

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
item_file: .ai/task/sample-feature/backend/dev/BE-D02-domain-models.md
slot_manifest: .ai/task/sample-feature/backend/dev.md
phase_index: .ai/task/sample-feature/backend/index.md
dependencies:
  BE-D01: completed, handoff=<summary>
```

## 相关引用
- `protocols/runtime-boundaries.md`
- `protocols/task-state-contract.md`
- `protocols/task-phase-execution.md`
- `protocols/backend-test-execution.md`
- `skills/t-task/SKILL.md`
- `skills/t-backend-finalize/SKILL.md`
- `skills/t-task-check/SKILL.md`
- `skills/t-task/references/phase-validator.md`
