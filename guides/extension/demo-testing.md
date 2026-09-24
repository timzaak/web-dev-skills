# Chrome 扩展用户故事演示

适用于 `extension-demo` 阶段的 Playwright 集成演示。`extension` 阶段负责 WXT 实现、Vitest 与技术验收；本阶段负责真实加载扩展后的完整用户路径及独立验收。普通 Web 页面故事仍归 `web-demo`。

## 输入和资产

- 从设计主文档及 `extension.md` 确认用户故事、扩展入口、宿主站点、权限、消息/存储、生命周期、后端依赖与环境模式。未规划用户故事演示时不启用本阶段。
- 测试资产置于目标项目 `demo/e2e/extension/`，按实际故事分组；fixture、helper 和用例由 `extension-demo-dev` 维护。任务或报告保留 draft 或 published 故事的真实来源路径，不把草稿写成已发布事实；代码注释遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/code-comment-contract.md`，不引用临时工作流路径。
- 每个用例覆盖可观察的完整路径：加载构建产物、触发 popup/options/content script/background 的实际交互、验证持久结果或明确错误态。按故事风险覆盖权限拒绝、消息失败、状态恢复等分支；不得用 Vitest mock 结果代替浏览器证据。
- 具体 Chromium fixture、独立 profile、扩展 ID、后台请求隔离与 worker 生命周期操作按 [扩展测试指南](${CLAUDE_PLUGIN_ROOT}/guides/extension/testing.md) 执行；复用 [Web Demo 日志和选择器规范](${CLAUDE_PLUGIN_ROOT}/guides/web-demo/index.md)。

## 执行和验收

- 从目标项目实际脚本确认构建命令及产物目录。扩展实现变化后先重新构建，再用新的 persistent context 运行；不能沿用旧加载产物。
- fixture 自行管理宿主/stub 时，对 `demo/e2e/extension/<file>.e2e.ts` 使用 `web-demo-test-runner.py --no-auto-env`；依赖真实后端时保留默认环境管理。首次、定向、整文件终验及恢复使用同一选择。
- 单文件诊断修复遵循 [Demo 运行修复契约](${CLAUDE_PLUGIN_ROOT}/protocols/web-demo-run-repair-contract.md)，其中扩展用例由 `extension-demo-diagnose` 诊断，测试/数据问题交 `extension-demo-dev`，扩展实现问题交 `extension-dev`。
- `extension-demo-accept` 只读验收故事映射、实际构建、浏览器执行日志、fixture 隔离、关键断言及必要清理；报告与结论遵循 [扩展 Demo 验收契约](${CLAUDE_PLUGIN_ROOT}/protocols/extension-demo-acceptance-contract.md)。
- 需要用户当前 Chrome 登录态或已安装扩展的现场证据时，额外按 [现场指南](${CLAUDE_PLUGIN_ROOT}/guides/extension/live-browser.md) 和 [扩展验收契约](${CLAUDE_PLUGIN_ROOT}/protocols/extension-acceptance-contract.md) 采集；独立 fixture 的通过结果不能替代必要现场证据。
