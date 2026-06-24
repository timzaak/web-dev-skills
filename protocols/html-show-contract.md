# HTML Preview 通用契约

PRD 专用规则见 `${CLAUDE_PLUGIN_ROOT}/protocols/prd-preview-contract.md`。

## File Location

HTML Preview 写入 `.ai/preview/` 下（不进入代码仓库）：

- PRD 草稿: `.ai/prd/<domain>/<feature>.md` → `.ai/preview/<domain>/<feature>.html`（临时草稿，发布后删除）
- 正式 PRD: `docs/prd/<domain>/<feature>.md` → `.ai/preview/<domain>/<feature>.html`
- Decision Brief: `.ai/decision/<feature>.md` → `.ai/preview/decision/<feature>.html`
- Tech Research: `.ai/tech-research/<feature>.md` → `.ai/preview/tech-research/<feature>.html`
- Design: `.ai/design/<feature>.md` → `.ai/preview/design/<feature>.html`
- Task: `.ai/task/<feature>/.../<name>.md` → `.ai/preview/task/<feature>/.../<name>.html`
- 其他文档: `<path>/<name>.md` → `.ai/preview/<name>.html`

Preview 是临时验证产物，不纳入版本控制。每次运行时重新生成。

## Source of Truth

- Markdown 文档是当前 Preview 的结构化真相源。
- HTML Preview 是从 Markdown 文档派生的可视化审阅视图。
- HTML Preview 不允许引入源文档未声明的新需求、规则或约束。
- 如果 Preview 为了演示流程使用示例数据，必须显式标注"示例数据，不是接口契约"。
- 如果 Preview 为了表达内容做了推断，必须在页面中列入"待确认假设"。

## Technology Constraints

HTML Preview 不再强制限定为单文件、内联 CSS/JS、无 npm/CDN/构建工具。允许为了提升可读性使用外部样式、脚本、第三方图形库或辅助资源。

必须满足：

- Preview 主入口仍写入 `.ai/preview/` 下。
- 如果使用外部资源、构建工具、npm 包、CDN 或第三方图形库，必须在 Preview 可见区域标注依赖来源、用途和打开/运行方式。
- 如果生成辅助文件，必须写入 `.ai/preview/` 下与主 HTML 同名或同目录的资源目录，不得写入目标项目源码。
- 不引用目标项目源码中的 React/Vue/Svelte/miniapp 组件作为 Preview 的运行依赖；目标项目已有 UI 只可作为入口或约束说明，不作为 Preview 主体复刻。
- 不要求所有 Preview 都能直接双击打开；如果需要本地服务或构建步骤，必须报告可复现命令。

## Review Workflow

`/t-html-show` 生成或更新 Preview 后，默认不自动打开；打开为可选项，规则与命令见下方 `Opening the Preview`。

推荐流程：

- 生成或更新 HTML Preview。
- 报告 Preview 路径和打开命令（默认不自动打开，见 `Opening the Preview`）。
- 人类提出修改意见。
- 同步修改 HTML Preview 与源文档。
- 重复审阅，直到人类确认 Preview 表达了真实意图。

## Opening the Preview

默认不自动打开。生成或更新 Preview 后，只报告 `preview_path` 和当前平台对应的打开命令，由人类自行决定是否打开。如 Preview 依赖外部资源、npm 包、构建工具或本地服务，还必须报告依赖说明和可复现的安装/构建/启动命令。

仅当人类在对话中明确要求打开（如"打开预览"/"open it"）时才执行打开；不解析额外 flag。

可直接打开的 Preview 按平台选择命令：

| 平台 | 命令 |
|---|---|
| macOS | `open "<path>"` |
| Windows（Git Bash） | `cmd.exe //c start "" "<path>"` |
| Linux | `xdg-open "<path>"` |

分支判断写法：

```bash
path="<preview-path>"
if [ "$(uname -s)" = "Darwin" ]; then open "$path"
elif [ -n "$WINDIR" ]; then cmd.exe //c start "" "$(cygpath -w "$path" 2>/dev/null || echo "$path")"
else xdg-open "$path"; fi
```

需要本地服务或构建步骤的 Preview，按页面声明的运行命令启动，再打开对应 URL 或产物路径。

校验要求：执行后必须确认命令返回成功；失败时如实报告路径与命令，不得谎报"已打开"。子代理同样遵守：不得在未真正打开时报告"已打开"。

## Content Model

Preview 不是 Markdown 的 HTML 复写，而是面向人类快速判断的解释视图。

每个 Preview 必须先回答：

- 这份文档是什么。
- 最重要的结论、变化或阻塞是什么。
- 人类需要优先审阅哪里。

