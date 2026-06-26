# UI Design Exploration Contract

本协议定义 `/t-ui-design` 的运行时产物、HTML mockup 约束和 `ui-spec.md` 交接结构。它只覆盖 UI 方案探索，不替代 PRD、技术设计、任务拆分或前端实现。

## File Location

UI 探索产物写入目标项目 `.ai/design-ui/<feature>/`，不进入正式源码：

```text
.ai/design-ui/<feature>/
├── board.html
├── variants/
│   ├── 01-*.html
│   ├── 02-*.html
│   └── ...
├── archive/
│   └── <round-or-timestamp>/
├── winner.html
├── ui-spec.md
└── feedback.md
```

- `board.html`：多方案并排对比看板。
- `variants/*.html`：决策前的活跃候选方案，每个 UI 方向一份可独立打开的单文件 HTML。
- `archive/<round-or-timestamp>/`：已收敛或被淘汰的历史探索稿，只作为追溯记录。
- `winner.html`：人类确认后的选中方案。
- `ui-spec.md`：交给 `/t-design` 的 UI 规格契约。
- `feedback.md`：同一 feature 内的反馈和偏好记忆。

## Source of Truth

- PRD、Decision Brief、用户故事和目标项目代码事实是产品与工程真相源。
- UI variant 是探索稿，用来帮助人类比较方向，不是产品契约。
- winner 确认前，`variants/*.html` 是候选探索稿；winner 确认后，`variants/*.html` 不再是活跃交接源。
- winner 确认后，`ui-spec.md` 是唯一文本规格真相源，`winner.html` 是唯一视觉参考真相源，供 `/t-design` 前端章节承接。
- `board.html`、`feedback.md` 和 `archive/**` 是决策记录或历史记录，不得作为后续设计、任务或实现的直接 UI 输入。
- 如果 UI 探索与 PRD 或用户故事冲突，停止并要求先修正上游文档。

## Technology Constraints

UI mockup 必须保持可直接审阅、无外部运行时依赖：

- 使用单文件 HTML。
- CSS 和少量原生 JavaScript 内联。
- 不依赖 npm、构建工具、CDN、React/Vue/Svelte、目标项目组件库或前端 dev server。
- 不调用图片生成 API，不要求 Figma、v0、Stitch、Lovable 或其他外部设计工具。
- 不引用外部图片、字体、脚本或样式。图标可用内联 SVG 或文本符号表达。
- 不生成可上线 React 代码；真实实现仍由 `/t-run` 的 frontend agent 完成。

## Variant Requirements

首轮默认生成 4-6 个方向。每个 variant 必须：

- 有明确设计方向名称，例如“高密度表格优先”“向导式分步”“卡片流概览”。
- 在布局、信息层级、密度、导航/交互模型或视觉语气上有实质差异。
- 覆盖核心页面区域、主操作、关键状态和主要反馈。
- 标注 mock data，避免伪装成接口契约。
- 标注来源和假设，例如 `data-ui-source`、`data-ui-variant`、`data-ui-assumption`。
- 遵循目标项目既有 frontend 规范和可实现组件边界，不创造无法映射到真实组件的概念控件。

禁止：

- 只改颜色、圆角或间距形成伪多方案。
- 把 API path、DTO schema、数据库字段或实现任务塞进 HTML。
- 为了视觉效果牺牲可读性、可访问性或移动端基本布局。

## Board Requirements

`board.html` 必须：

- 列出所有 variants 的方向、适用场景和主要取舍。
- 通过内嵌 HTML、同目录 iframe 或等价结构并排/分组展示 variants。
- 提供清晰的 winner/feedback 记录区域。该区域是**持久记录**，不是非持久草稿：决策前可临时记录偏好（“选为 winner”等点击交互刷新后可复位，这部分不要求持久化）；**winner 一经确认，必须把选定方向、保留/并入/淘汰元素以及指向 `winner.html`/`ui-spec.md`/`feedback.md` 的链接回写进 `board.html`**，使看板与确认结果一致，不得停留在首轮“未选择”状态。“不需要持久化交互”仅指决策前的点击交互，不豁免收敛后的回写。
- `board.html` 自身无网络依赖；如引用 sibling 产物，只允许引用 `.ai/design-ui/<feature>/` 下的本地产物（`variants/*.html`、`winner.html` 等）。

