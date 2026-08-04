# Demo 规范入口

Demo 规范入口，按“先确认测试基线，再按失败类型进入对应细页”使用。

| 你要确认的问题 | 对应规范 |
| --- | --- |
| Demo 测试整体基线、运行方式与核心约束 | [e2e-testing.md](${CLAUDE_PLUGIN_ROOT}/guides/web-demo/e2e-testing.md) |
| 选择器设计、命名和回退策略 | [selector-strategy.md](${CLAUDE_PLUGIN_ROOT}/guides/web-demo/selector-strategy.md) |
| Page Object 组织方式与适用边界 | [pom-guide.md](${CLAUDE_PLUGIN_ROOT}/guides/web-demo/pom-guide.md) |
| 测试维护入口，如何分流到修复细页 | [test-maintenance.md](${CLAUDE_PLUGIN_ROOT}/guides/web-demo/test-maintenance.md) |
| 常见失败模式与优先排查路径 | [common-failures.md](${CLAUDE_PLUGIN_ROOT}/guides/web-demo/common-failures.md) |
| 选择器失效时的修复办法 | [selector-repair.md](${CLAUDE_PLUGIN_ROOT}/guides/web-demo/selector-repair.md) |
| Page Object 或页面结构变化后的更新方式 | [pom-update.md](${CLAUDE_PLUGIN_ROOT}/guides/web-demo/pom-update.md) |
| 前端改动后的同步检查项 | [frontend-sync-checklist.md](${CLAUDE_PLUGIN_ROOT}/guides/web-demo/frontend-sync-checklist.md) |
| 失败诊断流程与证据优先级 | [diagnose-guide.md](${CLAUDE_PLUGIN_ROOT}/guides/web-demo/diagnose-guide.md) |
| 只读验收门禁、评分和拒绝条件 | [quality.md](${CLAUDE_PLUGIN_ROOT}/guides/web-demo/quality.md) |
| 前端联调调试辅助说明 | [demo-debugging.md](${CLAUDE_PLUGIN_ROOT}/guides/web-demo/demo-debugging.md) |
| `/t-tools:t-web-demo-run-all` 批次 token 去向诊断与改造分流 | [batch-token-profiling.md](${CLAUDE_PLUGIN_ROOT}/guides/web-demo/batch-token-profiling.md) |

## 使用规则

- `e2e-testing.md` 是 Demo 测试基线入口；先看这里，再按失败类型进入细页。
- `test-maintenance.md` 负责分流到 `selector-repair.md`、`pom-update.md`、`common-failures.md`，不要在 agent 文档里复制这套路由。
- `diagnose-guide.md` 只描述诊断流程；诊断报告结构以 `${CLAUDE_PLUGIN_ROOT}/protocols/diagnostic-report-contract.md` 为准。
- `quality.md` 只定义验收门禁和评分，不替代测试实现规范。
