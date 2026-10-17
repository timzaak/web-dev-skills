---
name: t-extension-demo-run
description: 运行单个 Chrome 扩展 Playwright 用户故事演示，诊断并修复真实加载后的集成失败；普通 Web 页面演示使用 t-web-demo-run。
argument-hint: "demo/e2e/extension/<scenario>.e2e.ts"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Agent
  - Task
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
---

# Extension Demo 单文件运行

校验参数为已存在的 `demo/e2e/extension/**/*.e2e.ts` 单文件，并读取 `${CLAUDE_PLUGIN_ROOT}/guides/extension/demo-testing.md`。按 `${CLAUDE_PLUGIN_ROOT}/protocols/web-demo-run-repair-contract.md` 的单文件执行、六轮上限、run ID、环境与结果字段执行；诊断角色固定为 `extension-demo-diagnose`，测试/数据修复角色为 `extension-demo-dev`。调度时遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md`。

首次整文件运行前确认项目实际构建及本次产物；只有 fixture 自行管理宿主/stub/profile 时传 `--no-auto-env`，所有定向及终验沿用相同模式。扩展实现修复后重新构建并创建新 context。以 Task 记录当前用例和轮次；中断时从首个 pending/failed 继续，不能把旧 run 当作新验证。

最后一行只输出共享契约 `${CLAUDE_PLUGIN_ROOT}/protocols/demo-result-contract.md` 定义的 `Result: {...}`；失败时保留最后日志和恢复动作。
