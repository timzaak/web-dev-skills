# Figma UI 还原契约

`/t-figma` 的运行时产物、真相源规则和 delta 收敛判据。只覆盖「Figma 设计稿 → 已有前端代码文件」的还原与测量验收，不替代 PRD、技术设计、任务拆分或前端实现规范。

**栈无关**：目标前端栈由 `context.md` 声明（React/Tailwind、Vue、Svelte、Next.js、Shopify Liquid、原生 HTML/CSS、PHP 等）。本契约不预设具体框架、构建工具或 dev server 形态。

## File Location

还原产物写入目标项目 `.ai/figma/<id>/`，不进入正式源码：

```text
.ai/figma/<id>/
├── spec.json          # Figma 规格快照，唯一 MCP 产物，迭代期零 MCP 依赖
├── baseline.png       # get_screenshot 基准图
├── context.md         # 已有代码上下文（token/动效/组件 + 栈声明）
├── conflicts.json     # 已确认的 spec 与项目 token 冲突（无冲突时为 []）
├── actual.png         # 实现后实际渲染截图
└── delta-report.json  # 测量 delta（最后一次）
```

验收报告：`.ai/quality/figma-restore-<feature>-<YYYYMMDD-HHMMSS>.md`。

`<id>` 取 `nodeId` 或 `fileKey-nodeId`，本次还原周期内不变。

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
```

规则：

- 「目标栈」必须先声明，后续章节按该栈表达。探测不出写 `unknown`，由人类补充。
- 章节缺失写「无」或「未检出」，不留空。
- 动效与组件必须给出来源路径，便于 agent 验证。

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

- **收敛成功**：FAIL / MISSING / ERROR 项均为零。MISSING（探针声明但页面未渲染）和 ERROR（探针异常）同样阻塞，因为测量不完整。
- **用尽迭代**：达到 `max-iterations`（默认 5）仍有阻塞项；产出报告交人类。
- WARN / CONFLICT 不阻塞，但必须在验收报告中列出。

## Convergence Loop

1. 还原 agent 编辑目标文件。
2. 测量脚本渲染页面，输出 `delta-report.json`。
3. 有 FAIL 项且未达 `max-iterations`：把 FAIL 项作为结构化文本喂回还原 agent，回到 1。
4. FAIL 清零或用尽迭代：产出验收报告。

回环禁止：把截图作为 diff 依据；重新调 Figma MCP；无 `max-iterations` 上限。

## Figma MCP Capability

优先官方 Dev Mode MCP：`get_metadata` / `get_design_context` / `get_screenshot` / `get_variable_defs`。

- 启动时探测工具是否注册；缺失即终止并提示安装，不静默降级。
- 社区 `talk-to-figma` 类 MCP（画布写入导向）不在支持范围。

## Robustness

t-figma 在不同目标环境下保持可用：

- **前端栈**：由 context 探测声明，不预设 React/Tailwind。token/动效/组件的扫描按探测到的栈适配（CSS vars / tailwind config / Liquid schema / theme 文件等）。
- **dev server**：形态由 context 声明（`npm run dev` / `shopify theme dev` / `php artisan serve` / 静态文件等）。脚本只接受一个可访问的 URL，不假设启动方式。
- **测量脚本**：`--cwd` 指向能 resolve `playwright` 的目录（可能是项目根、frontend 子目录或独立 e2e 目录）。缺失时清晰报错。
- **目标文件路径**：校验存在 + 在项目内 + 拒绝 `..`，但不限定具体目录名（不假设一定是 `frontend/src/**`）。

任何探测失败（栈、dev server、playwright）都不静默继续，而是终止并给出可操作的修复提示。
