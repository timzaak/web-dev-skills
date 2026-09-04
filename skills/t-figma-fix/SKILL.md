---
name: t-figma-fix
description: Independently refine one Figma UI region in an existing implementation, whether produced by t-figma-impl or written by hand, and distill validated project rules.
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

共享契约：`${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md`（生成或修订 spec、写 assets-manifest、判读 delta 分级或晋升长期规则前读）
二次重建：`${CLAUDE_PLUGIN_ROOT}/guides/figma/reconstruction.md`（判断偏差是否属于 spec 分组问题或修订二次规格前读）
规则记忆：`${CLAUDE_PLUGIN_ROOT}/guides/figma/rules.md`（写候选或晋升长期规则前读）

独立精修节点 URL 指向的已有实现；可以附着 `t-figma-impl` 等既有 session，也可以为手写或其他方式产生的代码自行建立局部基准。文字描述用于补充 hover、移动端、异常状态或代码问题。不得借机重做整页。

## 前置

校验 node URL、target-file 和非空描述，并确认 URL 对应区域已有可运行的代码实现；没有实现时停止，说明应先实现该区域或运行 `t-figma-impl`，不得把局部 fix 扩成整页实现。

调用 `${CLAUDE_PLUGIN_ROOT}/scripts/figma-session.py resolve`：

- 唯一 active session 的 fileKey 一致时附着，nodeId 可以不同；复用其中实际存在的 context、spec、manifest、candidates 和历史 delta，不要求这些产物必须来自 `t-figma-impl`。
- missing 时以 node URL 调用 `create --stage fixing` 建立独立 session。
- ambiguous 时询问选择；唯一 session 的 fileKey 不一致时，询问开发者回到匹配设计，或归档旧 session 后创建新的 fixing session，不得擅自复用或归档。

读取项目约束、长期规则、目标区域代码、邻近复用实现，以及 session 中实际存在的 candidates、spec revisions 和历史 delta。只对 fix 节点调用 metadata/design context/screenshot/variables，保存为新的 source 证据，不覆盖已有主稿快照。

缺少 `context.md` 时从项目和目标区域代码生成。独立 session 或无 spec 的附着 session，从 fix 节点证据与当前代码生成 revision 1 局部 `spec.json`；附着 session 已有 spec 但缺少当前 scope 时，增加 revision 后补入局部规格。两种情况都为可测语义元素添加稳定 probe，并在缺少 manifest 且本次不引入资产时写入空的 `assets-manifest.json`。当前代码就是修复前实现基线，不要求存在 impl 历史。若修复必须新增、替换或加工素材则停止，提示运行 `t-figma-assets`；不得用空 manifest 绕过本次变更涉及的资产。

## 精修闭环

1. 将节点 screenshot 与当前 DOM 区域对照，判断偏差属于 spec 分组、素材、响应式、样式值或现有组件使用问题。
2. 若 MCP 平面结构不准确，先更新 spec 对应 scope、增加 revision 并记录代码/截图/metadata 证据；首次生成的局部 spec 使用 revision 1。
3. 当前 session 没有该 scope 的可用 delta 时，先用 `scopeSelector` 做一次只读局部测量，产生修复前 delta；把本次节点的 `source/baseline-<node-name>.png` 显式作为 `--baseline`。测量无法运行时停止，不得凭视觉描述代替 agent 所需的结构化 delta。
4. 注入并委派 `figma-fix`，传入当前 scope 的 spec revision 和 delta，限制 change_scope 为目标区域及其直接共享样式；资产只能引用 manifest。发现新素材则停止，提示先运行 assets，不在 fix 内下载或转码。
5. 用相同 `scopeSelector` 和 baseline 运行 `figma-accept` 的局部截图、数值 probes、资产/视频检查。最多 5 轮，只回改当前 scope 的阻塞项。
6. 比较 Figma 表达、修复前代码和最终通过代码，写候选；收敛后按契约去重、改写、晋升长期规则。页面专属补丁和单次像素值不晋升。

输出修改范围、spec revision、局部 delta、验证证据、候选和已晋升规则。未收敛时不得更新长期规则。
