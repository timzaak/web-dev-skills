# Protocols 入口

共享协议入口，存放跨 skill 和 agent 复用的结构契约、状态模型和评分标准。

| 你要确认的问题 | 对应协议 |
| --- | --- |
| 插件资源与目标项目运行时边界 | [runtime-boundaries.md](/protocols/runtime-boundaries.md) |
| 实现类 agent 的通用结构化输出 | [agent-task-output-contract.md](/protocols/agent-task-output-contract.md) |
| 修复后补测集合的字段与允许命令 | [tests-to-run-contract.md](/protocols/tests-to-run-contract.md) |
| `.ai/task/.../.state.json` 的唯一结构真相 | [task-state-contract.md](/protocols/task-state-contract.md) |
| phase/slot/item 的执行顺序与前置规则 | [task-phase-execution.md](/protocols/task-phase-execution.md) |
| backend-test 的默认收敛与升级策略 | [backend-test-execution.md](/protocols/backend-test-execution.md) |
| 设计检查评分标准 | [design-check-rubric.md](/protocols/design-check-rubric.md) |
| PRD / user story 检查评分标准 | [prd-check-rubric.md](/protocols/prd-check-rubric.md) |
| 任务检查评分与阻塞规则 | [task-check-rubric.md](/protocols/task-check-rubric.md) |
| Demo 诊断报告结构与分类映射 | [diagnostic-report-v3-minimal.md](/protocols/diagnostic-report-v3-minimal.md) |

## 使用规则

- `protocols/` 只定义共享契约，不重复业务规范、工作流教程或项目事实。
- `skills/` 和 `agents/` 只描述何时使用这些协议，不再复制完整字段定义。
- 更新协议时，优先改这里指向的单一真相源，而不是在多个入口文档里同步抄写。
