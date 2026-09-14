# Figma UI 工程工作流契约

本契约是 `/t-tools:t-figma-assets`、`/t-tools:t-figma-impl`、`/t-tools:t-figma-fix`、`/t-tools:t-figma-ux` 与内部 Figma agents 的共享真相源。它覆盖目标项目中的工作区关联、Figma 原始快照、资产清单、动效规格、规则记忆和验收门禁。

## Command Contract

```text
/t-tools:t-figma-assets <figma-url> <target-file> [--asset-url <figma-node-url> ...] [--video-source <node-id>=<url-or-local-path> ...]
/t-tools:t-figma-impl <figma-url> <target-file> <preview-url>
/t-tools:t-figma-fix <figma-node-url> <target-file> <preview-url> <问题、状态或断点描述>
/t-tools:t-figma-ux <figma-url> <target-file> <preview-url>
```

- `<target-file>` 必须已存在、位于目标项目内且路径中不得含 `..`。
- `<preview-url>` 是 impl/fix/ux 的必填输入：用户提供的可访问页面 URL。缺失时 `AskUserQuestion` 补齐一次，仍无则停止。入口与 agent 不得启动、探测端口或猜测 dev server；URL 不可达时停止并请用户确认 URL 与 dev server 状态。assets 无页面验收，不需要。
- `figma-url` 必须能解析 `fileKey` 与 `nodeId`。assets/impl 的 URL 指向整页或主 frame；fix 的 URL 指向待精修节点。
- 四个命令以规范化后的项目相对 `target-file` 关联工作区。一个目标文件同时命中多个活动工作区时必须请开发者选择，不得按时间或目录顺序猜测。
- assets/impl 命中 session 后必须校验 URL 的 `fileKey + mainNodeId` 一致；不一致时请开发者选择归档旧 session 或回到原主稿，不得复用旧 session 产物。fix/ux 附着时允许 nodeId 不同，但 fileKey 必须与 session 一致。
- `t-figma-impl` 要求 assets 阶段已经完成；无素材页面也必须存在空的 `assets-manifest.json`。
- `t-figma-fix` 要求目标节点已有代码实现，但不要求运行过 `t-figma-impl`：可附着同 fileKey 的既有 session，也可为手写或其他方式产生的实现创建独立 fixing session，并生成局部二次规格；不承担从零整页实现。
- `t-figma-ux` 是独立的动效精修入口，不要求 assets/impl 先行：URL 可指向整页或待精修节点，只精修该范围内的动效交互，不修复静态视觉偏差（impl/fix 职责），不下载素材。目标文件必须已有对应实现（无论来自 impl 还是手写）。

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
    │   ├── motion-context.md
    │   ├── variables.json
    │   └── baseline[-<node-name>].png
    ├── raw/
    ├── motion.json
    ├── context.md
    ├── assets-manifest.json
    ├── rule-candidates.md
    └── actual.png
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
- session 脚本仅发现旧 `memo/figma/` 时，将其整体迁移到 `.ai/figma/` 后继续；新旧目录同时存在时必须停止并要求开发者显式合并，不得静默覆盖。
- `status` 只允许 `active|archived`。一个 target 只有一个 active session 时按各入口复用条件处理；零个时 assets/ux 可创建，impl 因缺少已完成的 assets session 必须停止，fix 在确认目标节点已有实现后可创建；多个时必须询问。
- `session.json` 保存主 URL、fileKey、mainNodeId、targetFile 和当前 stage（`assets|implemented|motion|fixing|accepted`）。状态文件不写时间元数据。

### Session Resolve

各入口开始时调用 `${CLAUDE_PLUGIN_ROOT}/scripts/figma-session.py resolve` 校验并规范化 target-file，并严格按下表处理；不得按时间或目录顺序猜测 session，也不得越过入口自身前置条件：

