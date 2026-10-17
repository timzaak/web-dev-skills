# Figma 素材处理

结构和字段以 `${CLAUDE_PLUGIN_ROOT}/protocols/figma-workflow-contract.md` 为准，本页只说明执行方法。

## 发现零散素材

先提取主 frame，再获取同文件 page 清单和稀疏 metadata。用节点名称、类型、宽高和层级筛选候选；不要对整文件逐节点请求 design context，也不要逐张截图预览。开发者给出的 `--asset-url` 直接加入候选，匹配不唯一时列 metadata 证据询问。

## 合成含文字图片

当图片、装饰和文字共同构成不可拆的营销素材时，按节点层级找到覆盖它们的最小父节点并导出。检查节点信息是否包含按钮、动态价格、本地化文案或其它 live UI；存在这些情况先询问。合成图在 manifest 标记 `flattened: true`，页面不得再重复渲染同一文字。

## 下载原始素材

节点确认后必须通过 Figma MCP `download_assets` 导出原始素材。`get_design_context` 中的素材 URL 只用于识别和理解设计，不作为下载源。

- `defaultScale` 默认使用 `3`；banner、hero 和主要内容图均保持 3 倍导出。
- 只有明确属于小型、非关键的图标或装饰素材时，才将 `defaultScale` 降为 `2`。
- 按目标素材类型设置导出格式：需要位图处理的素材导出 PNG/JPEG，矢量素材导出 SVG。
- `download_assets` 返回的临时 URL 必须立即下载到 `.ai/figma/<fileKey>-<nodeId>/raw/`，不得直接写入正式代码。
- 这类图片条目在 manifest 中的 `source` 记录为 `download-assets`。

## 透明声明与 alpha 处理

按设计意图填写 plan 的 `transparent`：图标、装饰、叠加素材、透明圆角或外发光为 `true`，实心背景和照片式插画为 `false`；无法确定时询问开发者。字段与校验规则见工作流契约的「资产 plan」。

- 先不填 `alphaMask` 运行 batch，由脚本检测真实像素；仅收到 `ALPHA_MASK_REQUIRED` 时，对报错节点调用 `get_screenshot(contentsOnly: true)`，下载隔离 PNG 到 `raw/`、补入 `alphaMask` 后重跑。已有 mask 的条目可保留。脚本缩放 mask 并合并到原始 3 倍 RGB；其他检测错误直接报错，不靠目视推断或补 mask 绕过。
- RGB 被画布色烘焙时另填 `unbakeColor`（常见为 `1e1e1e`，以实际为准），脚本结合有效 alpha 还原颜色；没有烘焙时不填。
- 声明不透明却检测到透明像素时复核 warning：确认设计意图后保留声明或改为 `true`，无需重复获取已有的有效 alpha。透明终检及 mask/颜色修复链路中的 TinyPNG alpha 恢复由脚本完成，不逐张目视评估压缩效果。

## 批量转换

1. 下载素材并声明透明意图后，按契约写工作目录 `assets-plan.json`，在目标项目根运行 `${CLAUDE_PLUGIN_ROOT}/scripts/figma-assets.py batch <plan>`。单张临时转换可用 `image|svg|video` 子命令。
2. PNG 压缩需要 kyz daemon 的 tinify 代理：默认 `127.0.0.1:8477`（`--tinypng-proxy` 覆盖），按 `Host: api.tinify.com` 转发并自动读取 daemon token。转换前确认 `kyz daemon status` 的 proxy_listen 存在；代理/上游错误（401、429、body 超限）时停止并转述，不回退为本地有损压缩。上传超过默认 10 MiB 时先调大 `request_body_limit_bytes`。
3. 失败时保留 plan 与 `raw/`，修复后重跑。输出已存在时默认停止；使用 `--overwrite-existing` 前须逐项确认是本次失败批处理的残留，或已获开发者明确替换授权。
4. 成功后逐条复核 warnings，再删除 `raw/`、保留 plan，报告 stdout 汇总 JSON 与 manifest 路径。

## SVG 优化

矢量素材不直接复制：plan 条目 `kind: svg` 由 batch 统一处理，脚本用 SVGO（默认预设 + multipass）清理 Figma 导出的冗余并落位，同时从优化产物的 width/height 或 viewBox 提取 manifest 尺寸。SVGO 缺失时脚本报错，安装 `npm install -g svgo` 后重跑；不回退为直接复制。

## 视频转换

Figma MCP 没有原视频时接受开发者提供的 URL 或项目内本地路径，下载后作为条目 `source`。batch 生成 H.264/AAC、yuv420p、faststart MP4；转换后脚本检查 codec、尺寸、moov 顺序。HTTP Range 是部署能力，必须在页面验收时另行请求验证。
