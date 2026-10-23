---
name: t-figma-impl
description: Implement a Figma UI in an existing frontend file, block by block; leave pending assets empty, bind prepared assets, and hand over for manual acceptance. Does not prepare media assets.
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

按人确认的本轮范围重建 Figma UI 并实现到既有前端文件；遵循工作流契约的「协作范围」，不补全未确认设计，不下载、转换素材。还原方法见 `${CLAUDE_PLUGIN_ROOT}/guides/figma/reconstruction.md`（分块前读），manifest 与交付规则见 `${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md`，agent 派发遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md`。

## 前置

校验 URL 与 target-file；`<preview-url>` 可选，仅用于交付报告回显。工作目录为 `.ai/figma/<fileKey>-<nodeId>/`。读取目标文件、邻近模块与项目 token/组件/动效模式，写 `context.md`：块清单（名称、baseline、使用资产、组件映射、精确数值）、主稿 viewport、目标栈验证命令；manifest 用路径引用，不复述内容。栈无法确定时询问。

按工作流契约的「工作目录」检查素材就绪情况：已就绪的引用 manifest 条目；manifest 缺失、部分条目缺失或产物未就绪时，对应位置跳过留空，缺项写 `context.md`，继续实现其它内容。位图、SVG、视频均交给 `t-figma-assets` 准备，impl 不补做素材。绑定遵循契约的「素材类型保真」。

## 还原与实现

1. 在 MCP 窗口内为主节点和各视觉块保存 baseline 截图到 `source/`（一次写入，不覆盖）；metadata、design context 和 variables 只在窗口内消费，不整页落盘。
2. 按 reconstruction 指南分块：截图定结构、节点树补精确数值，按文档顺序拆成可独立实现的视觉块，块清单写入 `context.md`。
3. 逐块委派 `figma-impl` agent：每次一个块或少量相邻小块，给出该块的 baseline、已就绪资产条目 id、待补素材清单和组件映射；素材未就绪不算块实现失败，留空后继续。实现失败先重试该块，不带病推进；中断后按 `context.md` 未完成块与待补素材恢复。

## 交付

4. 全部块实现后，若仍有待补素材，报告已实现布局和留空清单，提示以同一主稿 URL 运行 `t-figma-assets`，本轮以待绑定状态结束，不宣称整页完成。素材补齐后重读 manifest，按「素材类型保真」绑定并核对目标代码实际引用，重跑栈验证；无需重做已完成布局。
5. 缺项清零后在目标项目根运行 `python ${CLAUDE_PLUGIN_ROOT}/scripts/figma-assets.py verify <工作目录>/assets-plan.json`；plan/manifest 缺失、旧产物缺少验证证据或复验失败时交回 assets 修复，保留布局。栈验证和素材门禁均通过才交付：报告完成块清单与失败项，附 preview URL（如有）和 baseline 位置，由开发者对照页面人工验收。