| resolve 结果 | assets | impl | fix | ux |
|---|---|---|---|---|
| 唯一 active 且满足入口复用/附着条件 | fileKey/mainNodeId 一致时复用 | fileKey/mainNodeId 一致时复用，并校验 `assets-manifest.json` | fileKey 一致时附着；nodeId 可不同，复用其中实际存在的产物 | fileKey 一致时附着；nodeId 可不同 |
| 唯一 active 但不满足入口复用/附着条件 | fileKey/mainNodeId 不一致时询问；确认后 `archive` 旧 session 再 `create` | fileKey/mainNodeId 不一致时停止；提示回到匹配主稿，或先对新主稿运行 assets；不得由 impl 归档或创建 session | fileKey 不一致时询问开发者回到匹配设计，或归档旧 session 后创建新 fixing session；不得擅自复用或归档 | fileKey 不一致时询问 |
| 无 active session | 以主 URL `create` | 停止并提示先运行 assets | 确认目标节点已有代码实现后，以 node URL `create --stage fixing` | `create --stage motion` |
| 多个 active（ambiguous） | `AskUserQuestion` 选择 | `AskUserQuestion` 选择；所选 session 仍须通过 fileKey/mainNodeId 与 manifest 门禁 | 询问选择 | 询问选择 |

## Source of Truth and Reconstruction

1. 目标项目代码、配置及 `AGENTS.md`/`CLAUDE.md` 是当前实现与执行约束。
2. `docs/figma-rules.md` 是已验证的项目级 Figma 长期规则。
3. `source/` 是 MCP 提取窗口内取得的不可变原始证据；不得在调试中覆盖。
4. `rule-candidates.md` 是当前 session 的候选经验，不自动凌驾于代码或长期规则。

`get_metadata`/`get_design_context` 返回的是画布结构与设计表达：层次深、绝对坐标、不对应 DOM 语义，不视为可靠 DOM。二次重建以截图为主证据：

- 截图定结构：以视觉边界和 stacking 识别实际 block，不机械照搬 frame/group 层次；
- 节点树补数值：尺寸、颜色、变量、文本等精确事实取自 MCP，不用截图目测代替；
- 主稿证据（metadata、design context、variables、baseline）在 impl 的 MCP 窗口保存到 `source/`，一次写入后不得覆盖；fix/ux 只追加各自节点证据，不覆盖既有快照；
- 记录绝对定位、裁切、重叠、背景和最小视觉组合；
- 优先映射项目已有组件、token、动效和响应式模式；
- 只有视觉证据或现有代码支持时才修正 MCP 数值，不得凭空创造隐藏状态。

视觉块划分、组件映射与主稿 viewport 写入 `context.md`，不生成独立规格文件；资产引用以 manifest 为准。发现分块或数值理解有误时，直接更新 `context.md` 对应记录再修实现。

整页实现按视觉块推进：先分块并为每块保存 baseline 截图，再按文档顺序逐块实现（单次 dispatch 只承担一个块或少量相邻小块），全部块完成后做整页验收。

### Fix Attachment and Bootstrap

- 命中同 fileKey 的 active session 时，fix 附着并复用其中实际存在的 source、context、manifest 和 candidates；nodeId 可以不同，不得要求这些产物必须由 impl 生成。
- 无 active session 时，fix 只有在 URL 对应范围已有代码实现时才以 `create --stage fixing` 创建独立 session；没有实现则停止，不得扩大为整页实现。
- 缺少 `context.md` 时，fix 从项目和目标区域代码生成。fix 只对目标节点调用 MCP 取证据，保存为 `source/baseline-<node-name>.png`，不覆盖既有快照；当前代码就是修复前基线，不要求 impl 历史。
- 无已准备素材时允许写空 `assets-manifest.json`，表示本次 fix 不引入资产；若修复需要新增、替换或加工素材，必须先运行 assets，不得用空 manifest 绕过资产门禁。
- fix 进入修改前 stage 设为 `fixing`；验收收敛后设为 `accepted`，未收敛保持 `fixing`。

## Asset Discovery and Processing

### Discovery