页面结构遵循 Shneiderman 视觉信息觅食口诀「Overview first, zoom and filter, then details-on-demand」（1996）：

- **Overview first**：首屏必须有一句话结论、来源文档路径、文档类型、主视觉和最多 4 个注意项（数量受工作记忆 4±1 chunks 约束，Cowan 2001；超出则读者无法在首屏保持）。首屏的「结论 + 来源 + 类型 + 主视觉」共同构成 *information scent*（Pirolli & Card 信息觅食理论），让读者一眼判断是否值得深入。
- **Zoom/filter**：主体按文档类型展示关键关系、变化、依赖、风险或状态，不按 Markdown 原文顺序机械搬运。
- **Details on demand**：长表、步骤、证据、文件清单和细节说明默认放入 `<details>` 或次级区域。

首屏主信息按文档的审阅任务分治，不是所有文档都"结论先行"：

- **Decision / Tech Research（判断类）**：结论先行，首屏给结论、置信度、致命假设与风险。
- **Task（执行/恢复类）**：首屏给 Current Progress（当前 phase/slot 进度）+ Blocking（阻塞门禁）+ Next Action（下一步命令），让执行者一眼定位"现在干什么、卡在哪"，而非一句话结论。这三段对应 Endsley 情境感知三层：Perception（当前到哪）→ Comprehension（卡在哪/为何阻塞）→ Projection（下一步干什么），也是 operational dashboard「status at a glance」的惯例。
- **PRD（完整性审查类）**：不要结论先行 + 折叠细节。用强视觉层级（明确标题与区块）诱发 layer-cake 扫描以覆盖完整性；边界态、异常态、权限覆盖等完整性要点必须上提到注意项区域且禁止折叠，避免读者走 F-pattern 漏审。
- **Design / Generic**：首屏给主变化或核心答案，细节折叠。

必须包含：

- 文档标题、来源文档路径。
- 一句话结论或目标（结论先行型须短到可一眼判读，见下「首屏一眼可读」）。
- 一个主视觉区域，使用 `data-doc-section="PrimaryVisual"` 标记。
- 注意项区域，使用 `data-doc-section="Attention"` 标记；如没有风险或待确认项，写“无”。
- 依赖声明和打开/运行方式（如使用外部资源、npm 包、CDN、第三方图库、构建工具或辅助文件）。
- 示例数据声明（如使用）。
- 待确认假设（如有）。

### 首屏一眼可读（status at a glance）

首屏不是把结论写满，而是让读者**不滚动**即可抓到 #1 事实（Few 运营看板「5 秒规则」）。按文档类型落实：

- **结论先行型（decision / tech-research / design / generic）**：hero 结论标题必须是**单个从句**（建议 ≤ 40 汉字 / 80 字符），超长即无法一眼判读。`check_hero_brevity` 校验 `.insight` 首个标题长度。
- **task（执行/恢复型）**：首屏用三个情境感知锚点替代单一结论，标注 `data-sa="current"`（Perception：当前 phase/slot 进度）、`data-sa="blocking"`（Comprehension：阻塞门禁）、`data-sa="next"`（Projection：下一步命令），对应 Endsley 情境感知三层。`check_task_situational_awareness` 校验三锚点齐备且**不在 `<details>` 内**。

### 决策关键内容必须可见

kill criteria、阻塞门禁、边界态等**决定结论**的要点不得折叠进 `<details>`——折叠等于藏起 kill switch。`check_critical_content_visible` 按 doc type 校验：PRD（异常/空态/权限）、Decision（杀死/致命/不可逆）、Task（阻塞/门禁）。仅当某要点「全文仅出现在 `<details>` 内」才记违规（有可见副本即放行）。

禁止生成流水账式 Preview：连续卡片、长列表、按 Markdown 标题逐段复制、没有主视觉的表格堆叠，都不算合格 Preview。这类形态制造 *extraneous cognitive load*（Sweller 认知负荷理论）：读者把心智花在「拼接散落卡片」上而非理解内容，因此必须用主视觉把关系一次性外化。

## Expression Library

HTML Preview 的主视觉必须按文档语义选择表达方式，不能默认堆卡片。`.card` 只适合承载局部说明或重复条目，不应成为页面的主要表达结构。

可选表达形态：

