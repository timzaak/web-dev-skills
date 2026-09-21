---
name: t-figma-assets
description: Download image/video assets from Figma, convert them to WebP/MP4, place them in the target project, and write a simple asset mapping manifest.
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

只做三件事：从 Figma 下载图片/视频、转换成 WebP/MP4 并落位、输出 `assets-manifest.json` 映射。不实现 UI、不生成规格、不维护规则记忆。

运行时边界：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`（正式产物写入位置有争议时读）
执行方法：`${CLAUDE_PLUGIN_ROOT}/guides/figma/assets.md`（下载或转换前读）
共享契约：`${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md`（写 manifest 前读）

## 工作流

1. 调用 `${CLAUDE_PLUGIN_ROOT}/scripts/figma-session.py resolve` 校验 target-file，session 复用/归档/创建/多选按共享契约的 Session Resolve 表执行。探测正式资产目录与引用方式，多个同等合理目录时询问。
2. 发现素材：收集主节点内的图片/视频节点；不足时按 metadata 列同文件候选；`--asset-url` 显式补充。匹配不唯一时列出 node/page/name/size 证据询问，不盲选。
3. 含文字的图片默认导出包含文字的最小视觉父节点，manifest 标 `flattened: true`；文字疑似交互、动态或本地化语义时询问。
4. 按 assets.md 导出素材并立即下载到 session `raw/`，不得直接写入正式代码；预期透明的组合节点按 assets.md 同时准备 alpha mask。视频按 `--video-source` 提供 URL 或项目内文件，缺失则停止。
5. 逐个调用 `${CLAUDE_PLUGIN_ROOT}/scripts/figma-assets.py image|video|svg` 转换并落位，导出倍率和 mask/反烘焙参数按 assets.md 选择；PNG 压缩经 kyz daemon 的 TinyPNG 代理，预检与失败处理按 assets.md；SVG 必须走 `svg` 子命令优化，已有 WebP/GIF 直接复制。正式路径已存在时停止，除非开发者明确要求替换。
6. 汇总脚本 JSON 输出写 `assets-manifest.json`（字段按契约；无素材也写 `[]`），删除 `raw/`，session stage 设为 `assets`。

## 门禁

- 脚本报错时停止并转述原因；失败不写半成功 manifest。
- 输出下载、转换、复用、失败项和 manifest 路径，不声称完成 UI。
