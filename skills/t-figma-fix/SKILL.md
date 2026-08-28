---
name: t-figma-fix
description: Precisely refine one Figma UI region in an existing implementation and distill validated project rules.
argument-hint: "<figma-node-url> <target-file> <问题、状态或断点描述>"
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

# Figma 局部精修

共享契约：`${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md`
二次重建：`${CLAUDE_PLUGIN_ROOT}/guides/figma/reconstruction.md`
规则记忆：`${CLAUDE_PLUGIN_ROOT}/guides/figma/rules.md`

只精修节点 URL 指向的页面区域；文字描述用于补充 hover、移动端、异常状态或代码问题。不得借机重做整页。

## 前置

校验 node URL、target-file 和非空描述。调用 `${CLAUDE_PLUGIN_ROOT}/scripts/figma-session.py resolve`；missing 时提示先运行 assets/impl，ambiguous 时询问选择；node URL 的 fileKey 必须与所选 session 一致，但 nodeId 可以不同。要求 session 至少有 spec、context、manifest 和实现历史。

读取项目约束、长期规则、当前 candidates、spec revisions、历史 delta、目标区域代码和邻近复用实现。只对 fix 节点调用 metadata/design context/screenshot/variables，保存为新的 source 证据，不覆盖主稿快照。

## 精修闭环

1. 将节点 screenshot 与当前 DOM 区域对照，判断偏差属于 spec 分组、素材、响应式、样式值或现有组件使用问题。
2. 若 MCP 平面结构不准确，先更新 spec 对应 scope、增加 revision 并记录代码/截图/metadata 证据。
3. 注入并委派 `figma-fix`，限制 change_scope 为目标区域及其直接共享样式；资产只能引用 manifest。发现新素材则停止，提示先运行 assets，不在 fix 内下载或转码。
4. 用 `scopeSelector` 运行 `figma-accept` 的局部截图、数值 probes、资产/视频检查，并把本次节点的 `source/baseline-<node-name>.png` 显式作为 `--baseline`。最多 5 轮，只回改当前 scope 的阻塞项。
5. 比较 Figma 表达、修复前代码和最终通过代码，写候选；收敛后按契约去重、改写、晋升长期规则。页面专属补丁和单次像素值不晋升。

输出修改范围、spec revision、局部 delta、验证证据、候选和已晋升规则。未收敛时不得更新长期规则。