- 收集主节点内的图片/视频节点；不足时用无 nodeId 的 `get_metadata` 枚举同文件 pages，按节点名、类型和尺寸筛选候选。
- `--asset-url` 是显式补充来源，优先级高于自动匹配；跨 Figma 文件不自动扫描，必须显式提供节点 URL。
- 候选无法唯一匹配时列出 node id、page、名称、尺寸和截图证据询问，不得选择“看起来最像”的素材。

### Composite Assets

含文字的图片默认导出包含图片和文字的最小共同视觉父节点，manifest 标 `flattened: true`，impl/fix 不再重复实现其内文字。文字涉及交互、动态数据、本地化或独立无障碍语义时，先请开发者裁决。

### Images

- 图片、图标和合成父节点通过 Figma MCP `download_assets` 导出，不得使用 `get_design_context` 返回的素材 URL 代替下载；`defaultScale` 默认 3，仅明确的小型非关键图标或装饰用 2。
- 临时 URL 立即下载到 session `raw/`，不得写入正式代码；manifest 条目 `source` 记录为 `download-assets`。
- PNG/JPEG 转 WebP：照片 quality 100，透明图和 `flattened: true` 合成图 lossless；SVG、已有 WebP 和 GIF 直接保留。项目长期规则可覆盖默认策略。
- 使用 ffprobe 提取最终宽高，以最大公约数记录 `aspectRatio`。
- assets 阶段不编辑 UI 源码；impl/fix 根据 manifest 引用资产并写入真实 aspect-ratio。

### Video

- 视频源可以是 MCP 明确返回的临时 URL、`--video-source` URL 或项目内本地文件。官方 MCP 无原始视频时必须要求补充来源，禁止用截图、GIF 或占位视频伪造。
- 最终视频使用 MP4：H.264、AAC（存在音轨时）、`yuv420p`、CRF 23、medium preset、AAC 128k、`+faststart`；保持源尺寸，奇数宽高向下调整为偶数。
- ffprobe 必须验证容器、codec、pixel format 和尺寸；检查 `moov` 位于 `mdat` 前。
- 页面验收对视频 URL 发 `Range: bytes=0-1`，必须得到 `206` 和有效 `Content-Range`。faststart 通过但服务器无 Range 仍阻塞“流式播放”验收。

### Manifest

`assets-manifest.json` 是 impl/fix 引用资产和 accept 校验完整性的唯一映射：

```json
[
  {
    "id": "1:5",
    "name": "hero",
    "kind": "image",
    "source": "download-assets",
    "flattened": true,
    "outputPath": "public/assets/hero.webp",
    "publicUrl": "/assets/hero.webp",
    "sha256": "<64 lowercase hex>",
    "width": 1920,
    "height": 1080,
    "aspectRatio": "16/9"
  }
]
```

- `kind` 允许 `image|svg|gif|video`；`source` 允许 `download-assets|url|local-file`；`flattened` 仅含文字合成图标记。
- `publicUrl` 是页面运行时 URL；视频必填（验收时用于在浏览器中定位并播放检查），图片按目标栈需要填写。
- 名称语义化并沿用项目命名风格；禁止节点 id、hash 和 Figma 默认层名作为最终文件名。
- 同名同 SHA-256 复用；同名异内容必须停止，请开发者改名或明确允许替换。
- 全部条目成功后原子性写入，失败不写半成功条目；脚本 `image|video` 的 JSON 输出即条目数据来源。
- `raw/` 只是转换前的中转缓存：manifest 写入成功后即删除整个 session `raw/`；需要重新导出时重新调用 `download_assets` 下载，不依赖 raw 的持久性。

## Motion and Interaction

`t-figma-ux` 产出 session `motion.json`，作为动效交互的当前基准。

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

