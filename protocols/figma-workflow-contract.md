# Figma UI 工程工作流契约

`t-figma-assets`、`t-figma-impl`、`t-figma-ux` 与 Figma agents 的共享契约：命令入参、工作目录、资产 manifest、动效规格与验收判定。

## 命令

```text
/t-tools:t-figma-assets <figma-url> <target-file> [--asset-url <figma-node-url> ...] [--video-source <node-id>=<url-or-local-path> ...]
/t-tools:t-figma-impl <figma-url> <target-file> <preview-url>
/t-tools:t-figma-ux <figma-url> <target-file> <preview-url>
```

- `target-file` 必须已存在、位于目标项目内且路径不含 `..`。
- `preview-url` 可选，仅在交付报告中回显；页面验收由开发者自行完成，入口不得启动或探测 dev server。
- `figma-url` 必须能解析 `fileKey` 与 `nodeId`；assets/impl 指向整页或主 frame，ux 可指向整页或待精修节点。

## 工作目录

三个命令共享 `.ai/figma/<fileKey>-<nodeId>/`：同一主稿 URL 即同一目录，由首个入口创建，无注册表、无状态文件。

```text
.ai/figma/<fileKey>-<nodeId>/
├── source/baseline[-<block>].png   # 主稿与各视觉块基准截图，一次写入不覆盖
├── context.md                       # 块清单、主稿 viewport、目标栈验证命令、资产引用与 token/组件映射
├── assets-plan.json                 # 转换声明（image 条目必填 transparent），batch 输入，成功后保留
├── assets-manifest.json             # 资产映射，无素材时为 []
└── motion.json                      # 动效基准，仅 t-figma-ux
```

`t-figma-impl` 可先于 assets 启动：manifest 缺失时进入资产延后模式，块清单与实现只用资产语义引用（节点、名称、预期类型）占位，不下载、不伪造正式资产；交付前 assets 必须完成，impl 做一次绑定——把语义引用替换为真实 `outputPath`/`publicUrl`/`aspectRatio` 并重跑栈验证。manifest 已存在（含 `[]`）时直接引用。发现分块或数值理解有误时，直接更新 `context.md` 对应记录再修实现。

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
- image 必填布尔 `transparent`；可选 `alphaMask`（隔离 PNG 路径）、`unbakeColor`（背景色 hex）、`flattened` / `lossless`（默认 false）、`quality`（1–100，默认 80）、`maxWidth`（非负整数，默认 0 不缩放）。这些 image 专属字段不用于 svg/video。

batch 在转换前校验来源/mask 存在、输出不重复且默认不覆盖已有文件。透明数据由代码判定：ffprobe 确认 alpha 通道，FFmpeg 检测像素 alpha 最小值 `<255`（WebP 解码不兼容时回退 Pillow）。`transparent: true` 且源图无透明像素、未提供 mask 时，以 `ALPHA_MASK_REQUIRED` 和条目 id 阻断；检测失败不归类为缺 mask。声明 `false` 却有透明像素时报告 warning。全部转换成功后才原子写 manifest（无素材为 `[]`），stdout 返回 `manifestPath`、`total`、`warnings`；失败不写半成功 manifest。执行、warning 复核和恢复方法见 `${CLAUDE_PLUGIN_ROOT}/guides/figma/assets.md`。

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
    "outputPath": "public/assets/hero.webp",
    "publicUrl": "/assets/hero.webp",
    "width": 1920,
    "height": 1080,
    "aspectRatio": "16/9"
  }
]
```

- `kind` 为 `image|svg|gif|video`；`source` 为 `download-assets|url|local-file`；`flattened` 标记含文字合成图，impl 作为单个媒体元素引用，不再实现其内文字。
- `transparent` 记录 image 的透明意图；为 `true` 时，脚本已终检输出有 alpha 通道且有透明像素；`false` 不保证输出完全不透明。
- `publicUrl` 是页面运行时 URL，视频必填；名称语义化并沿用项目命名风格，不用节点 id、hash 或 Figma 默认层名。
- 视频必须有 MCP 返回的 URL 或 `--video-source` 来源；禁止用截图、GIF 或占位视频伪造。

## 动效规格

`t-figma-ux` 产出 `motion.json`：

```json
{
  "version": 1,
  "interactions": [
    {
      "id": "nav-drawer-open",
      "trigger": "click",
      "selector": ".nav-drawer-trigger",
      "motion": {
        "kind": "transition",
        "durationMs": 240,
        "easing": "cubic-bezier(0.42, 0, 0.58, 1)",
        "properties": ["transform"]
      },
      "origin": "prototype",
      "evidence": "design context: reaction -> SMART_ANIMATE 240ms EASE_IN_OUT",
      "reducedMotion": "fade"
    }
  ]
}
```

- `trigger` 为 `hover|focus|press|click|enter|exit|scroll|state`；`kind` 为 `transition|animation|spring`。
- `origin` 为 `prototype|project-pattern|principle-default|user-decision`；前两者必须附 `evidence`；首屏/跨页转场、破坏性操作反馈等影响用户流程感知的缺口必须开发者裁决后标 `user-decision`，不得静默套用默认。
- 原型数据在 MCP 窗口内提取并消费，结论记入 `evidence`，不落盘。
- `easing` 记 CSS computed 形式，Figma 名称映射见 `${CLAUDE_PLUGIN_ROOT}/guides/figma/motion.md`；spring 无 CSS 等价，记录 `{stiffness, damping, mass}` 并依赖项目动效库。
- 含位移或持续循环的 interaction 必须声明 `reducedMotion` 替代方式。

## 验收

验收以人工为主，不派发审计 agent。impl/ux 通过栈验证和素材门禁后即交付：报告实现范围、preview URL（如提供）与 baseline 截图位置，由开发者打开页面对照 baseline 自行验收。建议检查：块齐全、无明显错位/重叠、素材加载、视频可播放、`motion.json` 声明的交互触发后有状态变化。

发现问题回到对应入口修复；像素级细微差异（几 px 间距、抗锯齿、字重微差）由开发者裁量，不必回炉。

## 失败规则

- MCP 核心能力、ffmpeg/ffprobe 或目标栈缺失时，给出可操作提示并停止。
- 必要素材无法下载、视频无来源、候选素材有歧义或动效缺口未经裁决时，不进入实现。
- 栈验证未通过或素材门禁未过时不得宣称完成。
