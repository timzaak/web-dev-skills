---
name: t-figma-assets
description: Prepare Figma assets before UI binding; download media and isolated PNG evidence, let the script derive and repair transparency, convert assets, and write a verified manifest. Does not implement UI.
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Write
  - Bash
  - mcp__figma__get_metadata
  - mcp__figma__get_screenshot
  - mcp__figma__download_assets
---

# Figma 素材准备

从 Figma 下载图片/视频素材，转换为 WebP/MP4 落位，写 `assets-manifest.json` 并通过脚本复验后即完成。不实现 UI、不生成规格。AI 负责收集同节点导出与隔离证据，透明度及底色修复由脚本判定，不逐张看图评估。

执行方法：`${CLAUDE_PLUGIN_ROOT}/guides/figma/assets.md`（下载或转换前读）
plan 与 manifest 契约：`${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md`（编写 plan 前读）

## 工作流

1. 从 URL 解析 `fileKey`/`nodeId`，工作目录为 `.ai/figma/<fileKey>-<nodeId>/`；探测正式资产目录与引用方式，多个同等合理目录时询问。
2. 发现素材：收集主节点内图片/视频节点，不足时按 metadata 列同文件候选，`--asset-url` 显式补充；匹配不唯一时列 node/page/name/size 证据询问，不盲选、不逐张截图比对。
3. 含文字的营销图按节点层级导出最小共同父节点并标 `flattened: true`；文字疑似交互、动态数据或本地化语义时询问。
4. 用 `download_assets` 导出到 `raw/`；每个 image 节点都调用 `get_screenshot(contentsOnly: true)`，按 assets.md 下载并保留隔离 PNG，禁止按 AI 判断跳过。视频必须有 `--video-source` 或 MCP URL，缺失则停止。
5. 写 `assets-plan.json` 并运行 batch；脚本根据隔离 PNG 判定透明度、修复 alpha 与可识别的烘焙底色。按 assets.md 运行 verify、重跑与清理，报告脚本汇总和 manifest 路径。

## 门禁

- batch 与 verify 均成功才算完成；证据缺失、不匹配或颜色修复不确定时保留现场并转述脚本错误，不手写 manifest、不改透明声明绕过。
