# Extension Acceptance Contract

供 extension-dev、extension-test、extension-accept 及任务编排消费。领域证据见 [quality guide](${CLAUDE_PLUGIN_ROOT}/guides/extension/quality.md)。

## 输入与报告

输入：feature、变更范围、设计或适用的豁免依据、上游验证证据。
报告写入 `.ai/quality/extension-accept-[feature]-[YYYYMMDD-HHMMSS].md`，至少包含结论、门禁结果、manifest/权限差异、带文件或命令来源的问题、必要后续动作。

结构化返回遵循 [agent output](${CLAUDE_PLUGIN_ROOT}/protocols/agent-task-output-contract.md)，补充 `acceptance_result` 和 `report_path`。`change_scope` 表示实际改动，不能把只读检查对象当作改动。

## 判定

- `REJECTED`：必要门禁失败/未完成，设计或验收目标未满足，或存在影响功能正确性、权限边界、凭据保护、CSP 的未解决缺陷；`task_completion.status=failed`。
- `ACCEPTED_WITH_IMPROVEMENTS`：必要门禁全部通过，仅有不影响验收目标和安全边界的维护性改进；`task_completion.status=success`。
- `ACCEPTED`：必要门禁通过且无未解决问题；`task_completion.status=success`。

问题可标 P0（无法继续/核心功能阻塞）、P1（功能或安全边界受损）、P2（维护性改进）；P0/P1 均阻断，不用“带改进通过”豁免。无法执行的必要检查标记未验证，不能计为通过；不适用项写明原因。

## 恢复与重复执行

验收只读检查源码；允许生成构建输出和报告。失败交回编排层，由 extension-dev 或 extension-test 修复后重跑相关检查及验收。每次验收写新报告并引用本次证据；旧报告保留，不把旧成功覆盖到本次未验证项。任务状态迁移沿用 [task state](${CLAUDE_PLUGIN_ROOT}/protocols/task-state-contract.md)。
