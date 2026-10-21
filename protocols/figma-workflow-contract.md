# Figma UI 工程工作流契约

`t-figma-assets`、`t-figma-impl` 与 `figma-impl` agent 的共享契约：命令入参、工作目录、资产 manifest 与验收判定。

## 命令

```text
/t-tools:t-figma-assets <figma-url> <target-file> [--asset-url <figma-node-url> ...] [--video-source <node-id>=<url-or-local-path> ...]
/t-tools:t-figma-impl <figma-url> <target-file> <preview-url>
```

- `target-file` 必须已存在、位于目标项目内且路径不含 `..`。
- `preview-url` 可选，仅在交付报告中回显；页面验收由开发者自行完成，入口不得启动或探测 dev server。
- `figma-url` 必须能解析 `fileKey` 与 `nodeId`，指向整页或主 frame。

## 工作目录

两个命令共享 `.ai/figma/<fileKey>-<nodeId>/`：同一主稿 URL 即同一目录，由首个入口创建，无注册表、无状态文件。

```text
.ai/figma/<fileKey>-<nodeId>/
├── source/baseline[-<block>].png   # 主稿与各视觉块基准截图，一次写入不覆盖
├── source/asset-<node-id>.png      # 每个 image 的独立隔离证据，保留供 verify 消费
├── context.md                       # 块清单、主稿 viewport、目标栈验证命令、资产引用与 token/组件映射
├── assets-plan.json                 # 转换输入（image 必填 referencePng），batch/verify 消费
└── assets-manifest.json             # 资产映射，无素材时为 []
```

`t-figma-impl` 可先于 assets 启动：manifest 缺失时进入资产延后模式，块清单与实现只用资产语义引用（节点、名称、预期类型）占位，不下载、不伪造正式资产；交付前 assets 必须完成，impl 做一次绑定——把语义引用替换为真实 `outputPath`/`publicUrl`/`aspectRatio` 并重跑栈验证与素材 verify。manifest 已存在（含 `[]`）时可用于实现，交付仍须 verify。发现分块或数值理解有误时，直接更新 `context.md` 对应记录再修实现。

## 还原原则

- 目标项目代码、配置与 `AGENTS.md` 是当前约束；`source/` 是不可变视觉证据，MCP 返回的节点树不是 DOM。
- 截图定结构：按视觉边界与 stacking 划分 block，记录绝对定位、裁切、重叠与合成素材，不照搬 frame/group 层次；节点树只补尺寸、颜色、变量、文本等精确数值，不用截图目测代替。
- 优先映射项目已有组件、token、动效与响应式模式；只有视觉证据或现有代码支持时才修正 MCP 数值。
- 整页按块推进：单次 dispatch 只承担一个块或少量相邻小块，全部完成后交付人工验收。

## 资产 plan

`assets-plan.json` 是 `figma-assets.py batch` 的输入，结构为 `{"entries": [...]}`（无素材时为空数组）。每条必填非空字符串 `id`、`name`、`kind`、`source`、`outputPath`；`id` 与输出路径分别唯一，未知条目字段报错。

- `kind`: `image|svg|video`；`source` 为本地原始文件路径，所有相对路径按目标项目根（执行时的工作目录）解析。
- `origin`: `download-assets|url|local-file`，默认 `download-assets`，写入 manifest 的 `source`。
- `publicUrl`: 页面运行时 URL，video 必填，其余可选。
- image 必填非空字符串 `referencePng`：同节点 `get_screenshot(contentsOnly: true)` 的独立隔离 PNG 本地路径，包括不透明素材。可选 `flattened` / `lossless`（默认 false）、`quality`（1–100，默认 80）、`maxWidth`（非负整数，默认 0 不缩放）。这些 image 专属字段不用于 svg/video。`transparent`、`alphaMask`、`unbakeColor` 已从 plan 移除，旧字段按未知字段报错，不提供透明判定 override。

batch 在任何转换前检查全部来源和隔离证据、禁止输出覆盖输入，并默认拒绝覆盖已有输出。全部 image 先完成脚本判定，再执行转换：

1. 隔离 PNG 缺失报 `REFERENCE_REQUIRED`；放入 plan 同级可清理的 `raw/` 时报 `REFERENCE_NOT_PERSISTENT`。PNG 解码失败或格式错误阻断；全透明参考报 `REFERENCE_EMPTY`。源与参考的宽高比允许最多 1 像素取整误差，否则报 `REFERENCE_BOUNDS_MISMATCH`。独立参考不能与原导出使用同一路径。
2. `transparent` 由完整参考 alpha 最小值 `<255` 自动计算。即使源图已有 alpha，仍以参考 alpha 为准，避免不完整透明度通过；不透明参考同样强制校验。RGB PNG 的隐式 alpha 为 255。
3. RGB 比较缩采样到参考尺寸且最长边最多 256。参考不透明像素的逐通道平均绝对误差超过 4 时，报 `REFERENCE_RGB_MISMATCH`；半透明像素的 RGB 误差不超过 4 时保留原 RGB。否则用 `source = alpha * reference + (1-alpha) * background` 最小二乘拟合恒定底色，拟合仅使用 `0 < alpha <240` 的像素，不使用未定义的全透明 RGB。底色各通道需在 `[-4,259]`（取整并裁到 `[0,255]`），半透明像素拟合误差需不超过 4 且比原误差至少改善 2；否则报 `RGB_REPAIR_UNCERTAIN` 并停止，不猜常见底色。修复使用 `true = (baked-(1-alpha)*background)/alpha`，alpha 为 0/255 单独处理。
4. 参考 alpha 缩放后与高清 RGB 合并；原图 alpha 为 0 的位置没有有效 RGB，参考放大后若暴露这些位置，使用隔离参考颜色补齐，避免黑边。TinyPNG 压缩后，以 Pillow Lanczos 缩放到最终尺寸的完整参考 alpha 重新合并。WebP 终检逐像素要求 alpha 完全一致，否则报 `ALPHA_MISMATCH`，不以“存在一个透明像素”作为充分条件。

