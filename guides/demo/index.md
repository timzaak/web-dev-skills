# Demo 规范入口

Demo 规范入口，按“先确认测试基线，再按失败类型进入对应细页”使用。

| 你要确认的问题 | 对应规范 |
| --- | --- |
| Demo 测试整体基线、运行方式与核心约束 | [e2e-testing.md](/guides/demo/e2e-testing.md) |
| 选择器设计、命名和回退策略 | [selector-strategy.md](/guides/demo/selector-strategy.md) |
| Page Object 组织方式与适用边界 | [pom-guide.md](/guides/demo/pom-guide.md) |
| 测试维护入口，如何分流到修复细页 | [test-maintenance.md](/guides/demo/test-maintenance.md) |
| 常见失败模式与优先排查路径 | [common-failures.md](/guides/demo/common-failures.md) |
| 选择器失效时的修复办法 | [selector-repair.md](/guides/demo/selector-repair.md) |
| Page Object 或页面结构变化后的更新方式 | [pom-update.md](/guides/demo/pom-update.md) |
| 前端改动后的同步检查项 | [frontend-sync-checklist.md](/guides/demo/frontend-sync-checklist.md) |
| 失败诊断流程与证据优先级 | [diagnose-guide.md](/guides/demo/diagnose-guide.md) |
| 只读验收门禁、评分和拒绝条件 | [quality.md](/guides/demo/quality.md) |
| 前端联调调试辅助说明 | [demo-debugging.md](/guides/demo/demo-debugging.md) |

## 使用规则

- `e2e-testing.md` 是 Demo 测试基线入口；先看这里，再按失败类型进入细页。
- `test-maintenance.md` 负责分流到 `selector-repair.md`、`pom-update.md`、`common-failures.md`，不要在 agent 文档里复制这套路由。
- `diagnose-guide.md` 只描述诊断流程；诊断报告结构以 `protocols/diagnostic-report-v3-minimal.md` 为准。
- `quality.md` 只定义验收门禁和评分，不替代测试实现规范。
