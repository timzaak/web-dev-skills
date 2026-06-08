# PRD HTML Preview Contract

PRD 专用的 HTML Preview 契约。通用规则（技术约束、审阅流程、内容模型）定义在 `protocols/html-show-contract.md`，此处不重复。

定义 `/t-html-show` 在 PRD 模式下的专用规则，以及 `/t-prd-check` 对该预览的检查边界。

## Purpose

HTML Preview 是 PRD 的可视化审阅和协作产物，用于帮助人类快速理解、反馈和修改功能目标、用户路径、状态变化和待确认假设。

它不是实现方案、不是接口契约、不是最终 UI 设计稿。它是 PRD 的主要阅读界面，Markdown PRD 是结构化产品语义契约；两者必须同步。

## File Location

每份 PRD 草稿或正式 PRD 必须在 `.ai/preview/` 下生成对应 HTML Preview（不进入代码仓库）：

- PRD 草稿: `.ai/prd/<domain>/<feature>.md`
- 正式 PRD: `docs/prd/<domain>/<feature>.md`
- Preview: `.ai/preview/<domain>/<feature>.html`

Preview 是临时验证产物，不纳入版本控制。每次 `/t-html-show`、`/t-prd` 或 `/t-prd-publish` 后可重新生成。

## Source of Truth

- `.ai/prd` 中的 Markdown PRD 是临时候选产品语义契约，用于草稿审阅，发布成功后应删除。
- `docs/prd` 中的 Markdown PRD 是已发布的正式产品语义契约。
- HTML Preview 是从 Markdown PRD 派生的可视化审阅视图，也是人机沟通时优先打开和讨论的协作界面。
- HTML Preview 不允许引入 Markdown PRD 未声明的新需求、权限规则、业务规则或验收目标。
- 如果人类基于 HTML Preview 提出修改，必须同时更新 HTML Preview 和 Markdown PRD，不能只改其中一个。
- 如果 Preview 为了演示流程使用示例数据，必须显式标注“示例数据，不是接口契约”。
- 如果 Preview 为了表达交互做了推断，必须在页面中列入“待确认假设”。

## Technology Constraints

HTML Preview 必须保持目标项目技术栈无关：

- 使用单文件 HTML。
- CSS 和少量 JavaScript 内联。
- 不依赖 npm、构建工具、CDN、目标项目组件库或前端运行时。
- 不引用目标项目源码中的 React/Vue/Svelte/miniapp 组件。
- 不要求启动 dev server，浏览器直接打开即可审阅。

## Review Workflow

`/t-html-show` 在 PRD 模式下生成或更新 Preview 后，必须立即打开 `.ai/preview/<domain>/<feature>.html` 供人类审阅。

审阅流程遵循 `html-show-contract.md` 中定义的通用 Review Workflow，并增加：运行 `/t-prd-check` 验证 Preview 与 Markdown PRD 描述一致。

## Content Model

Preview 应结合“可视化 PRD 阅读器”和“低保真交互原型”两种形态。

必须包含：

- 功能名、优先级、来源 PRD 路径。
- 一句话目标。
- 需求背景或目标能力概述。
- In Scope / Out of Scope。
- 关键业务规则。
- 主要用户路径或业务流程。
- 业务状态、异常、空态或权限可见性说明。
- 验收目标摘要。
- 示例数据声明（如使用）。
- 待确认假设（如有）。

前端或交互功能应包含：

- 页面入口。
- PRD 定义的关键页面/区域低保真示意。
- 可点击或可切换的核心交互状态。
- 成功、失败、空态、加载态或禁用态中的关键状态。
- 已有代码实现的 UI 只可作为入口或约束说明，不作为 Preview 主体复刻。

纯后端或无用户界面的功能不生成伪 UI，但仍必须生成 Preview：

- 使用流程图、状态图、调用方场景、能力边界矩阵或验收矩阵表达。
- 不展示无意义的数据页面。
- 复杂后端场景应优先用 HTML/CSS 表达流程图或状态流转。

## Determinism Rules

Preview 使用固定结构：

- 页面标题使用 `<feature> PRD Preview`。
- 顶部 summary 区展示元数据和一句话目标。
- 主体使用固定区域：`Overview`、`Scope`、`Flow`、`States`、`Rules`、`Acceptance`、`Assumptions`。
- 页面元素使用语义化 `data-prd-*` 属性标记来源，例如 `data-prd-source`, `data-prd-section`。
- 样式应保持中性、低保真、易读，不追求目标项目视觉还原。

## Check Scope

`/t-prd-check` 必须把 HTML Preview 作为检查对象，但检查目标是“可审阅性和一致性”，不是视觉美观。

检查项：

- 可使用 `${CLAUDE_PLUGIN_ROOT}/scripts/check-html-show.py --type prd` 执行机械检查。
- Preview 文件是否存在且路径为 `.ai/preview/<domain>/<feature>.html`。
- 是否为单文件 HTML，且不依赖外部脚本、样式、CDN 或目标项目构建产物。
- 是否包含来源 PRD 路径。
- 是否包含固定区域：`Overview`、`Scope`、`Flow`、`States`、`Rules`、`Acceptance`、`Assumptions`。
- 是否包含示例数据声明（当页面出现示例数据时）。
- 对前端/交互功能，是否聚焦 PRD 定义的目标体验和关键状态，而不是复刻已有实现。
- 是否没有引入 PRD 未声明的新业务规则或验收目标。
- 是否与 Markdown PRD 的目标、范围、流程、业务状态、规则和验收目标一致。
- 是否没有出现接口端点清单、请求响应 schema、数据库设计或代码类型定义。

违反 Preview 契约时：

- 缺失 Preview 文件：P1。
- Preview 引入 PRD 未声明的新业务规则、权限规则或验收目标：P1。
- Preview 混入端点、schema、建表、迁移、类型定义等禁止内容：P0。
- Preview 依赖目标项目技术栈、构建工具或外部 CDN：P1。
- Preview 缺少必要审阅区域或来源 PRD 路径：P2。
