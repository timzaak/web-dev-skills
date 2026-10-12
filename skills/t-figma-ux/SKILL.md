---
name: t-figma-ux
description: Standalone motion-refinement entry that polishes interaction and animation of an already-implemented UI, using Figma prototype evidence and animation principles distilled for interfaces.
argument-hint: "<figma-url> <target-file> <preview-url>"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Agent
  - Write
  - Bash
  - mcp__figma__get_metadata
  - mcp__figma__get_design_context
  - mcp__figma__get_screenshot
  - mcp__figma__get_variable_defs
---

# Figma 动效精修

对目标文件中已有实现（impl 产出或手写）精修动效交互；不修静态视觉偏差、不做结构实现、不下载素材。原则基准与 easing 映射见 `${CLAUDE_PLUGIN_ROOT}/guides/figma/motion.md`（生成动效候选前读），`motion.json` 结构见 `${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md`，agent 派发遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md`。

## 工作流

1. 校验 URL（整页或待精修节点）和 target-file；`<preview-url>` 可选，仅用于交付报告回显。URL 范围内没有已实现代码时停止。
2. 读取项目动效模式与范围内代码；需要原型证据时在 MCP 窗口内提取并在窗口内消费，结论记入 `motion.json` 的 `evidence` 字段。范围内无原型数据且无交互语义时停止，请开发者明确动效范围。
3. 按 motion 指南生成 `.ai/figma/<fileKey>-<nodeId>/motion.json`；影响用户流程感知的动效缺口先询问裁决，不得静默套用原则默认。
4. 委派 `figma-ux` agent 只实现 `motion.json` 声明的动效并提供 reduced-motion 替代；完成后报告 `motion.json` 路径与 preview URL（如有），动效触发、时长手感和 reduced-motion 效果由开发者打开页面人工验收。
