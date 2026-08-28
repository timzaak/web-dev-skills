---
name: t-figma-ux
description: Implement motion and interaction for a reconstructed Figma UI, guided by prototype evidence and animation principles distilled for interfaces.
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

# Figma 动效交互

共享契约：`${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md`
原则基准：`${CLAUDE_PLUGIN_ROOT}/guides/figma/motion.md`

在已有整页实现上补充动效交互：提取原型证据、生成动效基准、实现并验收。不修复静态视觉偏差（那是 `t-figma-fix` 的职责），不下载素材，不重做结构。

## 前置

校验 URL 与 target-file；`figma-session.py resolve` 唯一 active session 且 fileKey/mainNodeId 与主稿一致，stage 至少 `implemented`。missing、mismatch 或 ambiguous 时分别提示先运行 assets/impl、回到主稿或询问选择。

读取 context.md 的项目动效模式、`docs/figma-rules.md`、当前 spec 与实现代码。优先从既有 `source/design-context.md` 提取 prototype reactions、transition、smart animate 证据；缺失时在同一 MCP 窗口重新提取并保存为 `source/motion-context.md`，不覆盖既有快照。页面完全无原型数据且无交互语义时停止，请开发者明确动效范围。

## 动效基准

1. 按 motion 指南的证据优先级生成 `motion.json`：原型数据 → 项目模式 → 原则默认（`origin: principle-default` 仅限不影响用户流程的微反馈）。
2. 首屏转场、跨页转场、破坏性操作反馈等影响用户流程感知的缺口用 AskUserQuestion 裁决，记录 `origin: user-decision`。
3. spring 动效缺项目动效库支撑时停止询问，不用 CSS 动画伪造。
4. 为每个 interaction 把 duration/easing/delay/property 数值探针追加进 `spec.json` 并增加 revision（scope=motion），easing 按 motion 指南记录 CSS computed 形式。

## 实现闭环

1. stage 设为 `motion`。
2. 按 subagent dispatch 契约注入并委派 `figma-ux`；agent 只实现 `motion.json` 声明的动效，复用项目动效模式并提供 reduced-motion 替代。
3. 启动或确认 context 声明的 dev server，注入并委派只读 `figma-accept` 测量动效探针。有阻塞 delta 且未到 5 轮时交回 ux；原型证据与实现分歧时先修订 `motion.json` 再修实现。
4. 收敛后 stage 设为 `accepted`，报告 `CONVERGED`；达 5 轮 stage 保持 `motion`，报告 `EXHAUSTED`。stagger、easing 词表等动效规则候选按 rules.md 晋升。

## 门禁

- duration/timing FAIL、动效探针 MISSING、reduced-motion 替代缺失均阻塞收敛。
- 未裁决的动效缺口不得用原则默认继续推进。
- 报告列出每个 interaction 的 origin、证据、reduced-motion 替代和需人工触发复核的 wiring 项。
