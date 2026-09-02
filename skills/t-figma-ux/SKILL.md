---
name: t-figma-ux
description: Standalone motion-refinement entry that polishes interaction and animation of an already-implemented UI, using Figma prototype evidence and animation principles distilled for interfaces.
argument-hint: "<figma-url> <target-file>"
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

共享契约：`${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md`
原则基准：`${CLAUDE_PLUGIN_ROOT}/guides/figma/motion.md`

独立动效精修入口：对目标文件中已有实现（impl 产出或手写）提取原型证据、生成动效基准并实现验收。不修复静态视觉偏差（`t-figma-fix` 职责），不做结构实现，不下载素材。

## 前置

校验 URL（整页或待精修节点）与 target-file；URL 范围内没有已实现代码时停止。`figma-session.py resolve` 命中同 fileKey 的 active session 时附着（nodeId 可不同），missing 时以 `create --stage motion` 独立创建并生成 context，ambiguous 或 fileKey 不一致时询问。

读取项目动效模式、长期规则和 URL 范围内代码；原型证据按契约取自既有快照或新存 `source/motion-context.md`。范围内无原型数据且无交互语义时停止，请开发者明确动效范围。

## 工作流

1. 按 motion 指南的证据优先级生成 `motion.json` 和动效探针；影响用户流程感知的缺口先 AskUserQuestion 裁决，不得静默套用原则默认。
2. 按 subagent dispatch 契约注入并委派 `figma-ux`，只实现 `motion.json` 声明的动效并提供 reduced-motion 替代。
3. 启动或确认 dev server 后委派只读 `figma-accept` 测量动效探针；reduced-motion 替代缺失同样阻塞收敛。阻塞 delta 未到 5 轮交回 ux，原型证据与实现分歧时先修订 `motion.json` 再修实现。
4. 收敛后 stage 设为 `accepted` 并按 rules.md 晋升动效规则候选；达 5 轮报告 `EXHAUSTED`。
