---
name: t-figma-impl
description: Reconstruct and implement a complete Figma UI in an existing frontend file, using prepared assets and measurable acceptance.
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

# Figma 整页实现

运行时边界：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`（判断产物写入位置或项目事实与插件默认冲突时读）
共享契约：`${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md`（写 context/spec、判读 delta 分级或晋升长期规则前读）
二次重建：`${CLAUDE_PLUGIN_ROOT}/guides/figma/reconstruction.md`（写 spec revision 1 或修订 MCP 结构前读）
验收方法：`${CLAUDE_PLUGIN_ROOT}/guides/figma/measurement.md`（生成探针、委派 accept 或判读 delta 报告前读）

负责完整 UI 稿的结构重建、代码实现和有界验收；不重新承担素材下载和转换。

## 前置和上下文

校验 URL 与 target-file，通过 `${CLAUDE_PLUGIN_ROOT}/scripts/figma-session.py resolve` 找 active session，并按共享契约的 Session Resolve 表执行。impl 只复用 fileKey/mainNodeId 与主稿 URL 一致且 assets 阶段已完成的 session；missing 或 mismatch 时停止并提示先运行 `t-figma-assets` 或回到匹配主稿，不得自行归档或创建 session。`assets-manifest.json` 不存在则停止；空数组合法。

读取项目约束、目标文件及邻近模块、现有 token/组件/动效/响应式模式、`docs/figma-rules.md`、session candidates 和 assets manifest，生成固定章节的 `context.md`。栈、dev server、Playwright 目录或资产引用方式无法确定时停止询问。

## 二次重建与实现

1. 对照 source metadata、design context、baseline screenshot 和已有代码识别视觉块、stacking、裁切、绝对定位、合成素材及 viewport。
2. 写可修正 `spec.json` revision 1；MCP 结构不准确的修正必须带 reason/evidence。每个可测语义元素生成唯一 `data-figma` probe。
3. 按 subagent dispatch 契约注入并委派 `figma-impl`。agent 只引用 manifest，复用 context 的组件/token/动效，并执行目标栈验证。
4. 启动或确认 context 声明的 dev server，注入并委派只读 `figma-accept`。有阻塞 delta 且未到 5 轮时，把结构化失败交回 impl；若视觉证据证明 spec 分组错误，先增加 revision 再修实现。
5. 收敛后晋升符合契约的规则候选，合并改写 `docs/figma-rules.md`，最多 10 条；否则候选留在 session。

## 结束状态

- 全部门禁通过：stage=`accepted`，报告 `CONVERGED`。
- 达 5 轮：stage 保持 `implemented`，报告 `EXHAUSTED`。
- 验证或必要探测失败：不进入 accept，不宣称完成。
