---
name: t-figma-assets
description: Prepare Figma bitmaps, SVGs, and videos for human-guided UI implementation; identify assets, validate their types, collect bitmap evidence, convert or optimize, and write a verified manifest. Does not implement UI.
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

从 Figma 下载位图/矢量/视频素材，分别转换为 WebP、优化 SVG、转换为 MP4 落位，写 `assets-manifest.json` 并通过脚本复验后即完成。不实现 UI、不生成规格。AI 负责收集同节点导出与隔离证据，透明度及底色修复由脚本判定，不逐张看图评估。

执行方法：`${CLAUDE_PLUGIN_ROOT}/guides/figma/assets.md`（下载或转换前读）
plan 与 manifest 契约：`${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md`（编写 plan 前读）

## 工作流

1. 从 URL 解析 `fileKey`/`nodeId`，工作目录为 `.ai/figma/<fileKey>-<nodeId>/`；探测正式资产目录与引用方式，多个同等合理目录时询问。
2. 确认本轮人指定的范围；已有 `context.md` 时读取范围与待补素材清单。按 assets.md 的「素材识别与类型校验」筛选候选，metadata 不足以判定类型时保留待确认项；匹配不唯一时列证据询问，不扩展到未确认设计。
3. 含文字的营销图按节点层级导出最小共同父节点并标 `flattened: true`；文字疑似交互、动态数据或本地化语义时询问。
4. 用 `download_assets` 获取资源，按该指南区分返回条目、下载到 `raw/` 并核对真实格式后才确定 plan 的 `kind` 和输出扩展名；每个 image 节点调用 `get_screenshot(contentsOnly: true)` 并保留隔离 PNG。视频必须有 `--video-source` 或 MCP URL。类型冲突、节点关联不明或来源缺失时交给人处理，不伪造就绪条目；impl 可继续留空。
5. 写 `assets-plan.json` 并运行 batch；脚本执行类型与输出扩展名检查，根据隔离 PNG 判定透明度、修复 alpha 与可识别的烘焙底色。按 assets.md 运行 verify、重跑与清理，报告脚本汇总、manifest 路径及待人工处理项。

## 门禁

- batch 与 verify 均成功才算完成；证据缺失、不匹配或颜色修复不确定时保留现场并转述脚本错误，不手写 manifest、不改透明声明绕过。