参考采集的 fileKey/nodeId 一致性由 MCP 调用方保证；脚本检查像素、边界和颜色一致性，不能认证文件的远端来源。数值误差阈值用于识别受支持的恒定底色烘焙，不代表任意渐变底色或复杂混合模式都能自动恢复；证据不确定时必须重新导出，不能降级放行。

全部转换、产物复验成功后才原子写 manifest（无素材为 `[]`），stdout 返回 `manifestPath`、`total`、`warnings`（透明问题阻断，不作为可忽略 warning；当前为空数组）。失败不写半成功 manifest，已有旧 manifest 不表示本次成功。执行与恢复见 `${CLAUDE_PLUGIN_ROOT}/guides/figma/assets.md`。

## 资产 manifest

`assets-manifest.json` 是 impl 引用资产的唯一映射，由 batch 写入；宽高与约分后的比例从最终产物提取，不从 CSS 或 Figma 标注推算。

```json
[
  {
    "id": "1:5",
    "name": "hero",
    "kind": "image",
    "source": "download-assets",
    "flattened": true,
    "transparent": true,
    "alpha": {
      "referencePath": ".ai/figma/example-1-2/source/asset-1-5.png",
      "referenceSha256": "<script-generated SHA-256>",
      "mode": "unbake",
      "unbakeColor": "1e1e1e"
    },
    "sha256": "<script-generated SHA-256>",
    "planEntrySha256": "<script-generated SHA-256>",
    "outputPath": "public/assets/hero.webp",
    "publicUrl": "/assets/hero.webp",
    "width": 1920,
    "height": 1080,
    "aspectRatio": "16/9"
  }
]
```

- `kind` 为 `image|svg|gif|video`；`source` 为 `download-assets|url|local-file`；`flattened` 标记含文字合成图，impl 作为单个媒体元素引用，不再实现其内文字。
- image 的 `transparent` 是脚本计算结果，不是 AI 意图声明；`true` 表示存在透明像素，`false` 表示全不透明。`alpha` 记录参考路径、文件 SHA-256、修复方式 `reference-alpha|unbake` 与自动推导的 `unbakeColor`（未去底色时为 null）。
- 所有条目都有最终文件 `sha256` 和 `planEntrySha256`；后者是原 plan 条目按键排序、UTF-8、无多余空格的 JSON SHA-256，用于发现输入变更。不得手写或修补这些证明字段。
- `publicUrl` 是页面运行时 URL，视频必填；名称语义化并沿用项目命名风格，不用节点 id、hash 或 Figma 默认层名。
- 视频必须有 MCP 返回的 URL 或 `--video-source` 来源；禁止用截图、GIF 或占位视频伪造。

## 验收

素材门禁由 `python ${CLAUDE_PLUGIN_ROOT}/scripts/figma-assets.py verify <plan>` 执行（目标项目根运行，`--manifest` 可指定路径）：plan 与 manifest 必须逐项对应，映射与 plan 摘要一致、输出文件 SHA-256 一致；每个 image 的持久化参考 SHA-256、完整输出 alpha、透明结果和尺寸也必须通过复验。成功 stdout 为 `{"manifestPath": "...", "total": 1, "verified": true}`，失败返回非零退出码。空 manifest 仅在 plan 也为空时通过；旧 manifest、已变更 plan 或已替换文件不能因路径存在而放行。verify 不读取 raw，便于清理后重跑；其不重新执行 RGB 拟合，通过摘要绑定已完成 batch 的产物。旧 plan/manifest 必须回到 assets 重新生成。

验收以人工为主，不派发审计 agent。impl 通过栈验证和素材门禁后即交付：报告实现范围、preview URL（如提供）与 baseline 截图位置，由开发者打开页面对照 baseline 自行验收。建议检查：块齐全、无明显错位/重叠、素材加载、视频可播放。

发现问题回到对应入口修复；像素级细微差异（几 px 间距、抗锯齿、字重微差）由开发者裁量，不必回炉。

## 失败规则

- MCP 核心能力、图片处理的 Pillow、ffmpeg/ffprobe 或目标栈缺失时，给出可操作提示并停止。
- 必要素材无法下载、视频无来源或候选素材有歧义时，不进入实现。
- 栈验证未通过或素材门禁未过时不得宣称完成。
