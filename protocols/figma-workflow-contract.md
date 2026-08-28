# Figma UI 工程工作流契约

本契约是 `/t-tools:t-figma-assets`、`/t-tools:t-figma-impl`、`/t-tools:t-figma-fix` 与内部 Figma agents 的共享真相源。它覆盖目标项目中的工作区关联、Figma 原始快照、二次规格、资产清单、规则记忆和验收门禁。

## Command Contract

```text
/t-tools:t-figma-assets <figma-url> <target-file> [--asset-url <figma-node-url> ...] [--video-source <node-id>=<url-or-local-path> ...]
/t-tools:t-figma-impl <figma-url> <target-file>
/t-tools:t-figma-fix <figma-node-url> <target-file> <问题、状态或断点描述>
```

- `<target-file>` 必须已存在、位于目标项目内且路径中不得含 `..`。
- `figma-url` 必须能解析 `fileKey` 与 `nodeId`。assets/impl 的 URL 指向整页或主 frame；fix 的 URL 指向待精修节点。
- 三个命令以规范化后的项目相对 `target-file` 关联工作区。一个目标文件同时命中多个活动工作区时必须请开发者选择，不得按时间或目录顺序猜测。
- assets/impl 命中 session 后必须校验 URL 的 `fileKey + mainNodeId` 一致；不一致时请开发者选择归档旧 session 或回到原主稿，不得复用旧 spec。fix 允许 nodeId 不同，但 fileKey 必须与 session 一致。
- `t-figma-impl` 要求 assets 阶段已经完成；无素材页面也必须存在空的 `assets-manifest.json`。
- `t-figma-fix` 要求已有 impl 工作区和二次规格，不承担从零整页实现。

旧 `/t-tools:t-figma` 不保留兼容入口。

## Workspace and Identity

目标项目使用以下结构：

```text
.ai/figma/
├── index.json
└── <session-id>/
    ├── session.json
    ├── source/
    │   ├── metadata.xml
    │   ├── design-context.md
    │   ├── variables.json
    │   └── baseline[-<node-name>].png
    ├── raw/
    ├── spec.json
    ├── context.md
    ├── assets-manifest.json
    ├── conflicts.json
    ├── rule-candidates.md
    ├── actual.png
    ├── delta-report.json
    ├── iterations/
    └── pixel-diff.png
```

`session-id` 默认是清洗后的 `<fileKey>-<mainNodeId>`。`index.json`：

```json
{
  "version": 1,
  "targets": {
    "src/pages/home.tsx": [
      { "sessionId": "abc123-1-2", "status": "active" }
    ]
  }
}
```

- target key 使用相对项目根、`/` 分隔、消除 `.` 后的路径；Windows 上匹配时不区分大小写，落盘保持真实大小写。
- `status` 只允许 `active|archived`。一个 target 只有一个 active session 时自动使用；零个时 assets/impl 可创建、fix 必须停止；多个时必须询问。
- `session.json` 保存主 URL、fileKey、mainNodeId、targetFile、当前 stage（`assets|implemented|fixing|accepted`）和 `specRevision`。状态文件不写时间元数据。

## Source of Truth and Reconstruction

1. 目标项目代码、配置及 `AGENTS.md`/`CLAUDE.md` 是当前实现与执行约束。
2. `docs/figma-rules.md` 是已验证的项目级 Figma 长期规则。
3. `source/` 是同一 MCP 提取窗口内取得的不可变原始证据；不得在调试中覆盖。
4. `spec.json` 是可修正的二次规格，是实现与数值验收的当前基准。
5. `rule-candidates.md` 是当前 session 的候选经验，不自动凌驾于代码或长期规则。

`get_design_context` 返回的是设计表达，不视为可靠 DOM。规格提取必须把 metadata、design context、screenshot、项目代码同时用于二次重建：

- 以视觉边界和 stacking 识别实际 block，而不是机械照搬 frame/group；
- 记录绝对定位、裁切、重叠、背景和最小视觉组合；
- 优先映射项目已有组件、token、动效和响应式模式；
- 只有视觉证据或现有代码支持时才修正 MCP 结构，不得凭空创造隐藏状态；
- 每次修正增加 `spec.revision`，并在 `revisions[]` 写 `{revision, scope, reason, evidence}`，不得写时间字段。

`spec.json` 至少包含 `source`、`revision`、`revisions`、`viewport`、`nodes`、`assets`、`probeSelectors`、`probeableNodes` 和 `integrity`。probe 规则和 delta 阈值沿用本契约后文。

## Asset Discovery and Processing

### Discovery

- 先对主节点调用 metadata/design context/screenshot/variables。
- 主节点内资产不足时，调用无 nodeId 的 `get_metadata` 枚举同文件 pages，再按节点名、类型、尺寸、视觉角色和主稿上下文筛选候选；只对候选节点获取详细上下文。
- `--asset-url` 是显式补充来源，优先级高于自动匹配。
- 跨 Figma 文件不自动扫描，必须显式提供节点 URL。
- 候选无法唯一匹配时停止并列出 node id、page、名称、尺寸和截图证据，不得选择“看起来最像”的素材。

### Composite Assets

资产候选的视觉范围内存在文字子节点时，默认导出包含图片和文字的最小共同视觉父节点，作为单张合成图：

- manifest 记录 `sourceNodeIds`、`flattened: true` 和 `embeddedText`；
- impl/fix 不再把这些文字重复实现为 live DOM；
- 如果文字涉及交互、动态数据、本地化或独立无障碍语义，必须先请开发者裁决是否允许扁平化。

### Images

