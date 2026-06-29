---
name: t-ui-design
description: Explore frontend UI directions for a feature after PRD check and before technical design. Generates multiple single-file HTML mockup variants, a comparison board, feedback history, winner mockup, and ui-spec handoff without using image generation, Figma, external UI tools, or production React code.
argument-hint: "[feature-name]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Task
  - Write
  - Bash
---

# 前端 UI 方案探索

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`  
需求来源边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`  
产物契约统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/ui-design-contract.md`

## 适用范围

仅在以下场景使用：

- 用户明确执行 `/t-ui-design [feature]`
- `/t-prd-check` 已通过，且 feature 有显著前端 UI 或交互体验
- 进入 `/t-design` 前，需要先通过可视化 mockup 比较多个 UI 方向

不用于：

- 纯后端、纯技术方案、无用户可见界面的需求
- 已经确定 UI 方向、只需要技术设计的需求
- 生产前端实现或代码生成
- 图片生成、Figma 设计稿生成、外部 AI UI 工具调用

## 目标

基于已检查的 PRD、Decision Brief、用户故事、既有前端规范和人类反馈，生成可审阅的 UI 方案探索产物，并收敛为 `/t-design` 可承接的 UI 规格。

输出目录：

- `.ai/design-ui/$ARGUMENTS/`

核心输出：

- `board.html`
- `variants/*.html`
- `archive/<round-or-timestamp>/`
- `feedback.md`
- `winner.html`
- `ui-spec.md`

如果未传 feature 名称，立即终止并提示：
`请提供 feature 名称。例如：/t-ui-design <feature>`

## Input Contract

上游输入：

- `.ai/decision/<feature>.md`（如存在）
- `.ai/prd/**/*.md` 中匹配 `<feature>` 的 PRD 草稿（优先）
- `docs/prd/**/*.md` 中匹配 `<feature>` 的正式 PRD
- `.ai/user-stories/**/*.md` 中匹配 `<feature>` 的 draft 用户故事
- `docs/user-stories/**/*.md` 中相关已发布用户故事
- `.ai/design/<feature>.md`（如已存在，用于迭代或补充）
- `.ai/design-ui/<feature>/feedback.md`（如已存在）
- `${CLAUDE_PLUGIN_ROOT}/guides/frontend/index.md`
- `${CLAUDE_PLUGIN_ROOT}/protocols/ui-design-contract.md`

## Output Contract

下游产出遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/ui-design-contract.md`：

- `.ai/design-ui/<feature>/board.html` — 多方案对比看板
- `.ai/design-ui/<feature>/variants/*.html` — 决策前的活跃候选 HTML mockup
- `.ai/design-ui/<feature>/archive/<round-or-timestamp>/` — 收敛后归档的历史探索稿
- `.ai/design-ui/<feature>/feedback.md` — 反馈记录
- `.ai/design-ui/<feature>/winner.html` — 选中方案
- `.ai/design-ui/<feature>/ui-spec.md` — UI 设计规格

## 核心约束

- 本 skill 是手工触发入口，不允许模型根据语义自动触发。
- 默认要求 `/t-prd-check <feature>` 已通过；如果没有可确认的 PRD 或用户故事，停止并提示先补齐上游。
- 只做 UI 方案探索，不写目标项目前端源码。
- 使用 HTML/CSS mockup，不使用图片生成。
- 所有 HTML 必须单文件、内联 CSS/JS、无外部依赖。
- 生成 variants 时必须有真实方向差异，不能只改颜色、圆角或间距。
- `ui-spec.md` 不得新增与 PRD 冲突的业务规则。
- winner 确认后，下游交接真相源只能是 `ui-spec.md` 和 `winner.html`；废弃 variants 必须归档，不得继续留在活跃 `variants/` 下。
- 如果用户反馈要求改变业务语义，先要求回到 `/t-prd` 或修正上游文档。

## 工作流程

### 1. 校验参数和输出位置

