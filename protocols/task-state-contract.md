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
    "web-demo": {"status": "pending"},
    "extension-demo": {"status": "pending"},
    "flutter-demo": {"status": "pending"}
  },
  "tasks": {
    "backend": {
      "dev": {
        "status": "pending",
        "manifest": ".ai/task/sample-feature/backend/dev.md",
        "items": {
          "BE-D01": {"status": "pending", "file": ".ai/task/sample-feature/backend/dev/BE-D01-implement.md", "agent": "backend-dev"}
        }
      },
      "accept": {
        "status": "pending",
        "manifest": ".ai/task/sample-feature/backend/accept.md",
        "items": {
          "BE-A01": {"status": "pending", "file": ".ai/task/sample-feature/backend/accept/BE-A01-review.md", "agent": "backend-accept"}
        }
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

按执行结果补充：

- 失败时：`last_error`

`.state.json` 不记录时间类元数据。不要写入 `generated_at`、`created_at`、`updated_at`、`started_at` 或 `completed_at`；是否已规划、失败或完成只由 `status`、任务目录和 manifest/item 文件存在性表达。

## State Rules

- 校验 `phase` 时读取 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 的 Phases；只允许其中的 `supported_phases`，并按该节确定启用条件。
- `phases` / `tasks` 只要求包含当前任务的 `active_phases`，不得强制要求未启用的阶段。
- `status` 只允许 `pending | failed | completed | skipped | generated`。
  - `skipped`：阶段或已规划的 item 不适用于当前任务
  - `generated`：任务规划已生成，尚未开始执行

`tasks[phase]` 的必需 slot 与 test 启用条件按 task-phase-execution 的 Slot Order 校验。每个已规划 slot 都必须有 manifest 和至少一个 item；未规划的 test slot 不得出现在 `tasks[phase]` 或阶段目录中。

## Execution Entry Transition

`generated` 是规划完成态，`pending` 是执行队列态。`/t-run` 对目标 phase 完成状态文件、阶段目录、manifest/item 和执行顺序校验后，必须在选择首个 item 前执行一次启动归一化：

- 将 `tasks[phase][slot].items[*].status == generated` 的 item 全部改为 `pending`；只处理本次目标 phase。
- 保留 `pending | failed | completed | skipped` item 原状态，不得借启动归一化重置失败或已完成结果。
- item 归一化后，按下方聚合规则重新计算目标 phase 的全部 slot 状态和 phase 状态，并在启动任何 agent 前一次性写回 `.state.json`。
- 若写回失败，重试一次；仍失败则终止执行且不启动 agent。再次运行 `/t-run` 时从当前持久化状态重新归一化。
- 该迁移只表示任务进入执行队列，不表示 item 已开始执行，也不引入 `running` 状态。

`/t-task-check` 只校验状态，不执行该迁移。`/t-task` 新生成且尚未进入执行队列的 item 保持 `generated`。

阶段 `completed` 与业务交付的区别按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`；后续行为验证记录在现有 index/Handoff，不增加状态枚举。

## Evidence Invalidation

重新进入已执行阶段或交付收尾时，按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md` 核对相关证据：

- 证据仍有效时保留 completed，不重复运行；skipped 只复核不适用依据，不要求不存在的执行日志。
- 证据缺失或相关输入变化时，将持有失效验证的已完成 item、依赖其结果的已完成下游 item 及对应 accept item 置为 pending，并重新聚合 slot/phase；不重置无关 item 或尚未执行的 generated item。
- 验证由后续 Demo 承接时，同时标记验证表对应行为为未执行并重新打开已完成的承接验收；记录失效原因和恢复入口，不自动执行其他 phase。
- 若需要生产修复，由编排层重新打开对应 dev item；先持久化状态与 Handoff 再启动 agent。状态写入失败时停止，不以旧 completed 返回成功。

## Acceptance Result

`/t-run` 按 `${CLAUDE_PLUGIN_ROOT}/protocols/acceptance-contract.md` 校验返回与报告，仅有效通过结论将 accept item 写为 completed。有效拒绝保留 accept=failed、last_error 和 Handoff，按根因将对应 dev/test 及失效下游 item 重开为 pending，聚合后停止；同命令重入先修复、重测，再独立验收。仅缺环境/设备/用户裁决时，不重开无缺陷的 dev/test，记录解除条件后停止。无效输出记录失败，不代出结论。

accept 不可单独 skipped 绕过门禁；仅整个 phase 有不适用依据且全部 item skipped 时允许跳过。

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
