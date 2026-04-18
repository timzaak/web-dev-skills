# 前端改动同步清单

适用场景：

- 修改 `data-testid`
- 调整页面结构、导航路径或表单字段
- 新增管理页、认证页或用户中心页

## 改动前

- 确认是否已有对应 Demo 用例或 Page Object
- 确认是否复用了 `frontend/src/components/shared/` 中的通用交互模式
- 标记可能受影响的 `demo/e2e/*.ts`

## 改动时

- `data-testid` 变更后同步更新 `demo/e2e/selectors.ts`
- 页面结构变化后同步检查 `demo/e2e/pages/*.ts`
- 路由变化后同步检查：
  - `LoginPage`
  - 相关 `goto()` 方法
  - 相关测试中的 `waitForURL`

## 改动后

- 跑最小相关 Demo 测试
- 若是通用导航、登录或会话逻辑变更，再补一条跨页面回归
- 将修复限制在最小影响面，不顺手重写整套 Demo

## 推荐命令

```powershell
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-test-runner.py demo/e2e/[相关测试].ts --mode fast
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-test-runner.py demo/e2e/[相关测试].ts --log-level verbose
```
