# Protocols 入口

| 你要确认的问题 | 对应协议 |
| --- | --- |
| 插件资源与目标项目运行时边界 | [runtime-boundaries.md](${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md) |
| PRD、用户故事和技术预研的正式/候选来源边界 | [requirement-source-contract.md](${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md) |
| 代码注释中临时工作流文档引用禁令与低价值注释定义 | [code-comment-contract.md](${CLAUDE_PLUGIN_ROOT}/protocols/code-comment-contract.md) |
| 产品立项决策简报结构、结论和下游承接规则 | [decision-brief-contract.md](${CLAUDE_PLUGIN_ROOT}/protocols/decision-brief-contract.md) |
| 跨阶段决策账本、用户决策暴露和消费追踪 | [decision-continuity-contract.md](${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md) |
| 实现类 agent 的通用结构化输出 | [agent-task-output-contract.md](${CLAUDE_PLUGIN_ROOT}/protocols/agent-task-output-contract.md) |
| 子 agent 调用前的角色规范注入 | [subagent-dispatch.md](${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md) |
| 修复后补测集合的字段与允许命令 | [tests-to-run-contract.md](${CLAUDE_PLUGIN_ROOT}/protocols/tests-to-run-contract.md) |
| `.ai/task/.../.state.json` 的唯一结构真相 | [task-state-contract.md](${CLAUDE_PLUGIN_ROOT}/protocols/task-state-contract.md) |
| phase/slot/item 的执行顺序与前置规则 | [task-phase-execution.md](${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md) |
| `.ai/super-run/...` 的目标级计划、状态、主会话执行与 Goal 闭环 | [super-run-state-contract.md](${CLAUDE_PLUGIN_ROOT}/protocols/super-run-state-contract.md) |
| backend-test 的默认收敛与升级策略 | [backend-test-execution.md](${CLAUDE_PLUGIN_ROOT}/protocols/backend-test-execution.md) |
| 设计检查评分标准 | [design-check-rubric.md](${CLAUDE_PLUGIN_ROOT}/protocols/design-check-rubric.md) |
| PRD / user story 检查评分标准 | [prd-check-rubric.md](${CLAUDE_PLUGIN_ROOT}/protocols/prd-check-rubric.md) |
| HTML Preview 通用契约 | [html-show-contract.md](${CLAUDE_PLUGIN_ROOT}/protocols/html-show-contract.md) |
| PRD HTML Preview PRD 专用契约 | [prd-preview-contract.md](${CLAUDE_PLUGIN_ROOT}/protocols/prd-preview-contract.md) |
| t-dream 候选问题、评分和报告契约 | [dream-report-contract.md](${CLAUDE_PLUGIN_ROOT}/protocols/dream-report-contract.md) |
| 任务检查评分与阻塞规则 | [task-check-rubric.md](${CLAUDE_PLUGIN_ROOT}/protocols/task-check-rubric.md) |
| Demo 共享 Result 输出结构 | [demo-result-contract.md](${CLAUDE_PLUGIN_ROOT}/protocols/demo-result-contract.md) |
| Demo 诊断报告结构与分类映射 | [diagnostic-report-contract.md](${CLAUDE_PLUGIN_ROOT}/protocols/diagnostic-report-contract.md) |
| Web Demo 单文件运行、修复、补测与环境刷新 | [web-demo-run-repair-contract.md](${CLAUDE_PLUGIN_ROOT}/protocols/web-demo-run-repair-contract.md) |
| Flutter Patrol Demo 单文件与批量修复 | [flutter-demo-run-repair-contract.md](${CLAUDE_PLUGIN_ROOT}/protocols/flutter-demo-run-repair-contract.md) |
| Figma 设计稿 → 已有前端代码的 UI 还原与测量收敛 | [figma-restore-contract.md](${CLAUDE_PLUGIN_ROOT}/protocols/figma-restore-contract.md) |

## 使用规则

- `protocols/` 只定义共享契约，不重复业务规范、工作流教程或项目事实。
- `skills/` 和 `agents/` 只描述何时使用这些协议，不再复制完整字段定义。
- 更新协议时，优先改这里指向的单一真相源，而不是在多个入口文档里同步抄写。
