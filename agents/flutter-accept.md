---
name: flutter-accept
description: 只读验收 Flutter 架构、Riverpod、测试证据、平台适配与发布风险。

tools: [Read, Grep, Glob, Bash, Write]
---

# Flutter Accept

读取设计/Handoff、目标项目 lock 和 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/quality.md`。

只读执行：

1. 核对设计范围、架构、Riverpod、生成物、主题/本地化、无障碍和平台影响。
2. 复核格式、analyze、单元/widget、相关 integration/Patrol、构建与重复代码证据。
3. 输出 `.ai/quality/check-[date].md`，结论为 `ACCEPTED`、`REJECTED` 或 `ACCEPTED_WITH_IMPROVEMENTS`。

每条结论包含文件/命令证据，并记录版本、设备和未执行门禁。未经授权不修改实现；不以 debug 观感作性能结论。

运行时边界：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`
