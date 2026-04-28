# Task State Contract

定义 `.ai/task/[feature]/.state.json` 的唯一结构真相。

## Required Top-Level Shape

下面示例展示启用 miniapp 的状态片段；未启用 miniapp 的项目不包含 `phases.miniapp` 或 `tasks.miniapp`。

```json
{
  "feature": "sample-feature",
  "phase": "backend",
  "phases": {
    "backend": {"status": "pending", "generated_at": null},
    "frontend": {"status": "pending", "generated_at": null},
    "miniapp": {"status": "pending", "generated_at": null},
    "demo": {"status": "pending", "generated_at": null}
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
      },
      "finalize": {
        "status": "pending",
        "file": ".ai/task/sample-feature/backend/finalize.md"
      }
    }
  },
  "metadata": {
    "design_document": ".ai/design/sample-feature.md",
    "created_at": "<timestamp>",
    "updated_at": "<timestamp>"
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

- 成功时：`started_at`, `completed_at`, `handoff_summary`
- 失败时：`started_at`, `last_error`

## Compatibility Rules

- 不兼容旧状态字段。
- 不允许出现 `agents` 根字段。
- `phase` 只允许 supported phases：`backend | frontend | miniapp | demo`。
- `phases` / `tasks` 只要求包含当前任务的 `active_phases`；未启用 miniapp 的项目不得强制要求存在 `phases.miniapp` 或 `tasks.miniapp`。
- `miniapp` 启用规则统一参考 `protocols/task-phase-execution.md`。
- `status` 只允许 `pending | running | failed | completed | awaiting_finalize`。

## Aggregation Rules

slot 状态：

- 任一 item `running` => slot `running`
- 任一 item `failed` => slot `failed`
- 全部 items `completed` => slot `completed`
- 否则 slot `pending`

phase 状态：

- 任一 slot `running` => phase `running`
- 任一 slot `failed` => phase `failed`
- backend 的 `dev/test/accept` 全部 completed 且 `finalize` 未 completed => `awaiting_finalize`
- backend 含 `finalize` completed => `completed`
- frontend/miniapp/demo 全部 slot completed => `completed`
- 其他情况 => `pending`
