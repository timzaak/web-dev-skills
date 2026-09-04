---
name: t-tech-research
description: Assess technical feasibility for a feature. Scans codebase, checks dependencies, researches libraries, and writes a structured report under .ai/tech-research/.
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Task
  - Write
  - Bash
  - WebSearch
  - mcp__context7__resolve-library-id
  - mcp__context7__query-docs
---

# 需求技术预研

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`
需求来源边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`
跨阶段决策连续性和用户决策暴露统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`

## 目标

基于 Decision Brief、用户需求、已有 PRD / user story（如存在）和现有代码库，评估技术可行性、依赖缺口、代码影响范围和关键风险，生成报告供 `/t-prd` 创建或更新草稿，或供纯技术方案 `/t-design` 参考。

决策纪律（全文只在此声明一次）：会影响技术路线、依赖选择、范围边界、兼容性、成本/风险结论、PRD 建议或后续 `/t-design` 输入的问题，先按 Topic 查 `.ai/decision-log/<file-name>.md`；仍未解决时用 `AskUserQuestion` 提问，回答前不得写入报告、给出收敛结论或把它写成 P0/P1 风险、显式假设、"需要更多信息"后继续。用户回答后先更新 Decision Log，再更新 Tech Research。D2 技术取舍由本阶段明确选择并写入 Tech Research；符合 Entry Gate 时才回写 Decision Log。

输出文件：
- `.ai/tech-research/<file-name>.md`（file-name 取自 `$ARGUMENTS` 第一个空格前的部分）
- `.ai/decision-log/<file-name>.md`（复用上游决策；仅在产生用户决策、问题状态变化或重要 AI 决策时更新）

如果未传 feature 名称，立即终止并提示：
`请提供 feature 名称。例如：/t-tech-research user-management`

## 输入与输出

输入：
- `.ai/decision/<file-name>.md`（可选但推荐，来自 `/t-decision`）
- `.ai/decision-log/<file-name>.md`（存在时必须在任何提问前读取）
- 用户原始需求描述（参数、当前对话或补问获取）
- 现有代码库
- 可选：`.ai/prd/**/*.md`、`docs/prd/**/*.md`、`.ai/user-stories/**/*.md`、`docs/user-stories/**/*.md`、`.ai/design/**/*.md`

输出报告必须包含：
- 需求理解与技术需求提取
- 现有代码库评估（依赖和可复用模块）
- 差距分析
- 库调研与最佳实践（如适用）
- 影响分析
- 可行性判定
- PRD 创建/更新建议
- 纯技术方案设计建议（如不涉及业务逻辑变动）
- 参考资料

## 参数规则

- `$ARGUMENTS` 可包含两部分：`<file-name> [补充描述]`；第一个空格前的部分作为输出文件名（如 `rag-otel-metrics`），空格后的部分作为额外需求上下文；只传一个词时同时作为文件名和需求主题
- 确保 `.ai/tech-research/` 和 `.ai/decision-log/` 存在
- 如果 `.ai/tech-research/<file-name>.md` 已存在，先询问是否覆盖

## 核心约束

- 先分析现有代码和依赖，再评估缺口；不凭空列举库
- 如果存在 `.ai/decision/<file-name>.md`，必须承接其中 Verdict、Scope Direction、D0/D1 决策和 Handoff，不得用技术预研改写产品立项结论；Verdict 为 `Needs Clarification`、`Park` 或 `Reject` 时，除非用户明确要求技术探索，否则停止并提示先回到 `/t-decision`
- 如果存在 `.ai/decision-log/<file-name>.md`，必须承接相关 Active Decision，不得重复询问 Resolved Question 或采用 Superseded Decision
- 如果已存在相关 `.ai/prd`、`.ai/user-stories` 或 published baseline，必须读取并把它们作为候选产品边界与已发布基线；不得用技术结论静默改写产品语义，需要改变时明确交回 `/t-prd` 更新
- 依赖评估必须基于真实 `Cargo.toml`、`package.json` 和 lock 文件（如存在）
- 外部搜索只用于库级事实、最佳实践和兼容性信息，不能替代本地代码分析；Context7 优先，WebSearch 只作补充
- 影响分析中的文件路径必须使用仓库真实路径，但只到文件或模块粒度
- 不产出 API 接口设计、数据库设计或任务拆解；报告聚焦于"能否做""需要什么""影响什么"；技术路线只描述方向、集成方式与依赖选择，不给出具体 schema、接口字段、路由路径、代码结构或配置项命名
- **收敛规则**：讨论时可多方案，最终报告必须收敛为单一、明确、可执行的技术路线；不保留方案对比、候选排序或"可选/视情况"等开放式描述，被排除方向只写成确定约束或风险。报告中不得留下"待确认"/"需确认"/"待定"/"TBD"等未决项；显式假设只允许用于不影响技术路线、依赖选择、范围边界、兼容性、成本/风险结论和后续交付判断的非阻塞缺口

## 工作流程

### 1. 明确需求

如果当前对话中已有足够需求背景，不要重复提问。按决策纪律检查账本后，仅在需求目标、约束、技术偏好或排除项不足以支撑可行性判断且账本没有答案时，用 `AskUserQuestion` 补问最少问题（需求目标或问题陈述、期望的技术能力或效果、特定库或技术方向偏好、已知约束或排除项）。

### 2. 建立本地上下文

按需读取此项目的依赖和相关代码；代码分析复杂时可委托探索任务，要求返回相关实现位置、可复用点、影响模块和理由。

### 3. 分析差距

对比需求与现状，明确：现有栈已覆盖的能力、需要新增或升级的依赖、可能需要替换的依赖、版本兼容性问题、现有代码需要修改的部分。

### 4. 调研新依赖

仅当本地分析表明需要新依赖或需要补充库级事实时执行。对每个候选库调研：核心用法和 API 概览、与目标项目技术栈的集成方式、版本迁移注意事项（如适用）、常见陷阱和兼容性问题、推荐版本和引入方式。不需要新依赖时，在报告中写明"现有依赖栈可满足需求"并说明理由。

### 5. 决策收敛

把本地分析、依赖调研和人类讨论收敛为一个最终技术路线，按核心约束的收敛规则写入。两种无法收敛的情形分开处理：因技术事实不足时，结论可写"需要更多信息"并列出待调研证据；因用户决策不足时，按决策纪律提问，不得以"需要更多信息"代替提问后继续交付。

### 6. 生成影响分析

输出文件级和架构级影响：需要新增或修改的文件、可能受影响的配置和测试文件、需要调整的模块边界/接口契约/数据流/全局配置、风险矩阵（P0/P1/P2）。

### 7. 写入报告

使用 [template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-tech-research/template.md) 的结构生成 `.ai/tech-research/<file-name>.md`。不适用章节保留并标记"不适用"及原因。报告必须包含 Decision Trace，逐项说明相关 Active Decision 的应用位置。写入后运行：

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/check-decision-closure.py .ai/tech-research/<file-name>.md
```

