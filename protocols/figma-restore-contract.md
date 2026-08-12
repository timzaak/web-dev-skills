# Figma UI 还原契约

`/t-figma` 的运行时产物、真相源规则和 delta 收敛判据。只覆盖「Figma 设计稿 → 已有前端代码文件」的还原与测量验收，不替代 PRD、技术设计、任务拆分或前端实现规范。

**栈无关**：目标前端栈由 `context.md` 声明（React/Tailwind、Vue、Svelte、Next.js、Shopify Liquid、原生 HTML/CSS、PHP 等）。本契约不预设具体框架、构建工具或 dev server 形态。

## File Location

还原产物写入目标项目 `.ai/figma/<id>/`，不进入正式源码：

```text
.ai/figma/<id>/
├── spec.json             # Figma 规格快照，迭代期的结构化对照基准
├── baseline.png          # get_screenshot 基准图
├── context.md            # 已有代码上下文（token/动效/组件 + 栈声明 + 资产目录）
├── conflicts.json        # 已确认的 spec 与项目 token 冲突（无冲突时为 []）
├── raw/                  # 从 MCP 临时 URL 下载的原始字节，中间产物，可手动清理
├── assets-manifest.json  # Figma 资产 → 最终 outputPath 映射，供实现与验收使用
├── actual.png            # 实现后实际渲染截图
└── delta-report.json     # 测量 delta（最后一次）
```

验收报告：`.ai/quality/figma-restore-<feature>-<YYYYMMDD-HHMMSS>.md`。

`<id>` 取 `nodeId` 或 `fileKey-nodeId`，本次还原周期内不变。

最终资产落在 `context.md` 声明的项目正式资产目录；`.ai/figma/<id>/raw/` 只缓存 MCP 临时 URL 对应的原始字节，迭代期不重新调用 MCP。

## Source of Truth

- Figma 设计稿是视觉真相源；`spec.json` 是它的固化快照。
- `context.md` 声明目标栈与既有资源；还原必须复用其中声明的 token/动效/组件，不引入新依赖。
- `spec.json` 与 `context.md` 冲突时（如 Figma 13px，项目 token 只有 12/16）：优先 project token，并把机器可读条目写入 `conflicts.json`；测量后 delta-report 标记 `CONFLICT`，由人类裁决。
- 还原迭代以 `spec.json` 为对照基准，不重新调 MCP（避免上下文漂移和额外配额消耗）。

## spec.json Structure

```json
{
  "source": { "fileKey": "abc123", "nodeId": "1:2", "url": "https://..." },
  "viewport": { "width": 320, "height": 720, "deviceScaleFactor": 1 },
  "stack": { "framework": "auto", "detected": "react/tailwind" },
  "tokens": {
    "colors": [{ "name": "primary/500", "value": "#1d4ed8" }],
    "spacing": [{ "name": "space-4", "value": "16px" }],
    "font": [{ "name": "text-base", "fontSize": 16, "lineHeight": "24px" }]
  },
  "nodes": [
    { "id": "1:2", "name": "Card", "type": "FRAME",
      "layout": { "width": 320, "height": 48, "padding": 16, "gap": 8 },
      "typography": { "fontSize": 16, "fontWeight": 600, "lineHeight": "24px" },
      "fill": "#ffffff", "children": [] }
  ],
  "assets": [
    { "id": "1:5", "name": "hero-background", "kind": "image",
      "source": "design-context", "rawPath": ".ai/figma/<id>/raw/hero-background.png" }
  ],
  "probeSelectors": [
    { "name": "title", "selector": "[data-figma='title']", "expect": { "fontSize": 24, "fontWeight": 600 } }
  ]
}
```

规则：

- `source` 不写时间元数据（以 `${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md` 为准）。
- `stack.framework` 默认 `auto`，由 context 提取阶段探测并回填 `stack.detected`；探测失败时为 `unknown`，还原 agent 需在 context 中人工声明。
- `probeSelectors` 是测量探针声明。selector 优先用 `data-figma='<name>'` 属性（栈无关、稳定）；缺失时回退到目标栈可用的结构化选择器。
- `viewport` 固化设计节点对应的浏览器视口；缺失时测量脚本回退到根节点布局尺寸，再回退到 `1280×900`。响应式页面不得忽略该字段。
- 每个 probe 的 `name` 必须唯一，`selector` 和 `expect` 必须非空，`expect` 仅使用 Delta Thresholds 中声明的属性。
- `assets` 只记本次实现需要的资产；`kind` ∈ `image|svg|gif`，`source` ∈ `design-context|download-assets`。`rawPath` 指向规格提取阶段已下载的原始字节，最终路径由 `assets-manifest.json` 声明。
- Figma 视频不在自动资产能力范围内；设计依赖视频时必须在实现前由人类提供可用源或项目 CDN 地址，不得伪造、截图替代或假定 `download_assets` 能取得原视频。

