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

## 隔离证据与自动透明修复

每个 image 条目都需要同一导出节点的独立隔离 PNG，包含照片和看起来不透明的素材；不能先由 AI 决定哪些图片需要检查。字段、自动判定规则与失败码以工作流契约的「资产 plan」为准。

- 对每个 image 调用 `get_screenshot(contentsOnly: true)`，下载 PNG 到 `source/asset-<node-id>.png`（文件名中的冒号替换为连字符），plan 的 `referencePng` 指向它。使用导出节点的完整边界，不能用整页截图、原始 image fill 或另一节点代替；可按 metadata 的较长边设置 `maxDimension`，避免默认上限缩小分辨率。
- 隔离证据一次写入后保留；已存在时复用同一稿的证据。设计发生变化或证据需重新获取时，使用带版本后缀的新文件并更新 plan，不覆盖旧快照。截图失败或不提供可下载 PNG 时停止。
- plan 不再接受 `transparent`、`alphaMask`、`unbakeColor`。脚本使用参考 alpha、检测 RGB 与参考是否一致、拟合可识别的烘焙底色，并自动修复；不确定时重新获取正确导出与隔离证据，不猜底色、不增加人工 override。
- TinyPNG 后恢复完整参考 alpha，最终逐像素核对；正式产物保留原始高清 RGB 分辨率，只有显式 `maxWidth` 才缩小。脚本不能认证截图来自哪个 Figma 节点，AI 仅负责保证两个 MCP 请求的 fileKey/nodeId 相同。

## 批量转换

1. 下载素材和隔离证据后，按契约写工作目录 `assets-plan.json`，在目标项目根运行 `python ${CLAUDE_PLUGIN_ROOT}/scripts/figma-assets.py batch <plan>`。图片处理需要 Pillow，缺失时运行 `python -m pip install Pillow` 后重跑。单张临时转换使用 `image <source> <output> --reference-png <isolated.png>`；矢量/视频使用 `svg|video` 子命令，临时转换不能代替 batch manifest。
2. PNG 压缩需要 kyz daemon 的 tinify 代理：默认 `127.0.0.1:8477`（`--tinypng-proxy` 覆盖），按 `Host: api.tinify.com` 转发并自动读取 daemon token。转换前确认 `kyz daemon status` 的 proxy_listen 存在；代理/上游错误（401、429、body 超限）时停止并转述，不回退为本地有损压缩。上传超过默认 10 MiB 时先调大 `request_body_limit_bytes`。
3. 失败时保留 plan 与 `raw/`，修复后重跑。输出已存在时默认停止；使用 `--overwrite-existing` 前须逐项确认是本次失败批处理的残留，或已获开发者明确替换授权。
4. batch 成功后在同一目标项目根运行 `python ${CLAUDE_PLUGIN_ROOT}/scripts/figma-assets.py verify <plan>`，成功后再删除 `raw/`；保留 plan、manifest 与 `source/asset-*.png`，报告 batch/verify 的 stdout 汇总 JSON 与 manifest 路径。verify 不依赖 raw，可在 impl 交付前重跑。

旧 plan 的透明字段和旧 manifest 没有脚本复验依据，不直接沿用：为所有 image 补充独立隔离 PNG，移除旧字段，再按失败恢复规则重新运行 batch。verify 失败回到 assets 修复，不以人工确认代替脚本门禁。

## SVG 优化

矢量素材不直接复制：plan 条目 `kind: svg` 由 batch 统一处理，脚本用 SVGO（默认预设 + multipass）清理 Figma 导出的冗余并落位，同时从优化产物的 width/height 或 viewBox 提取 manifest 尺寸。SVGO 缺失时脚本报错，安装 `npm install -g svgo` 后重跑；不回退为直接复制。

## 视频转换

Figma MCP 没有原视频时接受开发者提供的 URL 或项目内本地路径，下载后作为条目 `source`。batch 生成 H.264/AAC、yuv420p、faststart MP4；转换后脚本检查 codec、尺寸、moov 顺序。HTTP Range 是部署能力，必须在页面验收时另行请求验证。
