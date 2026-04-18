# Demo E2E 测试指南

用于 Demo 开发与功能验证的主入口。

## 适用范围

- 新增或修改 `demo/e2e/**/*.e2e.ts`
- 修复 Demo 测试代码问题
- 运行单文件或最小回归验证

## 核心规则

1. 完整用户故事主路径优先用 Demo / E2E 覆盖。
2. 业务数据优先通过 UI 创建或通过 Demo seed 预置，不在测试文件里走业务旁路。
3. 当前默认使用单租户固定路径，如 `/auth/login`、`/manage`、`/manage/users`。
4. 选择器优先 `data-testid`、语义 role、稳定文本，不依赖脆弱 CSS。
5. 运行和清理优先使用项目脚本与统一 fixture。

## 当前目录事实

```text
demo/e2e/
├── fixtures/
├── helpers/
├── pages/
├── selectors.ts
└── *.e2e.ts
```

角色目录和文件组织以当前 `demo/e2e/` 实际结构为准，不再把旧项目目录命名当默认模板。

## 标准命令

```powershell
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-test-runner.py demo/e2e/[test-file].ts
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-run-all.py
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/debug-test.py demo/e2e/[test-file].ts
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-stop.py
```

## 自检

- [ ] 测试覆盖真实用户路径
- [ ] 未使用旧的租户前缀路由示例
- [ ] 选择器可维护
- [ ] 已完成最小验证运行

## 参考

- POM：[`pom-guide.md`](${CLAUDE_PLUGIN_ROOT}/guides/demo/pom-guide.md)
- 选择器策略：[`selector-strategy.md`](${CLAUDE_PLUGIN_ROOT}/guides/demo/selector-strategy.md)
- 维护指南：[`test-maintenance.md`](${CLAUDE_PLUGIN_ROOT}/guides/demo/test-maintenance.md)
- 调试指南：[`diagnose-guide.md`](${CLAUDE_PLUGIN_ROOT}/guides/demo/diagnose-guide.md)
