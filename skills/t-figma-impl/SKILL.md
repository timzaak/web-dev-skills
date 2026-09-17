---
name: t-figma-impl
description: Reconstruct and implement a complete Figma UI in an existing frontend file, block by block, using prepared assets and visual acceptance.
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

# Figma 整页实现

运行时边界：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`（判断产物写入位置或项目事实与插件默认冲突时读）
共享契约：`${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md`（校验 session、分块、写 context 或晋升长期规则前读）
二次重建：`${CLAUDE_PLUGIN_ROOT}/guides/figma/reconstruction.md`（分块或修订结构理解前读）

负责完整 UI 稿的结构重建、代码实现和有界目视验收；不重新承担素材下载和转换。

## 前置和上下文

校验 URL 与 target-file，通过 `${CLAUDE_PLUGIN_ROOT}/scripts/figma-session.py resolve` 找 active session，并按共享契约的 Session Resolve 表执行。impl 只复用 fileKey/mainNodeId 与主稿 URL 一致且 assets 阶段已完成的 session；missing 或 mismatch 时停止并提示先运行 `t-figma-assets` 或回到匹配主稿，不得自行归档或创建 session。`assets-manifest.json` 不存在则停止；空数组合法。

读取项目约束、目标文件及邻近模块、现有 token/组件/动效/响应式模式、`docs/figma-rules.md`、session candidates 和 assets manifest，生成固定章节的 `context.md`。栈或资产引用方式无法确定时停止询问。`<preview-url>` 缺失时 `AskUserQuestion` 补齐一次，仍无则停止。

## 二次重建与分块

1. 在 MCP 窗口内保存主节点 metadata、design context、variables 和 baseline 到 session `source/`（一次写入，后续不覆盖）。
2. 按 reconstruction 指南执行：baseline 截图定结构（视觉块、stacking、裁切、绝对定位、合成素材），节点树只补精确数值，不照搬 frame/group 层次。
3. 把页面划分为可独立实现的视觉块（按文档顺序），在 MCP 窗口内为每块保存 `source/baseline-<block>.png`；块清单（名称、baseline、使用资产、组件映射）与主稿 viewport 写入 `context.md`。

## 逐块实现与整页验收

4. 按块清单顺序逐块委派 `figma-impl`：每次 dispatch 只承担一个块或少量相邻小块，给出该块的 baseline、资产和组件映射；agent 完成该块并执行目标栈验证。块失败先重试该块，不带病推进；中断后从 `context.md` 块清单的未完成块恢复。
5. 全部块完成后注入并委派只读 `figma-accept` 做整页目视比对。有阻塞问题且未到 5 轮时，把问题按所在块归组交回 impl；若视觉证据证明分块理解错误，先更新 `context.md` 再修实现。
6. 收敛后晋升符合契约的规则候选，合并改写 `docs/figma-rules.md`，最多 10 条；否则候选留在 session。

## 结束状态

- 验收通过：stage=`accepted`，报告 `PASS`。
- 达 5 轮：stage 保持 `implemented`，报告 `EXHAUSTED`。
- 栈验证失败：不进入 accept，不宣称完成。
