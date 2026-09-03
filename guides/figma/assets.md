# Figma 素材处理

结构和字段以 `${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md` 为准，本页只说明执行方法。

## 发现零散素材

先提取主 frame，再获取同文件 page 清单和稀疏 metadata。用主稿中的视觉角色、语义名称、宽高和节点类型筛选候选；不要对整文件逐节点请求 design context。开发者给出的 `--asset-url` 直接加入候选，匹配不唯一时列证据询问。

## 合成含文字图片

当图片、装饰和文字共同构成不可拆的营销素材时，找到覆盖它们的最小父节点并导出该节点。检查父节点是否混入按钮、动态价格、本地化文案或其它 live UI；存在这些情况先询问。合成后记录文字摘要供 alt 文本和审计使用，页面不得再重复渲染同一文字。

## 下载原始素材

节点确认后必须通过 Figma MCP `download_assets` 导出原始素材。`get_design_context` 中的素材 URL 只用于识别和理解设计，不作为下载源。

- `defaultScale` 默认使用 `3`；banner、hero 和主要内容图均保持 3 倍导出。
- 只有明确属于小型、非关键的图标或装饰素材时，才将 `defaultScale` 降为 `2`。
- 按目标素材类型设置导出格式：需要位图处理的素材导出 PNG/JPEG，矢量素材导出 SVG。
- `download_assets` 返回的临时 URL 必须立即下载到 `.ai/figma/<session>/raw/`，不得直接写入正式代码或 manifest。
- 这类素材在 manifest 中的 `source` 记录为 `download-assets`，不要标记为 `design-context` 或 `url`。

## 图片转换

1. PNG/JPEG 照片转 quality 100 WebP；透明或含文字合成图转 lossless WebP。
2. 用 ffprobe 读取最终宽高，约分成 `W/H`；不要从 CSS 或 Figma 标注猜比例。
3. 按节点语义识别 mobile/desktop 变体并写入 manifest。没有移动版本时 impl 不生成多余 `<picture>` wrapper。
4. 正式路径先查 hash，同名异内容停止，禁止静默覆盖。

## 视频转换

Figma MCP 没有原视频时接受开发者提供的 URL 或项目内本地路径。用 `${CLAUDE_PLUGIN_ROOT}/scripts/figma-assets.py video` 生成 H.264/AAC、yuv420p、faststart MP4；转换后检查 codec、尺寸、moov 顺序。HTTP Range 是部署能力，必须在页面验收时另行请求验证。
