---
name: t-figma-assets
description: Download image/video assets from Figma, convert them to WebP/MP4, place them in the target project, and write the asset mapping manifest.
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

从 Figma 下载图片/视频素材，转换为 WebP/MP4 落位，写 `assets-manifest.json` 后即完成。不实现 UI、不生成规格。按节点 metadata 和脚本检查结果直接执行，不逐张看图评估。

执行方法：`${CLAUDE_PLUGIN_ROOT}/guides/figma/assets.md`（下载或转换前读）
plan 与 manifest 契约：`${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md`（编写 plan 前读）

## 工作流

1. 从 URL 解析 `fileKey`/`nodeId`，工作目录为 `.ai/figma/<fileKey>-<nodeId>/`；探测正式资产目录与引用方式，多个同等合理目录时询问。
2. 发现素材：收集主节点内图片/视频节点，不足时按 metadata 列同文件候选，`--asset-url` 显式补充；匹配不唯一时列 node/page/name/size 证据询问，不盲选、不逐张截图比对。
3. 含文字的营销图按节点层级导出最小共同父节点并标 `flattened: true`；文字疑似交互、动态数据或本地化语义时询问。
4. 用 `download_assets` 导出到 `raw/`，按 assets.md 声明透明意图；视频必须有 `--video-source` 或 MCP URL，缺失则停止。
5. 写 `assets-plan.json` 并运行 batch，由脚本判定是否需要 mask；仅对 `ALPHA_MASK_REQUIRED` 指定的节点补隔离截图，按 assets.md 重跑与清理，报告结果、warnings 和 manifest 路径。

## 门禁

- batch 成功且 warnings 已逐条复核后才算完成；报错时保留现场并转述原因。
