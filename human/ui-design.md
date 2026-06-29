# 前端 UI 探索能力设计说明（design-shotgun 适配方案）

本文是 `t-ui-design` 的设计背景说明。该能力已落地为：

- skill：`skills/t-ui-design/SKILL.md`
- subagent：`agents/ui-design.md`
- 共享契约：`protocols/ui-design-contract.md`

它记录本项目如何适配类似 gstack `/design-shotgun` 的前端 UI 探索能力：多方案生成 → 并排对比 → 反馈迭代 → 收敛定稿。

目标是说明设计意图和现有结构如何对齐，后续修改应优先更新 skill、agent 和 protocol 中的正式契约。

## 它解决什么问题

当前流程里，前端 UI 只有两个落点，都不做"方案探索"：

- `t-design` 的前端章节只产出**单一方案**的文本线框（页面/路由/组件清单 + 线框说明）。它假定方向已经确定，只把确定的方向描述清楚。
- `t-html-show` 的 `interactive-preview` 是把**已经定下来的设计**可视化成一份 HTML，供人类审阅，不是多方案对比。

缺的是 gstack `/design-shotgun` 那一段：在方向还没定死之前，并行产出 4-6 个不同设计方向，并排给人看，收集偏好，迭代几轮，最后收敛到一个 winner。这一步的价值是**用看代替描述**——用户说不清"我想要什么"，但能在几个具体方案里挑出"哪个更对"，并指出"再留白一点""标题更大""去掉渐变"。

补上这一段后，前端 UI 的决策从"AI 写一段线框文字，人凭想象判断"变成"AI 产出几个可见方案，人直接比较和取舍"，更早暴露方向偏差。

## 为什么不照搬 gstack

gstack 的 `/design-shotgun` 用 GPT Image 生成图片 mockup，再用 `/design-html` 把选中的图片转成可上线 HTML。直接照搬会和本项目冲突：

- **目标栈不同**：本项目是 React + TanStack + Tailwind + Radix UI，不是 gstack 的裸 HTML / Pretext。图片 mockup 离真实组件远，转译成本高。
- **约定不同**：本项目的 Preview 产物写入 `.ai/preview/` 并服务于审阅闭环，不假设有图像生成 API 或密钥。引入 GPT Image 会改变产物来源和验收方式。

因此变体应该用 **HTML/CSS mockup**（单文件 HTML，可用 Tailwind 风格的 class），而不是图片。这反而是一个优势：HTML mockup 离真实 React 实现最近，winner 选定后几乎能直接映射成组件结构，比图片 mockup 更能指导开发，也不需要任何外部 API。

## 已落地的 skill 形态

- **名称**：`t-ui-design`，遵循 `t-*` 命名，命令式入口、手工触发，不被模型自动触发。
- **位置**：`/t-prd-check` 通过之后、`/t-design` 之前或并行。仅当 feature 有显著前端 UI 时才跑；纯后端、纯技术方案跳过。
- **职责边界**：只做 UI 方案探索和收敛，产出 UI 设计规格。不写技术设计（仍是 `t-design`）、不拆任务（仍是 `t-task`）、不写真实组件代码（仍是 `t-run`）。即不越界做 gstack `/design-html` 那种直接生成可上线代码的环节——保持"探索"和"实现"的边界。

## 产物布局

写入目标项目的运行时目录，遵循 `.ai/` 边界，不进版本控制：

```text
.ai/design-ui/<feature>/
├── board.html          # 多方案并排对比看板（单文件 HTML，系统默认浏览器打开）
├── variants/           # 每个变体一份单文件 HTML，标注设计方向
├── winner.html         # 收敛后选定的 mockup
├── ui-spec.md          # UI 设计规格：页面/路由/状态 + 组件映射
└── feedback.md         # 跨轮反馈累积（轻量 taste memory）
```

`ui-spec.md` 是交接产物，至少包含：

- 页面/路由/组件清单和关键状态。
- 组件映射：每个区域用哪些 Radix 原语、Tailwind 模式、`data-testid` 命名。
- 关键交互和空/错/加载态。

## 工作流