- 校验 `$ARGUMENTS` 非空。
- 文件名仅允许中文、英文、数字、空格、下划线、连字符。
- 拒绝 `..`, `/`, `\`。
- 长度限制 1 到 50 字符。
- 确保 `.ai/design-ui/$ARGUMENTS/variants/` 目录存在。

如 `.ai/design-ui/$ARGUMENTS/` 已存在：

- 若存在 `feedback.md` 但没有 `ui-spec.md`，进入 iterate 模式。
- 若存在 `ui-spec.md`，询问是否继续迭代或保持现有 winner。
- 若只有部分 HTML 产物，按当前上游和反馈重建缺失产物。

### 2. 收集上游输入

按以下顺序读取：

- `.ai/decision/$ARGUMENTS.md`（如存在）
- `.ai/prd/$ARGUMENTS.md` 或 `.ai/prd/**/$ARGUMENTS.md`
- `docs/prd/**/$ARGUMENTS.md`
- `.ai/user-stories/$ARGUMENTS.md` 或 `.ai/user-stories/**/$ARGUMENTS.md`
- `docs/user-stories/00-index.md` 与 `docs/user-stories/**/*.md` 中相关故事
- `.ai/design/$ARGUMENTS.md`（如存在）
- `.ai/design-ui/$ARGUMENTS/feedback.md`（如存在）
- `${CLAUDE_PLUGIN_ROOT}/guides/frontend/index.md`
- `${CLAUDE_PLUGIN_ROOT}/protocols/ui-design-contract.md`

如果找不到足够判断 UI 范围的 PRD、用户故事或设计输入，停止并提示先运行 `/t-prd` 与 `/t-prd-check`。

### 3. 判断是否适合 UI 探索

继续执行的条件：

- 有页面、表单、列表、仪表盘、配置、详情、对话框、工作流或其他用户可见 UI。
- UI 方向尚未明确，或人类希望比较不同方向。

跳过条件：

- 纯后端、纯脚本、纯数据迁移、纯测试、纯文档。
- PRD 明确 UI 不变。

跳过时明确说明原因，并建议直接进入 `/t-design $ARGUMENTS`。

### 4. 委派 UI 生成

通过 Task 委派 `ui-design` subagent。

初始生成 prompt 必须包含：

```text
使用 ui-design 生成首轮 UI 方案探索产物。
feature: <feature>
mode: initial
输出目录: .ai/design-ui/<feature>/
必须遵循: ${CLAUDE_PLUGIN_ROOT}/protocols/ui-design-contract.md
```

迭代 prompt 必须包含：

```text
使用 ui-design 基于 feedback.md 迭代 UI 方案探索产物。
feature: <feature>
mode: iterate
输出目录: .ai/design-ui/<feature>/
反馈文件: .ai/design-ui/<feature>/feedback.md
必须遵循: ${CLAUDE_PLUGIN_ROOT}/protocols/ui-design-contract.md
```

收敛 prompt 必须包含：

```text
使用 ui-design 收敛 UI winner 并生成 ui-spec.md。
feature: <feature>
mode: finalize
winner: <variant-name-or-path>
输出目录: .ai/design-ui/<feature>/
收敛要求: 将最终方案写入 winner.html，生成 ui-spec.md，将未选中或废弃 variants 归档到 archive/<round-or-timestamp>/，收敛后 variants/ 不得保留废弃 HTML。
必须遵循: ${CLAUDE_PLUGIN_ROOT}/protocols/ui-design-contract.md
```

### 5. 打开 board（可选，默认不打开）

生成或更新 `board.html` 后，默认不自动打开；报告 `.ai/design-ui/$ARGUMENTS/board.html` 路径与打开命令。仅当用户明确要求打开时才执行，使用 `html-show-contract.md` 的 `Opening the Preview` 中定义的命令并校验启动结果。如果无法打开，报告失败并保留文件路径。

### 6. 收集反馈

使用 `AskUserQuestion` 收集：

- 当前偏好的 variant。
- 要保留或合并的元素。
- 要去掉的元素。
- 是否需要下一轮，还是确认 winner。

将反馈追加到 `.ai/design-ui/$ARGUMENTS/feedback.md`。

如果用户确认 winner，委派 `ui-design` 生成 `winner.html` 和 `ui-spec.md`。

确认 winner 后，必须把结论回写进 `board.html`：标注选中 variant、保留/并入/淘汰的元素，并把 winner/反馈区从决策前的临时状态更新为持久记录（链接 `winner.html`/`ui-spec.md`/`feedback.md`）。收敛后的 `board.html` 必须与确认结果一致，不得停留在首轮“未选择”状态。详见 `${CLAUDE_PLUGIN_ROOT}/protocols/ui-design-contract.md` 的 Board Requirements。

确认 winner 后，还必须清理活跃候选目录：

- 将最终选中方案写入 `winner.html`，并以 `ui-spec.md` 作为 `/t-design` 的唯一文本交接规格。
- 将所有未选中或已废弃的 `variants/*.html` 移到 `.ai/design-ui/$ARGUMENTS/archive/<round-or-timestamp>/variants/`，并在归档文件显著标注 `DEPRECATED UI EXPLORATION - DO NOT USE AS DESIGN INPUT`。
- winner 来源文件也应移出或归档；收敛后的活跃视觉参考只能是 `winner.html`。
- 收敛后 `variants/` 不得保留废弃 HTML；可以为空，或只保留说明文件指向 `winner.html`、`ui-spec.md` 和 `archive/`。
- `board.html` 可以保留历史对比摘要，但必须把历史方案标记为已淘汰/已归档，不得让后续 AI 把它们当成活跃 UI。

### 7. 收尾输出

完成后说明：

- `board.html` 路径
- variants 数量和方向
- `feedback.md` 路径
- `winner.html` 和 `ui-spec.md` 路径（如已确认）
- 归档目录路径（如已确认）
- 下一步：
  - 未确认 winner：再次运行 `/t-ui-design $ARGUMENTS`
  - 已确认 winner：运行 `/t-design $ARGUMENTS`

## 质量检查清单

- variants 是否有实质差异。
- HTML 是否无外部依赖。
- 是否标注 mock data 和假设。
- `ui-spec.md` 是否只描述 UI 规格，不越界写 API/数据库/生产代码。
- `ui-spec.md` 是否能被 `/t-design` 前端章节直接承接。
- 收敛后 `board.html` 是否已回写（标注 winner、保留/并入/淘汰元素、链接 `winner.html`/`ui-spec.md`/`feedback.md`），没有停留在首轮“未选择”状态。
- 收敛后 `variants/` 是否没有废弃 HTML，历史候选是否已归档并标注不得作为设计输入。

## 失败处理

- 参数缺失：终止并给出 `/t-ui-design <feature>` 示例。
- 文件名非法：终止并说明允许字符范围。
- 上游 PRD/用户故事不足：终止并提示先补齐上游。
- 不涉及 UI：跳过并建议直接 `/t-design <feature>`。
- HTML 生成失败：终止并报告。
- 用户反馈改变业务规则：要求先修正 PRD 或 Decision Brief。

## 附加资源

- UI 设计探索契约：`${CLAUDE_PLUGIN_ROOT}/protocols/ui-design-contract.md`
- 前端规范入口：`${CLAUDE_PLUGIN_ROOT}/guides/frontend/index.md`
- UI 方案探索 subagent：`${CLAUDE_PLUGIN_ROOT}/agents/ui-design.md`
