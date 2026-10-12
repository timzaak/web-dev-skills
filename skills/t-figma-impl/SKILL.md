---
name: t-figma-impl
description: Reconstruct and implement a complete Figma UI in an existing frontend file, block by block, using prepared assets, then run a single read-only visual acceptance pass.
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

重建 Figma 整页稿并实现到既有前端文件；不下载、转换素材。还原方法见 `${CLAUDE_PLUGIN_ROOT}/guides/figma/reconstruction.md`（分块前读），manifest 与交付规则见 `${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md`，agent 派发遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md`。

## 前置

校验 URL 与 target-file；`<preview-url>` 可选，仅用于交付报告回显。工作目录为 `.ai/figma/<fileKey>-<nodeId>/`。读取目标文件、邻近模块与项目 token/组件/动效模式，写 `context.md`：块清单（名称、baseline、使用资产、组件映射、精确数值）、主稿 viewport、目标栈验证命令；manifest 用路径引用，不复述内容。栈无法确定时询问。

`assets-manifest.json` 已存在（`[]` 表示无素材）时块清单直接引用真实资产；缺失时进入资产延后模式：块清单与实现只用资产语义引用（节点、名称、预期类型）占位，不下载、不伪造正式资产。

## 还原与实现

1. 在 MCP 窗口内为主节点和各视觉块保存 baseline 截图到 `source/`（一次写入，不覆盖）；metadata、design context 和 variables 只在窗口内消费，不整页落盘。
2. 按 reconstruction 指南分块：截图定结构、节点树补精确数值，按文档顺序拆成可独立实现的视觉块，块清单写入 `context.md`。
3. 逐块委派 `figma-impl` agent：每次一个块或少量相邻小块，给出该块的 baseline、资产和组件映射；块失败先重试该块，不带病推进；中断后按 `context.md` 未完成块恢复。

## 交付

4. 全部块完成后过素材门禁：manifest 缺失时停止，提示以同一主稿 URL 运行 `t-figma-assets`；其完成后做一次绑定（语义引用替换为真实 `outputPath`/`publicUrl`/`aspectRatio`）并重跑栈验证。
5. 报告完成块清单与失败项，附 preview URL（如有）和 baseline 位置，由开发者对照页面人工验收；栈验证失败不宣称完成。
