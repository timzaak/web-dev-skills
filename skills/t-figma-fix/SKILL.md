---
name: t-figma-fix
description: Independently refine one Figma UI region in an existing implementation, whether produced by t-figma-impl or written by hand, and distill validated project rules.
argument-hint: "<figma-node-url> <target-file> <preview-url> <问题、状态或断点描述>"
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

共享契约：`${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md`（附着/创建 session、写 assets-manifest 或晋升长期规则前读）
二次重建：`${CLAUDE_PLUGIN_ROOT}/guides/figma/reconstruction.md`（判断偏差属于分块理解或结构问题时读）
规则记忆：`${CLAUDE_PLUGIN_ROOT}/guides/figma/rules.md`（写候选或晋升长期规则前读）

独立精修节点 URL 指向的已有实现；可以附着 `t-figma-impl` 等既有 session，也可以为手写或其他方式产生的代码自行建立局部基准。文字描述用于补充 hover、移动端、异常状态或代码问题。不得借机重做整页。

## 前置

校验 node URL、target-file、非空描述和 `<preview-url>`（缺失时 `AskUserQuestion` 补齐一次，仍无则停止），并确认 URL 对应区域已有可运行的代码实现；没有实现时停止，说明应先实现该区域或运行 `t-figma-impl`，不得把局部 fix 扩成整页实现。

调用 `${CLAUDE_PLUGIN_ROOT}/scripts/figma-session.py resolve`，附着（同 fileKey，nodeId 可不同）、独立 `create --stage fixing`、不一致与 ambiguous 询问等决策按共享契约的 Session Resolve 表执行；附着时复用 session 中实际存在的 context、manifest 和 candidates，不要求这些产物必须来自 `t-figma-impl`。

读取项目约束、长期规则、目标区域代码和邻近复用实现。只对 fix 节点调用 screenshot 等 MCP 证据，保存为新的 `source/baseline-<node-name>.png`，不覆盖已有快照。

缺少 `context.md` 时从项目和目标区域代码生成。本次不引入资产且缺 manifest 时写空 `assets-manifest.json`；修复需要新增、替换或加工素材则停止，提示先运行 `t-figma-assets`，不得用空 manifest 绕过本次变更涉及的资产。

## 精修闭环

1. 将节点 baseline 截图与当前 DOM 区域对照，判断偏差属于分块理解、素材、响应式、样式值或现有组件使用问题。
2. 分块或数值理解有误时，先更新 `context.md` 对应记录再修实现。
3. 注入并委派 `figma-fix`，传入 scope selector、问题描述、节点 baseline 截图和目标代码范围，限制 change_scope 为目标区域及其直接共享样式；资产只能引用 manifest。发现新素材则停止，提示先运行 assets。
4. 用相同 scope 委派 `figma-accept` 做局部目视比对。最多 5 轮，只回改当前 scope 的阻塞问题。
5. 比较 Figma 表达、修复前代码和最终通过代码，写候选；收敛后按契约去重、改写、晋升长期规则。页面专属补丁和单次像素值不晋升。

输出修改范围、局部比对结论、验证证据、候选和已晋升规则。未收敛时不得更新长期规则。
