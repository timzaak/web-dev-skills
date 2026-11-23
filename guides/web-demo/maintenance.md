# Demo 测试维护与修复指南

用于定位并最小化修复 Demo 失败与前端同步问题。先运行目标测试拿到第一条失败信息，再按问题类型处理：

```bash
uv run scripts/web-demo-test-runner.py demo/e2e/<测试文件>.e2e.ts --log-level verbose
```

## 1. 问题分流

- `401/403`、角色不匹配：先检查登录和权限上下文，再决定是否转后端。
- `404/500`、`ECONNREFUSED`：按日志链路判断后端或环境问题，不在测试维护中硬修。
- 无明显服务错误但断言失败：按下方分类排查选择器、Page Object、等待与数据隔离。
- 每次只做最小修复，不要同时改等待、选择器、业务断言三类逻辑。

维护目标：小改动（选择器或文案级修复）5 分钟内完成，中等改动（Page Object 或表单流同步）15 分钟内完成；大改动拆分为前端变更、Demo 修复、回归验证三个明确步骤。

## 2. 选择器修复

适用：`selector not found`、`timeout waiting for selector`、前端重构后 `demo/e2e/selectors.ts` 与实际页面不一致。

修复步骤：

1. 先检查 `demo/e2e/selectors.ts` 中的共享选择器定义。
2. 对照 `frontend/src/**` 对应页面或组件的 `data-testid`、文本或语义 role（优先级：`data-testid` / 语义 role & label / 稳定文本 / 表单属性）。
3. 仅修改一层抽象：共享选择器失效优先改 `selectors.ts`；只有当前页面特殊才在 Page Object 层补局部适配。
4. 用最小相关测试回归：

```bash
uv run scripts/web-demo-test-runner.py demo/e2e/<测试文件>.e2e.ts --mode fast
```

禁止：在测试文件里直接硬编码新 CSS 选择器绕过 `selectors.ts`、用长链式 CSS 或布局类名作为主选择器、同时改选择器/等待/业务断言。

## 3. Page Object 更新

适用：页面结构变化、路由跳转变化、表单字段/按钮/对话框行为变化、测试文件开始堆积重复页面操作。

处理顺序：

1. 定位受影响的 Page Object（`demo/e2e/pages/`），校准对应页面的共享选择器，不发明第二套选择器。
2. 保持职责边界：导航（`goto()` 反映目标项目当前实际路由）与可交互等待（`waitForReady()`）留在 Page Object；表单填写方法只封装输入动作，不吞掉关键断言；业务断言留在测试文件。
3. 已有共享 helper 优先复用，不再复制流程。
4. 完成判定：测试文件重复 UI 操作减少、Page Object 未新增无关业务判断、相关测试在 `--mode fast` 下通过。

## 4. 常见稳定性问题

先确认是测试稳定性问题，不是服务异常：

- **strict mode violation**：缩小选择器范围；使用更精确的 role、文本或 `data-testid`；仅在语义明确时才用 `first()` / `nth()`。
- **元素不可交互**：确认元素可见且未被遮挡；需要时使用 `scrollIntoViewIfNeeded()`；`force: true` 仅作最后手段。
- **测试超时**：优先补业务断言或显式等待条件，不先加大超时掩盖竞态；确为慢请求再调整局部超时。
- **CI-only failure**：检查数据隔离和时间戳命名；检查是否依赖本地状态、动画或浏览器节奏；确认主断言未把 `sonner`、toast、Snackbar 等自动消失提示当作主判断条件，改为断言持久业务结果。

完成判定：修复后的等待条件可解释、未新增固定 sleep、主验收断言不依赖自动消失提示、本地通过后再进完整命令链路。

## 5. 前端改动同步清单

适用：修改 `data-testid`、调整页面结构/导航路径/表单字段、新增页面。

- **改动前**：确认已有对应 Demo 用例或 Page Object、通用交互模式复用位置，标记可能受影响的 `demo/e2e/**/*.e2e.ts`。
- **改动时**：`data-testid` 变更同步更新 `demo/e2e/selectors.ts`；页面结构变化同步检查 `demo/e2e/pages/*.ts`；路由变化同步检查登录页、相关 `goto()` 与测试中的 `waitForURL`。
- **改动后**：跑最小相关 Demo 测试；涉及通用导航、登录或会话逻辑变更时再补一条跨页面回归；将修复限制在最小影响面，不顺手重写整套 Demo。
