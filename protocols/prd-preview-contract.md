# PRD HTML Preview Contract

通用规则见 `${CLAUDE_PLUGIN_ROOT}/protocols/html-show-contract.md`。

## File Location

PRD 草稿或正式 PRD 的对应 HTML Preview 写入 `.ai/preview/`（不进入代码仓库）：

- PRD 草稿: `.ai/prd/<domain>/<feature>.md`
- 正式 PRD: `docs/prd/<domain>/<feature>.md`
- Preview: `.ai/preview/<domain>/<feature>.html`

Preview 是临时验证产物，不纳入版本控制。

## Source of Truth

- `.ai/prd` 中的 Markdown PRD 是临时候选产品语义契约，用于草稿审阅、设计、任务、实现和验收阶段，同步到正式 PRD 后应删除。
- `docs/prd` 中的 Markdown PRD 是已发布的正式产品语义契约。
- HTML Preview 是从 Markdown PRD 派生的可视化审阅视图，也是人机沟通时优先打开和讨论的协作界面。
- HTML Preview 不允许引入 Markdown PRD 未声明的新需求、权限规则、业务规则或验收目标。
- 如果人类基于 HTML Preview 提出修改，必须同时更新 HTML Preview 和 Markdown PRD，不能只改其中一个。
- 如果 Preview 为了演示流程使用示例数据，必须显式标注“示例数据，不是接口契约”。
- Preview 为表达交互所做的推断只能是不改变产品语义的可视化假设，并必须显式标注；需要用户裁决的问题必须在生成 Preview 前按 Decision Exposure Gate 解决。

## Technology Constraints

HTML Preview 不再强制限定为单文件、内联 CSS/JS、无 npm/CDN/构建工具。允许为了提升 PRD 可审阅性使用外部样式、脚本、第三方图形库或辅助资源。

必须满足：

- Preview 主入口仍写入 `.ai/preview/<domain>/<feature>.html`。
- 如果使用外部资源、构建工具、npm 包、CDN 或第三方图形库，必须在 Preview 可见区域标注依赖来源、用途和打开/运行方式。
- 如果生成辅助文件，必须写入 `.ai/preview/` 下与主 HTML 同名或同目录的资源目录，不得写入目标项目源码。
- 不引用目标项目源码中的 React/Vue/Svelte/miniapp 组件作为 Preview 的运行依赖；已有 UI 只可作为入口或约束说明，不作为 Preview 主体复刻。

## Review Workflow

`/t-html-show` 在 PRD 模式下生成或更新 Preview 后，默认不自动打开；打开为可选项，规则与命令见 `html-show-contract.md` 的 `Opening the Preview`。

审阅流程遵循 `html-show-contract.md` 中定义的通用 Review Workflow。

## Content Model

Preview 应结合“可视化 PRD 阅读器”和“低保真交互原型”两种形态。

PRD 的审阅任务是**完整性审查**（产品意图、范围、规则、验收是否正确且无遗漏），既不是判断类（Decision/Research），也不是执行类（Task）。因此 PRD Preview 的信息架构与通用契约的「结论先行 + 折叠细节」不同：

- **不结论先行、不折叠细节**：不要把内容压成一句话结论、再把需要逐一核对的要素塞进 `<details>`。PRD 读者要确认「有没有漏」，结论先行反而会隐藏待审查项。
- **用强视觉层级诱发 layer-cake 扫描**：每个固定 section 必须有清晰标题与独立区块，让读者视线沿标题层逐块停留（NN/g layer-cake 模式），从而覆盖完整性、发现缺口；避免无标题长文诱发 F-pattern（只盯左上、漏掉靠后与右下 section）。
- **边界态/异常态/空态/错误态/权限可见性必须上提到可见区域且禁止折叠**：这些是完整性审查最易漏的点，不得放进 `<details>`。`check_critical_content_visible`（doc type = prd）会校验「异常/空态/错误/失败/权限/边界/禁用」等关键词不得仅出现在 `<details>` 内。

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
- 可视化假设或验证风险（如有；不得包含需要用户回答的问题）。

前端或交互功能应包含：

- 页面入口。
- PRD 定义的关键页面/区域低保真示意。
- 可点击或可切换的核心交互状态。
- 成功、失败、空态、加载态或禁用态中的关键状态。
- 已有代码实现的 UI 只可作为入口或约束说明，不作为 Preview 主体复刻。

纯后端或无用户界面的功能不生成伪 UI：

- 使用流程图、状态图、调用方场景、能力边界矩阵或验收矩阵表达。
- 不展示无意义的数据页面。
- 复杂后端场景可使用 HTML/CSS、内联 SVG、Mermaid、D3、ECharts 或其他图形库表达流程图或状态流转；使用外部依赖时必须声明依赖和打开/运行方式。

## Determinism Rules

Preview 使用固定结构：

- 页面标题使用 `<feature> PRD Preview`。
- 顶部 summary 区展示元数据和一句话目标。
- 主体使用固定区域：`Overview`、`Scope`、`Flow`、`States`、`Rules`、`Acceptance`、`Assumptions`。
- 页面元素使用语义化 `data-prd-*` 属性标记来源，例如 `data-prd-source`, `data-prd-section`。
- 样式应保持中性、低保真、易读，不追求目标项目视觉还原。

## Check Scope

检查目标是“可审阅性和一致性”，不是视觉美观。

检查项：

- 可使用 `${CLAUDE_PLUGIN_ROOT}/scripts/check-html-show.py --type prd` 执行机械检查。
- Preview 文件路径是否为 `.ai/preview/<domain>/<feature>.html`。
- 如使用外部脚本、样式、CDN、npm 包或构建工具，是否声明依赖来源、用途和打开/运行方式。
- 是否包含来源 PRD 路径。
- 是否包含固定区域：`Overview`、`Scope`、`Flow`、`States`、`Rules`、`Acceptance`、`Assumptions`。
- 边界态/异常态/权限等完整性要点是否被折叠进 `<details>`（由 `check_critical_content_visible` 校验，违反记 P1）。
- 是否包含示例数据声明（当页面出现示例数据时）。
- 对前端/交互功能，是否聚焦 PRD 定义的目标体验和关键状态，而不是复刻已有实现。
- 是否没有引入 PRD 未声明的新业务规则或验收目标。
- 是否与 Markdown PRD 的目标、范围、流程、业务状态、规则和验收目标一致。
- 是否没有出现接口端点清单、请求响应 schema、数据库设计或代码类型定义。

违反 Preview 契约时：

- Preview 引入 PRD 未声明的新业务规则、权限规则或验收目标：P1。
- Preview 混入端点、schema、建表、迁移、类型定义等禁止内容：P0。
- Preview 使用外部依赖但未声明来源、用途或打开/运行方式：P1。
- Preview 缺少必要审阅区域或来源 PRD 路径：P2。
