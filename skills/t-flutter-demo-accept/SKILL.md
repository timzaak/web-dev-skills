---
name: t-flutter-demo-accept
description: Independently accept Android Patrol demos against user stories and execution evidence; use after Flutter demo development.
argument-hint: "<file|domain|all> [--device <android-id>]"
allowed-tools: [Read, Glob, Grep, Bash, Write, Agent]
---

# Flutter Demo 验收

按文件/domain/`all` 解析 `patrol_test/**/*_test.dart`，保留用户指定的 Android device；没有匹配文件时报告无可验收目标，不返回通过。

1. 读取 `${CLAUDE_PLUGIN_ROOT}/protocols/acceptance-contract.md`；故事来源与稳定 US ID 按 `${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md` 的 Story Traceability 解析，发布前允许真实 draft。
2. 按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 读取并注入 `${CLAUDE_PLUGIN_ROOT}/agents/flutter-demo-accept.md`，逐文件串行派发独立 subagent，传入设计、故事/必要场景、device、原始证据及上游承接位置。
3. agent 按领域规范核查整文件 Android 执行和技术门禁；有效证据可复用，缺失/失效时才补验。必要设备未确定且无法取得证据时交回调用方，不擅自换设备或把未验证当通过。
4. 按公共协议核查返回与报告。有效拒绝继续批量其他文件，派发失败/无效返回记验收未完成；批量写汇总并合并待验证项，不能遗漏失败。单文件返回原结论。中断先确认旧 agent 已结束再核对证据恢复。

本入口只编排验收和汇总，不修复测试或业务源码，不推进任务状态。

