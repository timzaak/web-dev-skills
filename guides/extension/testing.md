# Chrome 扩展测试指南

真实浏览器/场景验证优先覆盖扩展加载、跨上下文通信和用户路径；仅在这些路径难稳定覆盖重要业务规则或异常边界时新增 Vitest，并说明可观察回归及覆盖缺口。允许不新增局部测试，受影响的现有测试仍需定向验证。先确认项目现有 scripts、fixtures 与依赖版本，再选择受影响范围。

需要用户当前标签页、登录态或已安装扩展的现场验证时，先读 [用户 Chrome 调试](${CLAUDE_PLUGIN_ROOT}/guides/extension/live-browser.md)，采用 Chrome DevTools MCP；本页的临时 profile 负责独立回归，两种证据不得互相冒充。extension-test 仍负责 Vitest，现场采集由开发角色或主会话完成。

## Vitest

- WXT 内置 `WxtVitest`，从 `wxt/testing/vitest-plugin` 导入；它接入 WXT Vite 配置、别名和 browser 的 fakeBrowser 实现，无需另找 `wxt-vitest` 包。
- 使用 `wxt/testing/fake-browser` 的 fakeBrowser，beforeEach 调 reset；统一使用 WXT browser 导入。直接调用 chrome 的封装需项目共享 helper，不假设 browser mock 会覆盖所有 chrome API。
- 测消息 handler 的业务分支、接收端非法输入与权限拒绝、项目存储迁移、错误处理、hooks 和有状态 UI。不要重复验证库自身的 fallback/watch 或静态渲染事实。
- fakeBrowser 不模拟浏览器进程、真实权限或 worker 生命周期；单测可验证状态恢复函数，实际挂起/重启由浏览器测试提供证据。
- React 组件用 Testing Library / userEvent；shadow UI 使用共享 render helper，将查询限定在 shadow root，覆盖卸载清理。
- 需要后端请求隔离时用 MSW 的 Node 测试环境，覆盖 UI 和 handler 调用的客户端；“无需后端”只适用于该隔离测试。通用原则按 [frontend testing](${CLAUDE_PLUGIN_ROOT}/guides/frontend/testing.md) 读取。

配置或 API 不确定时查 [WXT Unit Testing](https://wxt.dev/guide/essentials/unit-testing.html)。

## Playwright 扩展 fixture

由 extension-demo-dev 维护 `demo/e2e/extension/` 中的扩展专用 fixture 和用例；先读 [扩展演示指南](${CLAUDE_PLUGIN_ROOT}/guides/extension/demo-testing.md)，再复用 [Web Demo 规范](${CLAUDE_PLUGIN_ROOT}/guides/web-demo/index.md) 的日志、选择器与报告约定。

- 用 Playwright 自带 Chromium：`chromium.launchPersistentContext('', { channel: 'chromium', args: [...] })`，args 包含 `--disable-extensions-except=<构建绝对路径>`、`--load-extension=<同一路径>`。支持 headless；不要换成品牌 Chrome/Edge 后假设侧载参数仍可用。
- 测试前 build；fixture 确认 manifest 存在，每个测试使用独立临时 profile，结束时关闭 context。宿主页面从项目 fixture 启动的本地站点或明确测试站点加载，不依赖个人浏览器配置。
- 先取 `context.serviceWorkers()`，为空再等待 serviceworker 事件；存在 background 时从其 URL 推导扩展 ID。无 background 的扩展应提供不依赖 worker 的 ID 获取方式，不强加生产后台入口。
- popup/options 可通过 `chrome-extension://<id>/<实际页面>` 验证页面行为，但这不证明工具栏弹窗关闭等真实生命周期。需求涉及 popup 关闭或 worker 重建时，单独验证状态恢复。
- 当前 Playwright 在 worker 重启后保持 Worker handle；重启窗口的新 evaluate 等待恢复，挂起瞬间在执行的 evaluate 可能抛 `Service worker restarted`。以项目锁定版本文档为准，给等待设置超时，不对非幂等操作盲重试。
- 不假设页面 route/MSW 能拦截扩展后台请求。涉及 background fetch 时使用 fixture 管理的本地 HTTP stub 或设计指定测试后端，验证请求确实到达并在结束时清理。
- 构建缺失、权限拒绝、消息失败不得 skip 成功；覆盖本次实际受影响路径，不要求每次全量浏览器回归。

加载和生命周期行为查 [Playwright Chrome Extensions](https://playwright.dev/docs/chrome-extensions)。

## Demo 执行与恢复

扩展独立测试在 fixture 管理宿主/stub 和 profile 的前提下，通过现有 runner 的 `--no-auto-env` 运行，避免启动默认 Web 后端/frontend。例如：

```bash
uv run scripts/web-demo-test-runner.py demo/e2e/extension/settings.e2e.ts --no-auto-env --run-id <唯一ID>
```

混合项目依赖真实 Web 后端时按设计保留默认环境管理；不要仅因有扩展目录就跳过环境。是否使用 `--no-auto-env` 写入任务 Validation，定向、整文件终验和批次恢复均保留该选择。

修复闭环与隔离按 [Demo repair contract](${CLAUDE_PLUGIN_ROOT}/protocols/web-demo-run-repair-contract.md)；extension-demo 的测试编写/定向执行合并或拆分由 [task phase contract](${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md) 决定。
