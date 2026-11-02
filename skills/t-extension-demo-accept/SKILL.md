---
name: t-extension-demo-accept
description: 独立验收 Chrome 扩展真实加载后的 Playwright 用户故事演示并汇总报告；普通 Web 页面演示使用 t-web-demo-accept。
argument-hint: "[demo/e2e/extension/<file>.e2e.ts|all]"
allowed-tools: [Read, Glob, Grep, Bash, Write, Agent]
---

# Extension Demo 验收

文件参数只接受 `demo/e2e/extension/**/*.e2e.ts`；`all` 或留空只扫描此目录，排除 fixture/helper/template。先读 `${CLAUDE_PLUGIN_ROOT}/protocols/acceptance-contract.md` 和 `${CLAUDE_PLUGIN_ROOT}/protocols/extension-demo-acceptance-contract.md`，按专项契约排除 verification、处理显式初始化参数或无故事目标，不编造故事通过结论。

按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 读取并注入 `${CLAUDE_PLUGIN_ROOT}/agents/extension-demo-accept.md` 全文，逐文件串行派发独立 subagent。传入分端设计、真实故事/US ID、必要场景、构建产物、环境模式、run ID/日志与上游承接位置。agent 按专项协议核查实际加载产物、整文件执行和清理证据，入口不复制门禁或生成第二套命令。

按公共协议检查返回与报告。批量对有效拒绝继续处理后续文件并写汇总，合并问题及待验证项；派发失败/无效返回记验收未完成，批次不能通过。单文件保留 agent 原结论。中断先确认旧 agent 已结束再恢复，不修改源码或自动转入修复。