命中项按 Decision Exposure Gate 分类处理；重新扫描通过前不得交付报告。

## 收尾输出

完成后说明：
- 报告路径
- 可行性结论（可行 / 有条件可行 / 需更多信息 / 不建议）
- 需要引入的新库数量和名称（如适用）
- 主要影响范围和关键风险点
- 下一步命令：尚无 PRD 草稿的业务功能进入 `/t-prd <file-name>`；已有 PRD 草稿且预研结论改变范围、业务规则、用户流程或验收目标时，重跑 `/t-prd` 更新草稿；二者已收敛时可按风险进入 `/t-prd-check` 或 `/t-design`；不涉及业务逻辑变动的纯技术方案可直接进入 `/t-design <file-name>`

## 质量门禁

- 基于真实依赖文件（`Cargo.toml`、`package.json`、lock 文件）做盘点，并优先从现有依赖和代码中寻找方案
- 已收敛为单一明确技术路线，无候选对比、开放式描述和未决项；阻塞性未确认信息已按决策纪律解决，非阻塞缺口已转为显式假设
- `needs_user_answer=0`、决策闭合扫描通过，并对相关 Active Decision 提供 Decision Trace
- 影响分析中的路径真实存在；可行性判定明确；风险区分 P0/P1/P2

## 失败处理

- 参数缺失或文件名非法：终止并给出示例或说明允许字符范围
- Decision Brief 明确 `Reject` / `Park` 且用户未要求继续探索：终止并提示先回到 `/t-decision`
- 无法创建输出目录或写文件：终止并报告
- 需求描述不足：按决策纪律处理（影响判断时补问并停止；不影响时只写显式假设）
- 既无代码库也无依赖文件：继续，但标记"无法评估现有实现，仅基于需求分析"
- Context7 查询无结果：降级到 WebSearch，在报告中标注信息来源；WebSearch 也无结果时标记"外部信息不可用，依赖本地分析"
