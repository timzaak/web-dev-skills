# Task State Contract

## Required Top-Level Shape

下面示例展示启用 miniapp 与 Flutter 的状态片段；未启用的项目不包含对应 phase 或 tasks。

```json
{
  "feature": "sample-feature",
  "phase": "backend",
  "phases": {
    "backend": {"status": "pending"},
    "frontend": {"status": "pending"},
    "miniapp": {"status": "pending"},
    "flutter": {"status": "pending"},
    "demo": {"status": "pending"}
  },
  "tasks": {
    "backend": {
      "dev": {
        "status": "pending",
        "manifest": ".ai/task/sample-feature/backend/dev.md",
        "items": {}
      },
      "test": {
        "status": "pending",
        "manifest": ".ai/task/sample-feature/backend/test.md",
        "items": {}
      },
      "accept": {
        "status": "pending",
        "manifest": ".ai/task/sample-feature/backend/accept.md",
        "items": {}
      }
    }
  },
  "metadata": {
    "design_document": ".ai/design/sample-feature.md"
  }
}
```

## Item Object

每个 item 至少包含：

- `status`
- `file`
- `agent`
- `depends_on`

按执行结果补充：

- 失败时：`last_error`

`.state.json` 不记录时间类元数据。不要写入 `generated_at`、`created_at`、`updated_at`、`started_at` 或 `completed_at`；是否已规划、失败或完成只由 `status`、任务目录和 manifest/item 文件存在性表达。

## State Rules

- `phase` 只允许 supported phases：`backend | frontend | miniapp | flutter | demo`。
- `phases` / `tasks` 只要求包含当前任务的 `active_phases`；未启用 miniapp/Flutter 的项目不得强制要求对应 phase。
- `miniapp` / `flutter` 启用规则统一参考 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md`。
- `status` 只允许 `pending | failed | completed | skipped | generated`。
  - `skipped`：阶段不适用于当前任务（如 backend 已实现，无需变更）
  - `generated`：任务规划已生成，尚未开始执行

## Execution Entry Transition

`generated` 是规划完成态，`pending` 是执行队列态。`/t-run` 对目标 phase 完成状态文件、阶段目录、manifest/item 和 DAG 校验后，必须在选择首个 item 前执行一次启动归一化：

- 将 `tasks[phase][slot].items[*].status == generated` 的 item 全部改为 `pending`；只处理本次目标 phase。
- 保留 `pending | failed | completed | skipped` item 原状态，不得借启动归一化重置失败或已完成结果。
- item 归一化后，按下方聚合规则重新计算目标 phase 的全部 slot 状态和 phase 状态，并在启动任何 agent 前一次性写回 `.state.json`。
- 若写回失败，重试一次；仍失败则终止执行且不启动 agent。再次运行 `/t-run` 时从当前持久化状态重新归一化。
- 该迁移只表示任务进入执行队列，不表示 item 已开始执行，也不引入 `running` 状态。

`/t-task-check` 只校验状态，不执行该迁移。`/t-task` 新生成且尚未进入执行队列的 item 保持 `generated`。

## Aggregation Rules

slot 状态：

- 任一 item `failed` => slot `failed`
- 全部 items `skipped` => slot `skipped`
- 全部 items 均为 `completed` 或 `skipped`，且至少一个 item `completed` => slot `completed`
- 全部 items 均为 `generated` 或 `skipped`，且至少一个 item `generated` => slot `generated`
- 否则 slot `pending`

phase 状态：

- 任一 slot `failed` => phase `failed`
- 全部 slots `skipped` => phase `skipped`
- 当前 active phase 的全部 slots 均为 `completed` 或 `skipped`，且至少一个 slot `completed` => `completed`
- 全部 slots 均为 `generated` 或 `skipped`，且至少一个 slot `generated` => phase `generated`
- 其他情况 => `pending`