## Asset Processing

资产获取属于规格提取阶段（stage 2），必须与 `get_design_context` / `get_screenshot` 在同一 MCP 窗口内完成，之后零 MCP：

1. 优先使用 `get_design_context` 返回的资产 URL；URL 是临时引用，立即下载原始字节到 `.ai/figma/<id>/raw/`，不得把临时 URL 写进正式代码。
2. 仅当 design context 没有给出所需资产，或需要节点导出格式时，才在 **remote MCP 可用时**调用可选的 `download_assets`；它返回的仍是临时 URL，必须显式下载。
3. stage 3 按 context 的目录、命名和引用方式把原始字节复制到正式资产目录。默认不转码、不重绘 SVG、不添加图标包；项目 `DESIGN.md` 若存在，只作为项目级覆盖约定。
4. 正式路径已存在时先计算 SHA-256：内容相同则复用，内容不同则停止并请人类选择，禁止静默覆盖。

工具不可用时按需降级：缺少可选 `download_assets` 不影响已有 asset URL；没有资产时不创建 `raw/`，但仍写空 manifest。

## assets-manifest.json Structure

stage 3 资产落位后写入；它是还原 agent 引用资产和验收资产完整性的唯一清单：

```json
[
  {
    "id": "1:5",
    "name": "hero-background",
    "kind": "image",
    "source": "design-context",
    "outputPath": "public/assets/hero-background.png",
    "sha256": "<64 lowercase hex chars>"
  }
]
```

规则：

- `id + name` 唯一定位；`id` 与 `spec.json.assets[].id` 对应。
- **`name` 必须语义化**：描述资产是什么或其用途（如 `hero-background`、`product-card-icon`、`logo-primary`、`onboarding-loop`），用英文，按 context「命名约定」规范化大小写/分隔符。`outputPath` 文件名由 `name` 决定。
  - 来源优先级：① Figma 节点图层名（若语义化，清洗非法字符后直接用）；② 节点名是无意义默认（`Frame 12` / `Rectangle 3` / `Image` / `Vector` 等）→ 从节点角色 + 父级上下文派生（如父 frame `ProductCard` 里的图标 → `product-card-icon`）；③ 仍无法判断 → 终止问用户，不臆造。
  - 禁止用节点 id（`1:5`）、序号计数（`image-1`）、纯 hash、无意义默认名作为最终文件名。
  - 项目构建期的 contenthash（webpack/vite 产物）属构建变换，不作为源资产命名；源文件名仍语义化。
- `outputPath` 是相对项目根的正式资产路径，由 context.md「资产目录与命名约定」+ 本规则 `name` 决定。
- `sha256` 是最终文件的 SHA-256，用于验收完整性与防止覆盖已有同名资产；默认不转码时也必须与 `rawPath` 对应文件一致。
- 无资产节点时写 `[]`。
- manifest 只记录成功落位的资产；下载失败、视频源缺失、同名内容冲突都会阻塞进入实现阶段，不写半成功条目。
- `raw/` 是中间产物，可在流程结束后手动清理；manifest 不承诺 `raw/` 长期存在。

## conflicts.json Structure

```json
[
  {
    "name": "card",
    "prop": "padding",
    "spec": 13,
    "projectValue": 16,
    "token": "space-4",
    "reason": "项目没有 13px spacing token"
  }
]
```

`name + prop` 唯一定位冲突。还原 agent 负责写入和清理；实际值重新与 spec 完全一致时，测量结果仍为 PASS。`CONFLICT` 不阻塞技术收敛，但必须进入验收报告等待人类裁决。

## context.md Structure

markdown 文档，面向还原 agent 直接阅读。固定章节：

