# 选择器修复

适用场景：

- `selector not found`
- `timeout waiting for selector`
- 前端重构后 `demo/e2e/selectors.ts` 与实际页面不一致

## 修复步骤

1. 先打开 `demo/e2e/selectors.ts` 确认共享选择器定义。
2. 再对照 `frontend/src/**` 中对应页面或组件的 `data-testid`、文本或 role。
3. 仅修改一层抽象：
   - 共享选择器失效，优先改 `selectors.ts`
   - 只有当前页面特殊，才在 Page Object 层补局部适配
4. 用最小相关测试回归。

## 优先级

1. `data-testid`
2. 语义化 role / label
3. 稳定文本
4. 表单属性

## 当前典型位置

- 登录页：`/auth/login`
- 管理后台：`/manage/*`

## 不要这样修

- 不要在测试文件里直接硬编码新的 CSS 选择器绕过 `selectors.ts`
- 不要同时改选择器、等待逻辑和业务断言
- 不要用长链式 CSS 或布局类名作为主选择器

## 验证命令

```powershell
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/debug-test.py demo/e2e/[测试文件].ts
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-test-runner.py demo/e2e/[测试文件].ts --mode fast
```