## Finalization and Archive Rules

确认 winner 后必须执行收敛清理，避免废弃 UI 被后续流程误读：

- 将最终选中方案写入 `winner.html`；如 winner 基于多个 variant 合并，`winner.html` 必须体现合并后的最终结果，而不是简单复制单个候选稿。
- 生成或更新 `ui-spec.md`，并在其中明确选定方向、保留/并入/淘汰元素和待 `/t-design` 承接的页面、组件、状态。
- 将所有未选中或已废弃的候选 HTML 移出活跃 `variants/`，归档到 `archive/<round-or-timestamp>/variants/`；归档文件必须在文件顶部或页面显著位置标注 `DEPRECATED UI EXPLORATION - DO NOT USE AS DESIGN INPUT`。
- winner 源文件也应从 `variants/` 移出或归档；收敛后的活跃视觉参考只能是 `winner.html`，避免同一方案存在多个可被误读的活跃副本。
- 收敛完成后，`variants/` 不得继续保留废弃 HTML。可以为空，或只保留说明文件指向 `winner.html`、`ui-spec.md` 和 `archive/`。
- `board.html` 可以保留历史对比摘要，但必须把历史方案标记为已淘汰/已归档，并链接 `winner.html` 与 `ui-spec.md` 作为唯一后续输入。

## Feedback Rules

`feedback.md` 记录每轮反馈，至少包含：

- 轮次和时间。
- 保留的方向。
- 淘汰的方向和原因。
- 人类偏好：密度、层级、颜色、排版、交互、状态表达。
- 下一轮调整要求。

v1 只维护单 feature 的反馈记忆。跨 feature 的项目级 taste profile 不在默认范围内。

## UI Spec Contract

`ui-spec.md` 必须包含：

- 选定设计方向和选择理由。
- 页面/路由/组件清单。
- 页面区域、主要操作和关键交互。
- 加载、空态、错误、提交中、权限受限等关键状态。
- 与目标项目现有 frontend 模式的承接关系。
- Radix/Tailwind/已有组件的映射建议。
- `data-testid` 命名影响和 Demo 选择器注意事项。
- 需要 `/t-design` 继续处理的假设或待确认事项。

不得包含：

- 后端接口契约细节。
- 数据库设计。
- 可直接复制上线的 React 实现。
- 与 PRD 冲突的新业务规则。

## Downstream Handoff

- `/t-design`：若 `.ai/design-ui/<feature>/ui-spec.md` 存在，只读取 `ui-spec.md`，必要时读取 `winner.html` 做视觉核对；不得读取 `variants/*.html`、`archive/**` 或从 `board.html` 中抽取废弃 UI 作为设计输入。前端设计必须承接页面结构、组件映射和关键状态，并标记“基于已确认 UI 规格”。
- `/t-task`：前端任务拆分可参考 `ui-spec.md` 的组件映射和状态清单；不得从历史 variants 拆任务。
- `/t-run`：真实前端实现以 `.ai/design/<feature>.md` 为直接设计输入，必要时追溯 `ui-spec.md` 和 `winner.html`；不得实现 archive 或废弃 variants 中的 UI。

## Check Scope

检查 UI 探索产物时优先确认：

- `board.html`、variants、`winner.html`、`ui-spec.md` 路径和角色正确。
- HTML 文件无外部依赖。
- variants 有真实差异。
- `ui-spec.md` 未越界到 API、数据库或生产代码。
- `ui-spec.md` 与 PRD/用户故事不冲突。
- 收敛后 `board.html` 已回写（标注 winner、保留/并入/淘汰元素，链接 `winner.html`/`ui-spec.md`/`feedback.md`），未停留在首轮“未选择”状态。
- 收敛后 `variants/` 下没有废弃 HTML；历史候选已归档并标注不得作为设计输入。
