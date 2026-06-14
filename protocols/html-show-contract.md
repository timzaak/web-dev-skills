# HTML Preview 通用契约

PRD 专用规则见 `${CLAUDE_PLUGIN_ROOT}/protocols/prd-preview-contract.md`。

## File Location

HTML Preview 写入 `.ai/preview/` 下（不进入代码仓库）：

- PRD 草稿: `.ai/prd/<domain>/<feature>.md` → `.ai/preview/<domain>/<feature>.html`（临时草稿，发布后删除）
- 正式 PRD: `docs/prd/<domain>/<feature>.md` → `.ai/preview/<domain>/<feature>.html`
- Decision Brief: `.ai/decision/<feature>.md` → `.ai/preview/decision/<feature>.html`
- Tech Research: `.ai/tech-research/<feature>.md` → `.ai/preview/tech-research/<feature>.html`
- Design: `.ai/design/<feature>.md` → `.ai/preview/design/<feature>.html`
- 其他文档: `<path>/<name>.md` → `.ai/preview/<name>.html`

Preview 是临时验证产物，不纳入版本控制。每次运行时重新生成。

## Source of Truth

- Markdown 文档是当前 Preview 的结构化真相源。
- HTML Preview 是从 Markdown 文档派生的可视化审阅视图。
- HTML Preview 不允许引入源文档未声明的新需求、规则或约束。
- 如果 Preview 为了演示流程使用示例数据，必须显式标注"示例数据，不是接口契约"。
- 如果 Preview 为了表达内容做了推断，必须在页面中列入"待确认假设"。

## Technology Constraints

HTML Preview 必须保持目标项目技术栈无关：

- 使用单文件 HTML。
- CSS 和少量 JavaScript 内联。
- 不依赖 npm、构建工具、CDN、目标项目组件库或前端运行时。
- 不引用目标项目源码中的 React/Vue/Svelte/miniapp 组件。
- 不要求启动 dev server，浏览器直接打开即可审阅。

## Review Workflow

`/t-html-show` 生成或更新 Preview 后，必须立即打开 HTML 文件供人类审阅。

推荐流程：

- 生成或更新 HTML Preview。
- 立即打开。
- 人类提出修改意见。
- 同步修改 HTML Preview 与源文档。
- 重复审阅，直到人类确认 Preview 表达了真实意图。

## Content Model

Preview 应结合"可视化阅读器"和"低保真交互原型"两种形态。

必须包含：

- 文档标题、来源文档路径。
- 一句话目标。
- 从源文档提取的关键内容，按逻辑分组为可审阅区域。
- 示例数据声明（如使用）。
- 待确认假设（如有）。

具体 section 由 agent 根据文档类型自适应选择。PRD 文档使用固定 section profile（见 `prd-preview-contract.md`）。

## Document Profiles

`templates/preview-template.html` 是通用壳和组件库，不代表每种文档都必须展示全部 section。生成时按文档类型裁剪：

| 文档类型 | 推荐 section | 适合的表达组件 |
|---|---|---|
| Decision Brief | `Decision`、`Overview`、`Scope`、`Evidence`、`Rules`、`Handoff`、`Assumptions` | verdict callout、metric-grid、compare、timeline |
| PRD | `Overview`、`Scope`、`Flow`、`States`、`Rules`、`Acceptance`、`Assumptions` | low-fidelity prototype、state-list、acceptance table |
| Tech Research | `Overview`、`Evidence`、`Scope`、`Rules`、`Handoff`、`Assumptions` | feasibility callout、gap matrix、risk table、reference list |
| Design | `Overview`、`Scope`、`Flow`、`States`、`Rules`、`Acceptance`、`Handoff` | diagram、timeline、matrix、risk table |
| Generic | 按 Markdown 标题自适应 | document-reader、table、callout |

不得为了套模板而制造源文档没有的内容。模板中的占位 section 如果源文档没有对应信息，生成时应删除或标注为“无”，不要编造。

## Determinism Rules

Preview 使用固定结构：

- 页面标题使用 `[文档名称] Preview`。
- 顶部 summary 区展示元数据和一句话目标。
- 页面元素使用语义化 `data-doc-*` 属性标记来源，例如 `data-doc-source`、`data-doc-section`。
- `<html>` 应标注 `data-doc-type`，取值为 `prd`、`decision`、`design`、`tech-research` 或 `generic`。
- 样式应保持中性、低保真、易读，不追求目标项目视觉还原。

## Check Scope

可用 `${CLAUDE_PLUGIN_ROOT}/scripts/check-html-show.py` 执行机械检查。

通用检查项：

- Preview 文件是否存在。
- 是否为单文件 HTML，且不依赖外部脚本、样式、CDN。
- 是否包含来源文档路径。
- 是否没有出现接口端点清单、请求响应 schema、数据库设计或代码类型定义。

PRD 专用检查项见 `${CLAUDE_PLUGIN_ROOT}/protocols/prd-preview-contract.md`。

违反 Preview 契约时：

- Preview 引入源文档未声明的新规则或约束：P1。
- Preview 混入端点、schema、建表、迁移、类型定义等禁止内容：P0。
- Preview 依赖目标项目技术栈、构建工具或外部 CDN：P1。
