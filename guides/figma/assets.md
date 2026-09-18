# Figma 素材处理

结构和字段以 `${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md` 为准，本页只说明执行方法。

## 发现零散素材

先提取主 frame，再获取同文件 page 清单和稀疏 metadata。用主稿中的视觉角色、语义名称、宽高和节点类型筛选候选；不要对整文件逐节点请求 design context。开发者给出的 `--asset-url` 直接加入候选，匹配不唯一时列证据询问。

## 合成含文字图片

当图片、装饰和文字共同构成不可拆的营销素材时，找到覆盖它们的最小父节点并导出该节点。检查父节点是否混入按钮、动态价格、本地化文案或其它 live UI；存在这些情况先询问。合成图在 manifest 标记 `flattened: true`，页面不得再重复渲染同一文字。

## 下载原始素材

节点确认后必须通过 Figma MCP `download_assets` 导出原始素材。`get_design_context` 中的素材 URL 只用于识别和理解设计，不作为下载源。

- `defaultScale` 默认使用 `3`；banner、hero 和主要内容图均保持 3 倍导出。
- 只有明确属于小型、非关键的图标或装饰素材时，才将 `defaultScale` 降为 `2`。
- 按目标素材类型设置导出格式：需要位图处理的素材导出 PNG/JPEG，矢量素材导出 SVG。
- `download_assets` 返回的临时 URL 必须立即下载到 `.ai/figma/<session>/raw/`，不得直接写入正式代码。
- 这类图片条目在 manifest 中的 `source` 记录为 `download-assets`。
- 视觉上应透明的组合节点不能只相信 `pix_fmt`：Figma 可能返回带 alpha 容器但 alpha 全为 255，并把画布色 `#1e1e1e` 烘焙进 RGB。对此节点同时调用 `get_screenshot(contentsOnly: true)`，下载隔离 PNG 作为 alpha mask；保留 `download_assets` 的 3 倍 RGB，通过脚本缩放并合并隔离截图的 alpha。
- alpha mask 合并只恢复透明度：半透明像素的 RGB 仍是与画布色 `#1e1e1e` 复合后的值，浅色渐变在页面上会显灰。转换时追加 `image --unbake-color 1e1e1e`（与 `--alpha-mask` 连用或对已带正确 alpha 的烘焙图单独使用），脚本按 `真实RGB=(烘焙RGB-(1-a)*背景)/a` 反解；Figma 桌面端 Export 导出可作权威对照，画布色非默认时以其为准。

## 图片转换

1. PNG/JPEG 照片按脚本默认 quality 转 WebP；透明或含文字合成图转 lossless WebP。预期透明图使用 `image --alpha-mask <isolated.png> --expect-alpha`；脚本必须确认最终 alpha 存在透明像素，不能只检查像素格式。
2. 用 ffprobe 读取最终宽高，约分成 `W/H`；不要从 CSS 或 Figma 标注猜比例。
3. 正式路径已存在时停止，禁止静默覆盖；开发者明确要求替换时才覆盖。
4. 脚本 `image|video` 的 JSON 输出（outputPath、width、height、aspectRatio）即 manifest 条目数据；全部成功后汇总写 `assets-manifest.json`，再删除 `raw/`。

## SVG 优化

矢量素材不直接复制：逐个调用 `svg <source> <output>`，脚本用 SVGO（默认预设 + multipass）清理 Figma 导出的冗余并落位，同时从优化产物的 width/height 或 viewBox 提取 manifest 尺寸。SVGO 缺失时脚本报错，安装 `npm install -g svgo` 后重跑；不回退为直接复制。

## 视频转换

Figma MCP 没有原视频时接受开发者提供的 URL 或项目内本地路径。用 `${CLAUDE_PLUGIN_ROOT}/scripts/figma-assets.py video` 生成 H.264/AAC、yuv420p、faststart MP4；转换后检查 codec、尺寸、moov 顺序。HTTP Range 是部署能力，必须在页面验收时另行请求验证。
