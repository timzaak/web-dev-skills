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

会影响技术路线、依赖选择、范围边界、兼容性、成本/风险结论、PRD 建议或后续 `/t-design` 输入的问题，必须通过 `AskUserQuestion` 解决；不得只写成 P0/P1 风险、显式假设或"需要更多信息"后继续收敛。

输出文件：
- `.ai/tech-research/<file-name>.md`（file-name 取自 `$ARGUMENTS` 第一个空格前的部分）
- `.ai/decision-log/<file-name>.md`（复用上游决策并记录本阶段技术决策或已解决问题）

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

- `$ARGUMENTS` 可包含两部分：`<file-name> [补充描述]`
  - 第一个空格前的部分作为输出文件名（如 `rag-otel-metrics`）
  - 空格后的部分作为额外的需求上下文，纳入需求理解
  - 如果用户只传了一个词，则同时作为文件名和需求主题
- 文件名仅允许中文、英文、数字、下划线、连字符；推荐 kebab-case
- 拒绝 `..`, `/`, `\`
- 文件名长度限制 1 到 60 字符
- 如果用户传入的完整参数不含空格且为长中文描述（>20字符），主动提议一个简短的英文 kebab-case 文件名，经用户确认后使用
- 确保 `.ai/tech-research/` 和 `.ai/decision-log/` 存在
- 如果 `.ai/tech-research/<file-name>.md` 已存在，先询问是否覆盖

## 核心约束

- 先分析现有代码和依赖，再评估缺口；不凭空列举库
- 如果存在 `.ai/decision/<file-name>.md`，必须承接其中 Verdict、Scope Direction、D0/D1 决策和 Handoff；不得用技术预研改写产品立项结论
- 如果存在 `.ai/decision-log/<file-name>.md`，必须承接相关 Active Decision，不得重复询问 Resolved Question 或采用 Superseded Decision
- 如果已存在相关 `.ai/prd`、`.ai/user-stories` 或 published baseline，必须读取并把它们作为候选产品边界与已发布基线；不得用技术结论静默改写产品语义
- 如果 Decision Brief 的 Verdict 是 `Needs Clarification`、`Park` 或 `Reject`，除非用户明确要求技术探索，否则应停止并提示先回到 `/t-decision`
- 依赖评估必须基于真实 `Cargo.toml`、`package.json` 和 lock 文件（如存在）
- 外部搜索只用于库级事实、最佳实践和兼容性信息，不能替代本地代码分析
- Context7 优先，WebSearch 只作补充
- 影响分析中的文件路径必须使用仓库真实路径，但只到文件或模块粒度；不写具体行号、函数签名、字段名、SQL 语句、DTO 字段或中间件实现细节
- 不产出 API 接口设计、数据库设计或任务拆解
- 报告聚焦于"能否做""需要什么""影响什么"；不写成"/t-design"级别的实现说明
- 技术路线只描述方向、集成方式与依赖选择，不给出具体 schema、接口字段、路由路径、代码结构或配置项命名
- 讨论时可多方案；最终报告必须收敛为单一、明确、可执行的技术路线
- 最终报告不得保留方案对比、候选排序或"可选/视情况"等开放式描述
- 被排除方向只写成确定约束或风险，不展开对比
- 显式假设只允许用于不影响技术路线、依赖选择、范围边界、兼容性、成本/风险结论和后续交付判断的非阻塞缺口

## 工作流程

### 1. 明确需求

如果当前对话中已有足够需求背景，不要重复提问。

先按 Topic 检查 `.ai/decision-log/<file-name>.md`；已有结论直接采用。仅在需求目标、约束、技术偏好或排除项不足以支撑可行性判断且账本没有答案时，使用 `AskUserQuestion` 补问最少问题：
- 需求目标或问题陈述
- 期望的技术能力或效果
- 特定库或技术方向偏好
- 已知约束或排除项

如果缺失或冲突会影响技术路线、依赖选择、兼容性、影响范围、风险等级、是否进入 PRD 或是否可直接进入 `/t-design`，必须等待用户回答；回答前不得写入报告或给出收敛结论。

只有非阻塞缺口才可在写报告前转为 §6.2 显式假设。报告中不得留下"待确认"/"需确认"/"待定"/"TBD"等未决项。

用户回答后先更新 Decision Log，再更新 Tech Research。D2 技术取舍若不改变产品语义、风险接受、显著成本或兼容承诺，由本阶段明确选择并记录 DEC，不得留成备选路线。

### 2. 建立本地上下文

按需读取以下文件，跳过不存在的文件：
- `.ai/decision/<file-name>.md`
- `.ai/decision-log/<file-name>.md`
- `backend/Cargo.toml`
- `frontend/package.json`
- `Cargo.lock`
- `package-lock.json`
- `.ai/prd/**/*.md`
- `docs/prd/**/*.md`
- `.ai/user-stories/**/*.md`
- `docs/user-stories/**/*.md`
- `.ai/design/**/*.md`

扫描真实代码目录，重点关注：
- `backend/api/`
- `backend/core/`
- `backend/sdk/`
- `frontend/src/`

如果代码分析较复杂，可委托探索任务，要求返回相关实现位置、可复用点、影响模块和理由。

### 3. 分析差距

对比需求与现状，明确：
- 现有栈已覆盖的能力
- 需要新增或升级的依赖
- 可能需要替换的依赖
- 版本兼容性问题
- 现有代码需要修改的部分

### 4. 调研新依赖

仅当本地分析表明需要新依赖或需要补充库级事实时执行。

对每个候选库调研：
- 核心用法和 API 概览
- 与目标项目技术栈的集成方式
- 版本迁移注意事项（如适用）
- 常见陷阱、限制和兼容性问题
- 推荐版本和引入方式

如果不需要新依赖，在报告中写明"现有依赖栈可满足需求"并说明理由。

### 5. 决策收敛

把本地分析、依赖调研和人类讨论收敛为一个最终技术路线。

收敛规则：
- 只把最终选定的依赖、集成方式、影响范围和风险写入报告
- 不保留候选比较、备选路线或"可二选一"表达
- 因技术事实不足无法收敛时，结论可写"需要更多信息"，并列出需要继续调研的技术证据
- 因用户决策不足无法收敛时，必须使用 `AskUserQuestion` 提问；回答前不得把结论写成"需要更多信息"并继续交付
- 已排除方向只作为确定约束或风险写入

### 6. 生成影响分析

输出文件级和架构级影响：
- 需要新增或修改的文件
- 可能受影响的配置文件和测试文件
- 需要调整的模块边界、接口契约、数据流或全局配置
- 风险矩阵，风险等级使用 P0/P1/P2

### 7. 写入报告

使用 [template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-tech-research/template.md) 的结构生成 `.ai/tech-research/<file-name>.md`。

如果某章节不适用，保留章节并标记"不适用"及原因，不要直接删除。

报告必须包含 Decision Trace，逐项说明相关 Active Decision 的应用位置。写入后运行：

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/check-decision-closure.py .ai/tech-research/<file-name>.md
```

