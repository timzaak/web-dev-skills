---
name: t-figma-assets
description: Discover, download, flatten, convert, place, and verify image/video assets for a Figma UI implementation.
argument-hint: "<figma-url> <target-file> [--asset-url <figma-node-url> ...] [--video-source <node-id>=<url-or-local-path> ...]"
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
  - mcp__figma__download_assets
---

# Figma 素材准备

运行时边界：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`
共享契约：`${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md`
执行方法：`${CLAUDE_PLUGIN_ROOT}/guides/figma/assets.md`

只负责素材发现、下载、合成导出、转换、落位与 manifest；不得实现或精修 UI。

## 输入和关联

解析主 Figma URL、已存在的目标文件、重复 `--asset-url` 和 `--video-source nodeId=source`。调用 `${CLAUDE_PLUGIN_ROOT}/scripts/figma-session.py resolve` 校验并规范化 target-file：唯一 active session 且 fileKey/mainNodeId 一致时复用；不一致时询问，确认后用 `archive` 归档旧 session 再 `create`；没有则以主 URL调 `create`；返回 ambiguous 时 AskUserQuestion 选择。

开始前读取目标项目 `AGENTS.md`/`CLAUDE.md`、目标文件邻近资产用法、`DESIGN.md`（若有）、`docs/figma-rules.md`（若有）和当前 session 候选。探测正式资产目录、命名和引用方式；存在多个同等合理目录时询问。

## 工作流

1. 同一 MCP 窗口内保存主节点 metadata、design context、screenshot、variables 到 session `source/`；这些文件后续不得覆盖。
2. 从主节点收集素材。缺失时用无 nodeId metadata 列 pages，再按 metadata 筛选同文件候选；显式 `--asset-url` 直接加入。匹配不唯一时展示 page/node/name/size 询问，不盲选。
3. 图片上存在文字时检查最小共同视觉父节点。无交互、动态或本地化语义则通过 `download_assets` 导出父节点并标记 flattened；否则询问。
4. MCP 临时 URL 立即下载到 raw。视频没有 MCP 源时按 node id 使用 `--video-source`；缺失则停止并要求 URL 或项目内本地文件。
5. 按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 注入并委派 `figma-assets`，完成转换、落位、hash 和 manifest。
6. 无素材时也写 `[]`。全部成功后把 session stage 设为 `assets`，更新 index。

## 门禁

- 图片转换和视频处理调用 `${CLAUDE_PLUGIN_ROOT}/scripts/figma-assets.py`；缺 ffmpeg/ffprobe 时停止并给安装提示。
- 同名同 hash 复用，同名异 hash 停止；不写半成功 manifest。
- 只记录经过本次证据支持的规则候选，不直接写 `docs/figma-rules.md`；规则晋升在 impl/fix 验收收敛后进行。
- 输出下载、合成、转换、复用、失败项和 manifest 路径，不声称完成 UI。