1. **读上游**：`.ai/decision`、`.ai/prd`、`docs/prd`、`.ai/design` 的前端章节、`guides/frontend/` 的开发与设计模式规范。
2. **生成变体**：产出 4-6 个**不同设计方向**的单文件 HTML mockup（不是同一布局的微调，而是密度、信息层级、视觉风格有实质差异的方案）。每个变体在 `variants/` 下独立成文件，并标注它的设计方向（如"高密度表格优先""卡片流""向导式分步"）。
3. **组成看板**：把所有变体并排组装成 `board.html`。默认不自动打开，需打开时用 `html-show` 契约 `Opening the Preview` 的命令或产物声明的运行命令。
4. **收集反馈**：用 `AskUserQuestion` 收集偏好和修改意见（"留白更多""标题更大""去掉渐变""A 和 B 的头部结合"）。反馈写入 `feedback.md`。
5. **迭代**：基于反馈生成下一轮——标记 winner、对 winner 生成变体、淘汰劣势方案。重复直到用户锁定。
6. **收敛**：把 winner 复制为 `winner.html`，并写 `ui-spec.md`（含组件映射）。
7. **交接**：提示下一步进入 `/t-design`（前端章节承接 `ui-spec.md`）。

## 如何复用现有基础设施

- **HTML 渲染约定**：沿用 `html-show` subagent 的 Preview 输出、依赖声明和打开方式约定，以及 `templates/preview-template.html` 的组件思路。
- **打开方式**：默认不自动打开（可选）；需打开时沿用 `html-show` 契约 `Opening the Preview` 的命令（提交 `32357eb` 已移除专用脚本）。
- **运行时边界**：沿用 `.ai/` 作为目标项目运行时产物根，不进版本控制（见 `protocols/runtime-boundaries.md`）。
- **前端规范**：变体生成时遵循 `guides/frontend/development.md` 的技术基线和 `guides/frontend/patterns.md` 的设计模式，保证 winner 能落地到真实组件。

## taste memory 取舍

gstack 有持久化的项目级 taste profile（含 5%/周衰减）。本项目没有持久 DB，taste memory 落在文件里即可：

- **v1 只做单 feature 跨轮反馈累积**：`feedback.md` 记录每一轮的偏好和修改意见，下一轮生成时读取，使迭代有记忆。
- **跨 feature 的项目级 taste profile 列为后续增强**：若要做，可在 `.ai/design-ui/.taste.md` 维护一份设计偏好摘要（配色、密度、排版倾向），由每个 feature 的 winner 收敛时增量更新。衰减策略可以参考 gstack 的 5%/周，但用文件时间戳近似实现，不需要 DB。

## 交接边界

- `ui-spec.md` → `t-design` 前端章节：作为 UI 约束（页面结构、组件映射、关键状态），`t-design` 不得静默偏离。
- `ui-spec.md` → `t-task`：前端 item 的组件拆分以组件映射为依据。
- 真实 React 组件代码仍由 `t-run` 的 `frontend-dev` 写，本 skill 不产出代码。

## 与现有流程的接入点

实现时需要改一处下游引用：`t-design` 的前端章节增加一行——若存在 `.ai/design-ui/<feature>/ui-spec.md`，必须承接其组件映射与页面结构，并在设计文档中标记"基于已确认 UI 规格"。这与 `t-design` 现有"承接 `.ai/decision` / `.ai/prd`"的引用方式一致。

## 与 gstack 的取舍对照

| 维度 | gstack `/design-shotgun` | 本项目 `t-ui-design` |
|---|---|---|
| 变体形式 | GPT Image 图片 mockup | HTML/CSS mockup（贴近 React+Tailwind 实现） |
| 外部依赖 | 需图像生成 API | 无（单文件 HTML） |
| taste memory | 项目级持久 profile + 衰减 | v1 单 feature 跨轮累积；跨 feature 为后续增强 |
| 代码衔接 | `/design-html` 直接生成可上线 HTML | 只到 `ui-spec.md`；真实组件在 `t-run` 写 |
| 适用范围 | 跨 10 个 AI agent | 仅 Claude Code |
| 位置 | 个人 vibe-coding 流程 | 团队工程流水线（PRD → 设计 → 任务 → 实现） |

核心取舍：本项目用"贴近实现但无外部依赖"换掉 gstack 的"视觉丰富但需图片 API"，并把代码生成留在 `t-run`，守住"探索"与"实现"的阶段边界。
