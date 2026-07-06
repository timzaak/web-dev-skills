# Task State Contract

## Required Top-Level Shape

下面示例展示启用 miniapp 的状态片段；未启用 miniapp 的项目不包含 `phases.miniapp` 或 `tasks.miniapp`。

```json
{
  "feature": "sample-feature",
  "phase": "backend",
  "phases": {
    "backend": {"status": "pending"},
    "frontend": {"status": "pending"},
    "miniapp": {"status": "pending"},
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

- `phase` 只允许 supported phases：`backend | frontend | miniapp | demo`。
- `phases` / `tasks` 只要求包含当前任务的 `active_phases`；未启用 miniapp 的项目不得强制要求存在 `phases.miniapp` 或 `tasks.miniapp`。
- `miniapp` 启用规则统一参考 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md`。
- `status` 只允许 `pending | failed | completed | skipped | generated`。
  - `skipped`：阶段不适用于当前任务（如 backend 已实现，无需变更）
  - `generated`：任务规划已生成，尚未开始执行

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
- backend/frontend/miniapp/demo 全部 slots 均为 `completed` 或 `skipped`，且至少一个 slot `completed` => `completed`
- 全部 slots 均为 `generated` 或 `skipped`，且至少一个 slot `generated` => phase `generated`
- 其他情况 => `pending`
