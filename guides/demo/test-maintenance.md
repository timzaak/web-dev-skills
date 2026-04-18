# 演示测试维护指南

> 本文档是 Demo 维护入口，不再承载所有案例细节。默认先按问题类型跳到对应 recipe，避免在一页内混读规则、案例和命令。

## 使用方式

1. 先运行目标测试，拿到第一条失败信息。
2. 根据问题类型进入对应 recipe。

```powershell
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-test-runner.py demo/e2e/[测试文件].ts --log-level verbose
```

## 维护入口

| 场景 | 进入文档 | 适用问题 |
| --- | --- | --- |
| 选择器失效或元素找不到 | `${CLAUDE_PLUGIN_ROOT}/guides/demo/selector-repair.md` | `selector not found`、`timeout waiting for selector` |
| 页面结构变化、需要更新 Page Object | `${CLAUDE_PLUGIN_ROOT}/guides/demo/pom-update.md` | UI 改版、路由变化、表单结构变化 |
| 超时、strict mode、元素不可交互、CI-only failure | `${CLAUDE_PLUGIN_ROOT}/guides/demo/common-failures.md` | 常见稳定性问题 |
| 前端改动前后的同步检查 | `${CLAUDE_PLUGIN_ROOT}/guides/demo/frontend-sync-checklist.md` | `data-testid`、页面结构、字段变更 |

## 分流规则

- `401/403`、角色不匹配：先检查登录和权限上下文，再决定是否转后端。
- `404/500`、`ECONNREFUSED`：优先按日志链路判断后端或环境问题，不在维护 recipe 中硬修。
- 无明显服务错误但断言失败：优先排查选择器、等待和数据隔离。

## 维护目标

- 小改动：5 分钟内完成选择器或文案级修复
- 中等改动：15 分钟内完成 Page Object 或表单流同步
- 大改动：拆分为前端变更、Demo 修复、回归验证三个明确步骤
