# Figma 素材处理

结构和字段以 `${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md` 为准，本页只说明执行方法。

## 发现零散素材

先提取主 frame，再获取同文件 page 清单和稀疏 metadata。用主稿中的视觉角色、语义名称、宽高和节点类型筛选候选；不要对整文件逐节点请求 design context。开发者给出的 `--asset-url` 直接加入候选，匹配不唯一时列证据询问。

## 合成含文字图片

当图片、装饰和文字共同构成不可拆的营销素材时，找到覆盖它们的最小父节点并导出该节点。检查父节点是否混入按钮、动态价格、本地化文案或其它 live UI；存在这些情况先询问。合成后记录文字摘要供 alt 文本和审计使用，页面不得再重复渲染同一文字。

## 图片转换

1. 临时 URL 立即下载到 `memo/figma/<session>/raw/`。
2. PNG/JPEG 照片转 quality 82 WebP；透明或含文字合成图转 lossless WebP。
3. 用 ffprobe 读取最终宽高，约分成 `W/H`；不要从 CSS 或 Figma 标注猜比例。
4. 按节点语义识别 mobile/desktop 变体并写入 manifest。没有移动版本时 impl 不生成多余 `<picture>` wrapper。
5. 正式路径先查 hash，同名异内容停止，禁止静默覆盖。

## 视频转换

Figma MCP 没有原视频时接受开发者提供的 URL 或项目内本地路径。用 `${CLAUDE_PLUGIN_ROOT}/scripts/figma-assets.py video` 生成 H.264/AAC、yuv420p、faststart MP4；转换后检查 codec、尺寸、moov 顺序。HTTP Range 是部署能力，必须在页面验收时另行请求验证。