```markdown
# 已有代码上下文

## 目标栈
- framework: <react/tailwind | next | vue | svelte | liquid | html | php | unknown>
- 目标文件: <path>
- dev server: <启动命令 或 URL>（测量阶段需要）

## Design Token
- 来源: <tailwind.config | CSS vars | theme.liquid | :root | ...>
- spacing / color / font: ...

## 动效模式
- 来源: <transition 定义位置>
- 过渡默认值 / @keyframes / 动效库变体: ...

## 可复用组件
- <Card> — 路径、props、适用场景
- <Button> — ...

## 资产目录与命名约定
- 目录: <public/assets | src/assets | assets/ | CDN>
- 命名约定: <kebab-case | snake_case>（大小写/分隔符风格；基础名必须语义化，见 `assets-manifest.json Structure` 命名规则）
- 引用方式: <相对路径 | 绝对路径 | import | CDN URL>
```

规则：

- 「目标栈」必须先声明，后续章节按该栈表达。探测不出写 `unknown`，由人类补充。
- 章节缺失写「无」或「未检出」，不留空。
- 动效与组件必须给出来源路径，便于 agent 验证。
- 「资产目录与命名约定」依次取项目 `DESIGN.md`（若存在）、目标文件邻近用法、框架约定。只有存在多个合理位置且无法判断时才请人类声明；无资产时写「不适用」。

## Delta Thresholds

测量以 `spec.json.probeSelectors` 为探针，脚本输出每项的 spec / actual / delta / status。

| 属性类别 | PASS | WARN | FAIL |
|---|---|---|---|
| 数值（fontSize/width/height/padding/margin/gap/borderRadius） | delta < 2px | 2 ≤ delta < 4px | delta ≥ 4px |
| 颜色（CSS hex/rgb/rgba，含 alpha） | 完全匹配 | — | 不匹配 |
| 时序（transition/animation duration） | 完全匹配 | delta < 50ms | delta ≥ 50ms |
| 枚举（font-weight/opacity/lineHeight） | 完全匹配 | — | 不匹配 |

已在 `conflicts.json` 声明且实际值仍与 spec 不同的项目标记为 `CONFLICT`，不计入 FAIL。

收敛判据：

- **收敛成功**：FAIL / MISSING / ERROR 项均为零，且 manifest 资产的路径、SHA-256、页面加载检查均通过。MISSING（探针声明但页面未渲染）和 ERROR（探针或资产异常）同样阻塞，因为验收不完整。
- **用尽迭代**：达到 `max-iterations`（默认 5）仍有阻塞项；产出报告交人类。
- WARN / CONFLICT 不阻塞，但必须在验收报告中列出。

## Convergence Loop

1. 还原 agent 编辑目标文件。
2. 验收 agent 校验资产完整性并运行测量脚本，输出 `delta-report.json`。
3. 有 FAIL 项且未达 `max-iterations`：把 FAIL 项作为结构化文本喂回还原 agent，回到 1。
4. FAIL 清零或用尽迭代：产出验收报告。

回环禁止：把截图作为 diff 依据；重新调 Figma MCP；无 `max-iterations` 上限。

## Figma MCP Capability

优先官方 Figma MCP：`get_metadata` / `get_design_context` / `get_screenshot` / `get_variable_defs`；remote MCP 可选 `download_assets`。

- 核心工具缺失即终止并提示安装，不静默降级。
- `download_assets` 是 remote-only 可选能力，仅在确有导出需求时探测和调用；其临时 URL 必须在 stage 2 下载，不能直接写入正式代码。
- 社区 `talk-to-figma` 类 MCP（画布写入导向）不在支持范围。

## Robustness

t-figma 在不同目标环境下保持可用：

- **前端栈**：由 context 探测声明，不预设 React/Tailwind。token/动效/组件的扫描按探测到的栈适配（CSS vars / tailwind config / Liquid schema / theme 文件等）。
- **dev server**：形态由 context 声明（`npm run dev` / `shopify theme dev` / `php artisan serve` / 静态文件等）。脚本只接受一个可访问的 URL，不假设启动方式。
- **测量脚本**：`--cwd` 指向能 resolve `playwright` 的目录（可能是项目根、frontend 子目录或独立 e2e 目录）。缺失时清晰报错。
- **目标文件路径**：校验存在 + 在项目内 + 拒绝 `..`，但不限定具体目录名（不假设一定是 `frontend/src/**`）。
- **资产目录**：优先沿用项目约定；只有存在资产且目录选择确实有歧义时才请求人类声明。
- **资产覆盖**：同名同 hash 复用，同名异 hash 阻塞，绝不静默覆盖项目文件。

任何必要探测失败（栈、dev server、playwright、存在资产时无法确定目录）都不静默继续，而是终止并给出可操作的修复提示。