- `trigger` 允许 `hover|focus|press|click|enter|exit|scroll|state`；`kind` 允许 `transition|animation|spring`。
- 附着与独立两种模式：命中同 fileKey 的 active session 时附着，复用其 context/candidates 与规则记忆；无 active session 时以 `create --stage motion` 独立创建，session 只承载动效产物。ambiguous 时必须询问，不得按顺序猜测。
- 原型证据：附着模式优先从既有 `source/design-context.md` 读取；独立模式或既有快照无原型信息时，在 MCP 窗口提取并保存为 `source/motion-context.md`，不覆盖既有快照。
- `easing` 统一记录 CSS computed 形式，Figma 名称映射见 `${CLAUDE_PLUGIN_ROOT}/guides/figma/motion.md`。spring 无 CSS 等价，`easing` 记录 `{stiffness, damping, mass}` 参数对象，验收靠实现声明与人工复核。
- `origin` 允许 `prototype|project-pattern|principle-default|user-decision`。`prototype` 和 `project-pattern` 必须附 evidence；`principle-default` 仅限不影响用户流程感知的微反馈；首屏转场、跨页转场、破坏性操作反馈等缺口必须取得开发者裁决后标 `user-decision`。
- 动效验收以触发观察为主：accept 按 `motion.json` 触发交互，确认前后状态变化与 `prefers-reduced-motion` 替代；时长/缓动手感无法目视判定的列入人工复核。同一元素存在多个不同 duration/easing 的过渡时，实现必须收敛为单一动效声明。独立模式写空 `assets-manifest.json` 保持 accept 前置一致。
- 每个含位移或持续循环的 interaction 必须声明 `reducedMotion` 替代方式；替代是否生效由 ux agent 在栈验证中检查并在 accept 报告中列出证据。
- stage：附着模式进入时设为 `motion`，独立模式创建即 `motion`；验收收敛后设为 `accepted`，未收敛保持 `motion` 并回环，达上限 `EXHAUSTED`。

## Project Rule Memory

impl/fix/ux 开始前读取目标代码、`docs/figma-rules.md` 和当前 session 候选；fix 还必须读取问题描述与当前区域代码。assets 是纯机械阶段，不参与规则记忆。

候选格式使用“观察 / 证据 / 建议规则 / 验证状态”。只有同时满足以下条件才可晋升：

1. 当前实现已通过 accept，或开发者明确确认；
2. 规则由项目现有代码支持，或已在至少两个不同节点/页面复用；
3. 不与更高优先级项目事实冲突；
4. 能凝练为一句“适用条件 → 执行动作”，不含选择器、单次像素值或页面专属补丁。

`docs/figma-rules.md` 最多 10 条活动规则，按结构、素材、响应式、局部精修分组。相同规则合并；新证据用于改写旧规则而不是追加。达到上限、证据不足或冲突的候选留在 session，并在报告列出。

## Measurement and Acceptance

验收是目视比对，不做数值测量。`figma-accept` 用 Chrome MCP 打开 preview URL 截图，与 session 的 baseline 截图逐块比对，检查运行状态，输出结构化结论；编排主链路只消费该结论。

- 按 `context.md` 记录的主稿 viewport 呈现；局部 fix 只比对 `scopeSelector` 对应区域，使用该节点的 baseline 截图。
- 阻塞问题：块缺失、结构错乱、明显错位或重叠、素材损坏或加载失败、视频无法播放、reduced-motion 替代缺失。
- 像素级细微差异（几 px 间距、抗锯齿、字重微差）不阻塞，进报告人工复核；不得只凭模糊印象改任意数值。
- `max-iterations` 默认 5，轮次由编排入口计数；达到上限仍未收敛则 `EXHAUSTED`。
- accept 只写 `.ai/figma/**` 截图和 `.ai/quality/figma-*.md` 报告，不修改代码、正式资产或长期规则。

## Failure Rules

- MCP 核心能力、Chrome MCP、ffmpeg/ffprobe 或栈缺失，或 preview URL 不可达时给出可操作提示并停止。
- 原始快照不完整、必要素材无法下载、视频无来源、候选素材有歧义或同名内容冲突时，不进入实现。
- 动效缺口影响用户流程感知或品牌调性而开发者未裁决时，不得用原则默认继续；spring 动效缺项目动效库支撑时停止询问。
- 规则冲突不得静默覆盖；报告冲突来源并等待开发者裁决。
- impl/fix 验证失败时不得宣称收敛；accept 不得代替实现 agent 修代码。
