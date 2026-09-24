---
name: t-extension-demo-accept
description: 验收 Chrome 扩展真实加载后的 Playwright 用户故事演示并写只读报告；普通 Web 页面演示使用 t-web-demo-accept。
argument-hint: "[demo/e2e/extension/<file>.e2e.ts|all]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Write
---

# Extension Demo 验收

文件参数只接受 `demo/e2e/extension/**/*.e2e.ts`；`all` 或留空只扫描此目录，排除 fixture/helper/template。先读 `${CLAUDE_PLUGIN_ROOT}/protocols/extension-demo-acceptance-contract.md`、`${CLAUDE_PLUGIN_ROOT}/guides/extension/demo-testing.md` 和 `${CLAUDE_PLUGIN_ROOT}/agents/extension-demo-accept.md`。

逐文件核对用户故事、实际构建产物和 manifest、fixture/环境模式、整文件 Playwright 执行与清理证据；必要时执行当前项目真实 build 和 `web-demo-test-runner.py`，使用唯一 run ID。根据验收契约写单文件报告；批量时继续处理后续文件并写汇总报告。任一必要门禁失败或未验证，该文件 `REJECTED`。不修改测试或业务源码。
