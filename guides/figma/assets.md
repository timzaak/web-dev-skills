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
- 视觉上应透明的素材不能只相信 `pix_fmt`：Figma 可能把画布色 `#1e1e1e` 烘焙进 RGB 并返回全不透明的 alpha（处理方式见下节，由 batch 强制拦截）。

## 透明声明与 alpha 处理

plan 中每个 image 条目必须显式声明 `transparent`，batch 按声明强制校验；缺声明的 plan 直接报错，不会静默跳过。

- 判定标准：图标、装饰、叠加在其他元素之上、带透明圆角或外发光的素材声明 `true`；整幅实心背景和照片式插画声明 `false`；按设计意图仍无法确定时询问开发者，不默认猜。
- 声明 `true` 且源图已有真实透明像素：无需额外参数，脚本走默认链路并做透明终检。
- 声明 `true` 但源图 alpha 全为 255（画布色 `#1e1e1e` 烘焙进 RGB）：batch 硬错误。对该节点调用 `get_screenshot(contentsOnly: true)`，隔离 PNG 下载到 `raw/` 作为条目 `alphaMask`；脚本保留 `download_assets` 的 3 倍 RGB，缩放并合并隔离截图的 alpha。
- 半透明素材的 RGB 仍是与画布色复合后的值：为条目追加 `unbakeColor`（默认画布色 `1e1e1e`，非默认以实际为准），脚本按 `真实RGB=(烘焙RGB-(1-a)*背景)/a` 反解。
- 声明 `false` 但源图存在透明像素：batch 记 warning 不阻断；逐条复核，确属 opaque 再交付，否则改声明并补 `alphaMask`。
- 透明终检与 TinyPNG alpha 量化恢复由脚本自动执行：声明 `true` 的输出必须有 alpha 通道且有透明像素，不逐张目视评估。

## 批量转换

1. 全部素材下载并完成透明判定后，写工作目录 `assets-plan.json` 并一次运行 `${CLAUDE_PLUGIN_ROOT}/scripts/figma-assets.py batch <plan>`：脚本先做前置校验（schema、透明声明、mask 与来源文件、正式路径不重复不覆盖），再逐条转换，全部成功后原子写 `assets-manifest.json`（无素材写 `[]`），stdout 输出汇总 JSON（manifest 路径、条目数、warnings）。plan 内相对路径按当前工作目录（目标项目根）解析。
2. plan schema：`{"entries": [{id, name, kind: image|svg|video, source, outputPath, transparent, alphaMask, unbakeColor, publicUrl, flattened, lossless, quality, maxWidth, origin}]}`；image 必填 `transparent`，视频必填 `publicUrl`，`origin`（`download-assets|url|local-file`）写入 manifest `source` 字段，未知字段报错。单张临时转换仍可用 `image|svg|video` 子命令，参数与 plan 字段同义。
3. TinyPNG 压缩依赖 kyz daemon 的 tinify 代理规则：默认 `127.0.0.1:8477`（`--tinypng-proxy` 覆盖），脚本按 `Host: api.tinify.com` 转发并自动读取 daemon token。转换前确认 `kyz daemon status` 的 proxy_listen 存在；脚本报代理或上游错误（401 凭据、429 月度配额、body 超限）时停止并转述，不回退为本地有损压缩。上传超过 daemon 默认 10 MiB body 上限时先调大 `request_body_limit_bytes`。
4. 尺寸与比例由脚本 ffprobe 最终产物得出并写入 manifest；不要从 CSS 或 Figma 标注猜比例。
5. 正式路径已存在时 batch 前置校验停止，禁止静默覆盖；修复问题后重跑加 `--overwrite-existing` 覆盖上次批处理的残留输出，开发者明确要求替换正式资产时才使用。
6. batch 成功后删除 `raw/`（`assets-plan.json` 保留）并报告汇总；warnings 逐条复核后才能交付。

## SVG 优化

矢量素材不直接复制：plan 条目 `kind: svg` 由 batch 统一处理，脚本用 SVGO（默认预设 + multipass）清理 Figma 导出的冗余并落位，同时从优化产物的 width/height 或 viewBox 提取 manifest 尺寸。SVGO 缺失时脚本报错，安装 `npm install -g svgo` 后重跑；不回退为直接复制。

## 视频转换

Figma MCP 没有原视频时接受开发者提供的 URL 或项目内本地路径，下载后作为条目 `source`。batch 生成 H.264/AAC、yuv420p、faststart MP4；转换后脚本检查 codec、尺寸、moov 顺序。HTTP Range 是部署能力，必须在页面验收时另行请求验证。