| 表达形态 | 适用语义 | 推荐 HTML 结构 |
|---|---|---|
| Flow graph | 步骤、调用链、审批链、数据流 | `.flow-graph` + `.flow-node` + `.flow-edge` |
| State graph | 状态、触发条件、合法/非法迁移 | `.state-graph` + `.state-node` + `.transition` |
| DAG / Dependency graph | task item 依赖、模块依赖、阻塞关系 | `.dag` + `.node-row` 或 `.dependency-grid` |
| Inline SVG graph | 复杂连线、分支、汇聚、环路 | `<svg class="svg-graph">` + `<g>` + `<path>` + `<text>` |
| Mermaid graph | 流程、状态、时序、类图等标准图 | Mermaid fenced source 或 Mermaid runtime |
| D3 / ECharts graph | 复杂关系、布局、数据驱动图 | 外部脚本或本地依赖，必须声明依赖与打开方式 |
| Timeline | 决策过程、版本演进、交付节奏 | `.timeline` + `.timeline-item` |
| Swimlane | 角色协作、系统边界、跨端流程 | `.swimlane` + `.lane-track` |
| Matrix | 能力边界、验收覆盖、方案比较 | `<table class="matrix">` |
| Heatmap | 风险、影响范围、覆盖强弱 | `.heatmap`，按位置和等级排序 |
| Funnel / Pipeline | 转化、处理阶段、排队和释放 | `.pipeline` + `.pipeline-stage` |
| Radial / Hub map | 中心能力与周边调用方/约束 | `.hub-map` + `.hub` + `.spoke` |
| Interactive preview | 有用户入口的前端目标体验 | 原生 HTML 控件 + `[data-panel]` |

选型规则：

- 有方向关系时优先使用 flow graph、state graph、DAG、swimlane 或 pipeline。
- 连线复杂、分支汇聚较多、HTML 节点难以排布时，可使用内联 SVG、Mermaid、D3、ECharts 或其他图形库；使用第三方库时必须声明依赖与打开方式。
- 有集合比较时优先使用 matrix、heatmap 或 option comparison。
- 有时间顺序时优先使用 timeline。
- 有中心能力与外部关系时优先使用 hub map。
- 只有无法归类的说明性内容才使用 card；连续 3 个以上 card 必须重新判断是否应改成图、矩阵、时间线或泳道。
- 图形节点必须包含内联标签、状态或简短解释，不能只用色块、连线或图例承载含义。

## Visual Encoding Rules

- 位置：最重要的信息固定在首屏顶部或左上。
- 大小与孤立：只有结论、阻塞、主变化可以放大。多个状态信号并列时，**有且仅有一个**最优先信号用 `data-rank="dominant"` 标记并放大（Von Restorff 孤立效应：唯一突出的元素才被记住；等权多信号互相抵消，无一成为真正的阻塞；亦即 Mayer 信号原理所依）。`check_attention_dominance` 校验 Attention 区 bad/warn ≥ 2 时有且仅有一个 dominant。
- 颜色：只表达状态，不做装饰（Tufte 数据墨水比：最大化承载信息的墨水，最小化装饰墨水）。红色表示阻塞或高风险，黄色表示待确认，绿色表示已满足，灰色表示背景信息。
- 颜色冗余：状态色不得是唯一编码手段。红/黄/绿必须同时配**内联**文字标签或图标（如 ✓/⚠/✗），满足无障碍（WCAG 1.4.1 Use of Color）。图标必须内联在元素文本里，不得仅靠 CSS `::before` 注入——后者机械检查与部分读屏不可见，等于没有冗余。
- 对比度：正文与背景对比度 ≥ 4.5:1（WCAG 1.4.3 AA）。`check_contrast` 校验 `:root` 调色板的正文/次要正文配对——防止修改设计令牌引入低对比度配色。
- 空间邻近：标签须紧贴其描述对象（Mayer 空间邻近原理），例如 DAG 节点内联标注而非另设图例，避免读者在「图例↔图形」间反复对位。
- 编码通道：需做大小判断的信号（风险、优先级、进度）必须用位置或长度编码，颜色和面积只能做辅助语义，不得单独承担判断（依据 Cleveland & McGill 1984 图形感知精度排序：位置（共同刻度）> 长度 > 方向/角度 > 面积 > 体积/曲度 > 饱和度 > 色相）。
- 前注意加工：颜色、位置、长度是前注意属性（Treisman），<200ms 并行感知。这解释了「颜色快但不精确」：色相能瞬间吸引注意，却无法可靠传递量级，故只能做状态提示，不能做大小判断。
- 分组：同一 phase、slot、模块、风险类别或验收域必须放在共同区域中（Gestalt 共同区域）。
- 连线：只表达依赖、迁移、调用、状态流转或 handoff，不用作装饰。
- 细节：能折叠的细节不要挤占首屏。

## Document Profiles

`templates/preview-template.html` 是解释型组件库，不代表每种文档都必须展示全部 section。生成时必须按文档类型选择 profile：