扫描命中时按 Decision Exposure Gate 分类并处理；重新扫描通过前不得交付报告。

## 收尾输出

完成后说明：
- 报告路径
- 可行性结论（可行 / 有条件可行 / 需更多信息 / 不建议）
- 需要引入的新库数量和名称（如适用）
- 主要影响范围
- 关键风险点
- 下一步命令：尚无 PRD 草稿的业务功能进入 `/t-prd <file-name>`；已有 PRD 草稿且预研结论改变范围、业务规则、用户流程或验收目标时，重跑 `/t-prd <file-name>` 更新草稿；二者已收敛时可按风险进入 `/t-prd-check <file-name>` 或 `/t-design <file-name>`；不涉及业务逻辑变动的纯技术方案可直接进入 `/t-design <file-name>`

## 质量门禁

生成前自检：
- 是否基于真实依赖文件做盘点
- 是否优先从现有依赖和代码中寻找方案
- 外部库调研是否覆盖核心 API、集成方式和已知限制
- 是否已收敛为单一明确技术路线
- 是否移除了方案对比、候选排序和开放式选择
- 报告是否不含任何"待确认"/"需确认"/"待定"/"TBD"等未决项；阻塞性未确认信息是否已通过 `AskUserQuestion` 解决，非阻塞缺口是否已转为显式假设
- 是否 `needs_user_answer=0`、通过决策闭合扫描，并对相关 Active Decision 提供 Decision Trace
- PRD 创建/更新建议是否明确可执行；如不涉及业务逻辑变动，是否说明可直接进入 `/t-design`
- 如存在 Decision Brief，是否没有偏离其目标用户、范围方向和已确认产品决策
- 如存在 PRD 草稿或 published baseline，是否已读取且没有静默改写产品语义；需要改变产品语义时是否明确交回 `/t-prd` 更新
- 影响分析中的路径是否真实存在
- 可行性判定是否明确
- 风险评估是否区分 P0/P1/P2
- 是否避免替代 `/t-design` 和 `/t-task` 的职责

## 失败处理

- 参数缺失：终止并给出 `/t-tech-research <file-name>` 示例
- Decision Brief 明确 `Reject` / `Park` 且用户未要求继续探索：终止并提示先回到 `/t-decision`
- 文件名非法：终止并说明允许字符范围
- 无法创建输出目录或写文件：终止并报告
- 需求描述不足：若影响可行性或路线判断，使用 `AskUserQuestion` 补齐，回答前不写报告；若不影响，只在报告中写入显式假设
- 决策闭合扫描失败：按 Decision Exposure Gate 分类；需要用户裁决时提问并停止，修正后重新扫描
- 既无代码库也无依赖文件：继续，但标记"无法评估现有实现，仅基于需求分析"
- Context7 查询无结果：降级到 WebSearch，在报告中标注信息来源
- WebSearch 也无结果：在报告中标记"外部信息不可用，依赖本地分析"