- MCP 临时 URL 必须立即下载到 session `raw/`，不得写入正式代码。
- PNG/JPEG 转 WebP；照片使用 quality 82，透明图和 `flattened: true` 的含文字合成图使用 lossless WebP。
- SVG、已有 WebP 和 GIF 默认保留；项目长期规则可覆盖默认策略。
- 使用 ffprobe 提取最终宽高，并以最大公约数记录 `aspectRatio`。移动/桌面变体必须在 manifest 的同一 `variants` 组关联。
- assets 阶段不编辑 UI 源码；impl/fix 根据 manifest 生成 `<picture>`、`srcset` 或目标栈等价表达，并写入真实 aspect-ratio。

### Video

- 视频源可以是 MCP 明确返回的临时 URL、`--video-source` URL 或项目内本地文件。官方 MCP 无原始视频时必须要求补充来源，禁止用截图、GIF 或占位视频伪造。
- 最终视频使用 MP4：H.264、AAC（存在音轨时）、`yuv420p`、CRF 23、medium preset、AAC 128k、`+faststart`；保持源尺寸，奇数宽高向下调整为偶数。
- ffprobe 必须验证容器、codec、pixel format 和尺寸；检查 `moov` 位于 `mdat` 前。
- 页面验收对视频 URL 发 `Range: bytes=0-1`，必须得到 `206` 和有效 `Content-Range`。faststart 通过但服务器无 Range 仍阻塞“流式播放”验收。

### Manifest

`assets-manifest.json` 是 impl/fix 引用资产和 accept 校验完整性的唯一来源：

```json
[
  {
    "id": "1:5",
    "name": "hero-campaign",
    "kind": "image",
    "source": "node-export",
    "sourceNodeIds": ["1:5", "1:6"],
    "flattened": true,
    "embeddedText": ["Summer sale"],
    "outputPath": "public/assets/hero-campaign.webp",
    "publicUrl": "/assets/hero-campaign.webp",
    "sha256": "<64 lowercase hex>",
    "mimeType": "image/webp",
    "width": 1920,
    "height": 1080,
    "aspectRatio": "16/9",
    "variants": { "desktop": "public/assets/hero-campaign.webp" },
    "conversion": { "mode": "webp-lossless" }
  }
]
```

- `kind` 允许 `image|svg|gif|video`；`source` 允许 `design-context|download-assets|node-export|url|local-file`。
- `publicUrl` 是页面运行时 URL；视频必填，用于 Range 验收，图片按目标栈需要填写。
- 名称必须语义化并沿用项目命名风格。禁止节点 id、数字序号、hash 和 Figma 默认层名作为最终文件名。
- 同名同 SHA-256 复用；同名异内容必须停止，请开发者改名或明确允许替换。
- manifest 只记录已成功落位且校验通过的资产；失败时不得写半成功条目。

## Project Rule Memory

每个命令开始前读取目标代码、`docs/figma-rules.md` 和当前 session 候选；fix 还必须读取历史 delta 与当前区域代码。

候选格式使用“观察 / 证据 / 建议规则 / 验证状态”。只有同时满足以下条件才可晋升：

1. 当前实现已通过 accept，或开发者明确确认；
2. 规则由项目现有代码支持，或已在至少两个不同节点/页面复用；
3. 不与更高优先级项目事实冲突；
4. 能凝练为一句“适用条件 → 执行动作”，不含选择器、单次像素值或页面专属补丁。

`docs/figma-rules.md` 最多 10 条活动规则，按结构、素材、响应式、局部精修分组。相同规则合并；新证据用于改写旧规则而不是追加。达到上限、证据不足或冲突的候选留在 session，并在报告列出。

## Measurement and Acceptance

测量使用 `spec.json.probeSelectors`，优先使用稳定的 `data-figma='<name>'` selector。支持全页或 `scopeSelector` 局部截图；局部 fix 的 baseline 和 actual 必须是同一视觉范围。

| 属性类别 | PASS | WARN | FAIL |
|---|---|---|---|
| 数值（fontSize/width/height/x/y/padding/margin/gap/radius） | delta < 2px | 2 ≤ delta < 4px | delta ≥ 4px |
| sRGB 颜色 | 完全匹配 | 不支持格式 | 可解析但不匹配 |
| transition/animation duration | 完全匹配 | delta < 50ms | delta ≥ 50ms |
| font-weight/opacity/lineHeight | 完全匹配 | lineHeight 一边为 normal | 不匹配 |

- FAIL/MISSING/ERROR、资产路径/hash/加载错误、视频 Range 错误均阻塞收敛。
- WARN、已声明 token CONFLICT、探针覆盖率和 pixel diff 不单独阻塞，但必须进入报告。
- screenshot/pixel diff 可以用于定位错误分组、裁切和 stacking，并据此修订二次规格；不得只凭模糊视觉印象改任意数值。
- `max-iterations` 默认 5。每轮归档 `iterations/iter-<N>.json`；达到上限仍未收敛则 `EXHAUSTED`。
- accept 只写 `.ai/figma/**` 测量产物和 `.ai/quality/figma-*.md` 报告，不修改代码、正式资产或长期规则。

## Failure Rules

- MCP 核心能力、ffmpeg/ffprobe、栈、dev server 或 Playwright 缺失时给出可操作提示并停止。
- 原始快照不完整、必要素材无法下载、视频无来源、候选素材有歧义或同名内容冲突时，不进入实现。
- 规则冲突不得静默覆盖；报告冲突来源并等待开发者裁决。
- impl/fix 验证失败时不得宣称收敛；accept 不得代替实现 agent 修代码。