| 文档类型 | 人类审阅问题 | 首屏主视觉 | 推荐 section |
|---|---|---|---|
| PRD | 产品意图、范围、规则和验收目标是否正确 | 用户路径/业务状态 + 完整性要点（上提、禁折叠） | `Overview`、`Scope`、`Flow`、`States`、`Rules`、`Acceptance`、`Assumptions` |
| Decision Brief | 是否值得做，边界和杀死条件是什么 | 决策地图 | `Decision`、`Confidence`、`Scope Direction`、`Kill Criteria`、`D0/D1 Decisions`、`Open Questions`、`Handoff` |
| Tech Research | 技术路线是否可行，差距和风险在哪里 | 可行性地图 | `Feasibility`、`Gap Matrix`、`Option Comparison`、`Risks`、`Handoff` |
| Design | 实现结构会怎么变，影响面和风险在哪里 | 结构变化地图 | `Intent`、`Traceability`、`Architecture Change`、`Interface & Data Impact`、`Frontend Impact`、`Risks`、`Test Strategy`、`File Impact`、`Handoff` |
| Task | 怎么执行、怎么恢复、哪些门禁会阻塞 | 执行地图（Current + Blocking + Next） | `Execution Overview`、`Phase & Slot Map`、`Item DAG`、`Blocking Gates`、`Validation Plan`、`Resume Points`、`Handoff` |
| Generic | 这份文档讲什么，核心答案是什么 | answer board 或文档导读 | 按 Markdown 大纲自适应 |

**section 与 3-block 骨架的映射**：通用模板 `preview-template.html` 是「重点（PrimaryVisual）/ 结构（Map）/ 细节（Details）」三块骨架。上表每个文档类型的”推荐 section”是该类型应在结构区及其下展开的内容块，不要求页面逐字出现这些标题——agent 在 3-block 骨架内用对应组件（`change-map`、`dag`、`lane`、`matrix`、`signal`、`details` 分组等）表达这些内容。PRD 走 `prd-preview-contract.md` 的固定结构，不套用 3-block 骨架。

不得为了套模板而制造源文档没有的内容。模板中的占位 section 如果源文档没有对应信息，生成时应删除或标注为”无”，不要编造。

## Determinism Rules

Preview 使用固定结构：

- 页面标题使用 `[文档名称] Preview`。
- 顶部 summary 区展示元数据和一句话目标。
- 页面元素使用语义化 `data-doc-*` 属性标记来源，例如 `data-doc-source`、`data-doc-section`。
- `<html>` 应标注 `data-doc-type`，取值为 `prd`、`decision`、`design`、`tech-research`、`task` 或 `generic`。
- 命名空间：PRD Preview 使用 `data-prd-source`/`data-prd-section`（见 `prd-preview-contract.md`）；其他类型使用 `data-doc-source`/`data-doc-section`。两套标记并存，机械检查各自认各自的 marker。
- 情境感知锚点：task 用 `data-sa="current|blocking|next"` 标注三锚点（见「首屏一眼可读」）。
- 孤立信号：Attention 区多信号时用 `data-rank="dominant"` 标记唯一最优先信号（见「Visual Encoding Rules · 大小与孤立」）。
- 样式应保持中性、低保真、易读，不追求目标项目视觉还原。

## Check Scope

可用 `${CLAUDE_PLUGIN_ROOT}/scripts/check-html-show.py` 执行机械检查。

通用检查项：

- Preview 文件是否存在。
- Preview 主入口是否存在；如使用外部脚本、样式、CDN、npm 包或构建工具，是否声明依赖来源、用途和打开/运行方式。
- 是否包含来源文档路径。
- 是否没有出现接口端点清单、请求响应 schema、数据库设计或代码类型定义。
- 颜色冗余（WCAG 1.4.1）：状态色块须内联文字/图标，不得仅靠 CSS 注入。
- 对比度（WCAG 1.4.3 AA）：`:root` 调色板正文配对 ≥ 4.5:1。
- 首屏一眼可读：结论先行型 hero 标题长度、task 的 Current/Blocking/Next 三锚点齐备且未折叠。
- 孤立信号（Von Restorff）：Attention 区多信号时有且仅有一个 `dominant`。
- 决策关键内容可见：kill criteria/阻塞门禁/边界态不得仅藏在 `<details>` 内。

PRD 专用检查项见 `${CLAUDE_PLUGIN_ROOT}/protocols/prd-preview-contract.md`。

违反 Preview 契约时：

- Preview 引入源文档未声明的新规则或约束：P1。
- Preview 混入端点、schema、建表、迁移、类型定义等禁止内容：P0。
- Preview 使用外部依赖但未声明来源、用途或打开/运行方式：P1。
