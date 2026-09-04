---
name: t-dream
description: Organize and realign PRDs, user stories, design/task docs, implementation facts, and project structure so the target project keeps a clean current context instead of accumulating stale or misleading information. Use when asked to audit documentation drift, structure drift, traceability gaps, whether PRD/code/test/demo directory organization and module boundaries are reasonable, or to merge/prune/rewrite PRDs into concise current authority sources.
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Task
  - Write
  - Agent
---

# 上下文整理与工程事实重组

运行时边界：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`（写报告或调用目标项目脚本前读）
需求来源边界：`${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`（区分草稿与已发布需求来源时读）
候选问题结构、评分权重、报告结构和模式写入边界：`${CLAUDE_PLUGIN_ROOT}/protocols/dream-report-contract.md`（构造 subagent 输出、计算评分或写报告前读）

## 目标
- 把 PRD、用户故事、设计、任务、Demo 注释、实现事实和项目结构重新收敛成当前可信上下文。
- 识别并减少错误信息累积：重复 PRD、历史过程文档、过期术语、失效设计、冲突业务规则、错误能力承诺和误导性实现说明。
- 评估 PRD 目录、代码目录、模块边界、测试布局、Demo 布局、`.ai/` 运行时产物组织是否合理，是否支持后续 AI agent 快速定位、窄范围修改和可靠验证。
- 建立 PRD -> 用户故事 -> 设计/任务 -> 代码 -> 测试/Demo 的 traceability 视图，指出断链、错链、重复链和缺失证据。
- 对比 PRD 与实现事实，检查能力边界、模型约束、校验、权限、业务逻辑、前端可见行为和 Demo 覆盖事实的差异。
- 通过专用 subagent 和多个 `general_agent` 按维度并行检查，主流程只负责编排、验证、合并、裁决和必要写入。
- 输出可追溯证据、差异分级和应修正文档还是实现的建议。

`t-dream` 聚焦目标项目当前上下文是否干净、可信、结构合理，并能继续支撑后续 AI 编程流程。

## 参数
| 参数 | 说明 |
|---|---|
| `[feature]` | 可选。聚焦指定功能、模块或领域关键词 |
| `--all` | 检查全部可识别 PRD / 模块 |
| `--deep` | 启用后端模块级深度一致性检查 |
| `--backend-only` | 只执行 PRD 与后端实现一致性检查（隐含 `--deep`） |
| `--govern-prd` | 显式进入 PRD 治理写入模式 |

默认模式是只读 audit，不修改目标项目文档或代码。未传入 `[feature]` 或 `--all` 时，先提示可用模块来源是 `docs/prd/**/*.md`，再建议用户指定范围。

用户只要求"检查/评估/排查准确性"时，保持只读 audit 模式；删除是高风险操作，见"PRD 治理模式"。

## 输入范围
- PRD：`docs/prd/**/*.md`（排除模板、索引和说明文件）
- 用户故事：`docs/user-stories/**/*.md`、`.ai/user-stories/**/*.md`
- PRD 草稿：`.ai/prd/**/*.md`
- 设计与任务：`.ai/design/**/*.md`、`.ai/task/**`
- Demo 测试：Web 为 `demo/e2e/**/*.e2e.ts`，Flutter 为 `patrol_test/**/*_test.dart`
- 实现代码：按目标项目真实结构定位 backend、frontend、demo 相关实现
- 项目结构：`docs/`、`.ai/`、backend/frontend/demo/test 目录、README、AGENTS/CLAUDE 类上下文入口、ADR 或架构说明（如存在）

## 执行模型

`t-dream` 是主控编排 skill，不应由主线程独自完成所有检查。主线程负责确定范围、构造共享上下文、并行启动 subagent、验证候选问题、合并结果、写入最终报告，并在 PRD 治理模式下执行经过验证的文档改动。

整体采用类似 code review 的两阶段机制：
- 并行发现：专用 subagent 与多个 `general_agent` 从不同维度独立发现候选问题。
- 统一验证：主线程或专门的验证 subagent 根据真实文件证据过滤误报、去重、定级和评分。

模式语义（`audit` / `govern-prd` / `backend-only` / `deep` 的写入边界和覆盖范围）以 `${CLAUDE_PLUGIN_ROOT}/protocols/dream-report-contract.md` 的模式表为准。补充约定：
- 默认聚焦 context health：当前上下文是否准确、收敛、可导航、可追踪、结构上可持续。措辞、格式、风格偏好仅在导致业务含义失真、查找成本显著增加或后续 agent 容易误用时进入问题清单。
- `govern-prd` 先完成 audit 和治理计划，再按计划改写 PRD、索引和引用。
- `backend-only` 适合实现阶段收口，不输出上下文治理或结构组织结论。

`--all` 预算策略：
- 默认先做索引级健康扫描：PRD 文件、标题、索引引用、用户故事引用、draft story 引用、设计/任务入口、明显重复/过期关键词和结构入口。
- 只对高风险模块深挖。高风险信号包括：索引缺失、同名/近义 PRD 重复、用户故事或 Demo 指向旧 PRD、PRD 声明和代码关键词明显错位、权限/租户/状态规则冲突信号。
- 若用户要求全量深挖，必须显式使用 `--all --deep`。

## PRD 治理模式

当用户请求整理、合并、精简、删除过期过程文档或更新 PRD 结构，或显式传入 `--govern-prd` 时，进入 PRD 治理模式（写入模式，可修改 `docs/prd/**`、相关索引和必要引用，但不得修改实现代码）。

- 治理原则、流程（盘点 → 设计合并目标 → 编写新权威 PRD → 归档/删除旧 PRD → 更新引用 → 验证）和合并判定读取 `${CLAUDE_PLUGIN_ROOT}/guides/product/prd-governance.md`。
- 删除是高风险操作：除非用户明确说"删除旧 PRD / 删除过期文档"，否则默认归档到 `docs/prd/archive/...` 或生成合并计划，不直接删除文件。
- 治理输出结构遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/dream-report-contract.md` 的 PRD Governance Output。
- 主线程必须对治理改动二次验证后才执行写入。

## 并行 subagent 维度

默认按以下维度并行调用 subagent：

| 维度 | subagent 任务 |
|---|---|
| PRD 上下文治理 | 使用 `context-curator` 识别重复、过期、冲突、过程化和非权威 PRD 内容 |
| 结构组织评估 | 使用 `structure-review` 评估 PRD、代码、测试、Demo、`.ai/` 目录和模块边界是否合理 |
| PRD 描述准确性 | 使用 `general_agent` 提取关键 PRD 声明，并核对是否被实现事实支撑；默认 audit 只做高风险声明抽样 |
| 用户故事与验收描述 | 核对用户故事、GWT、验收标准是否与 PRD 和实现一致 |
| Demo 描述与覆盖事实 | 核对 Demo 测试注释、故事映射、断言和实际覆盖是否准确 |
| 后端实现一致性 | 检查 API 能力边界、模型、校验、权限、业务逻辑 |
| 前端实现一致性 | 核对页面、组件、交互、权限可见性与 PRD/故事描述是否一致 |
| Traceability | 核对 PRD -> 用户故事 -> 设计/任务 -> 代码 -> 测试/Demo 链路是否存在断链、错链或重复链 |
| 候选问题验证 | 复核各维度候选问题是否有文件定位、真实证据、合理分级和修复方向 |

`--backend-only` 只启动"后端实现一致性""后端深度一致性"和"候选问题验证"。`--deep` 在"后端实现一致性"之外，额外按模块调用 `backend-consistency` 做专项深度检查。`backend-consistency` 在 `t-dream` 调用下必须只返回结构化结果，不自行写入独立一致性报告。

### subagent 调用要求
- 使用 `Task` 或 `Agent` 启动 `subagent_type="context-curator"`、`subagent_type="structure-review"`、`subagent_type="general_agent"`；调用按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 执行，`general_agent` 为内置 agent，按协议跳过注入。
- 各 subagent 必须只读检查，不修改代码或文档；只输出候选问题，不直接决定最终报告结论。
- 各 subagent 必须接收同一份共享上下文包，保持检查范围一致；并行执行时各维度结论互不污染，冲突由主线程在汇总阶段处理。
- 候选问题字段、置信度阈值和"专项 agent 可增加的字段"以 `${CLAUDE_PLUGIN_ROOT}/protocols/dream-report-contract.md` 为准；最终 P0/P1 必须经过验证且置信度不低于 80。

共享上下文包必须包含：
- 检查范围：`[feature]` / `--all` / `--backend-only` / `--deep` / `--govern-prd`。
- PRD 文件列表和目标模块列表。
- 相关用户故事、Demo 测试和实现检索路径。
- 设计、任务、README、AGENTS/CLAUDE、ADR 或架构说明路径（如存在）。
- 上下文健康判定规则、结构组织判定规则、描述准确性判定规则、P0/P1/P2/P3 分级规则和 `${CLAUDE_PLUGIN_ROOT}/protocols/dream-report-contract.md` 报告格式要求。
- 当前目标是整理和重组当前工程上下文。

## 执行流程

### 1. 确定检查范围
- 解析 `[feature]`、`--all`、`--deep`、`--backend-only`、`--govern-prd`。
- 创建 `.ai/quality/`（如不存在）。
- `--all`：扫描 `docs/prd/**/*.md` 自动提取模块名；默认先做索引级健康扫描，只对高风险模块继续深挖。
- `[feature]`：优先匹配 PRD 文件名；若不存在精确文件，按标题、路径、模块名、用户故事引用和测试注释进行模糊定位。
- 校验 PRD 存在；不存在时记录 P1，并列出可用 PRD 来源。

### 2. 构造共享上下文包
主线程先做轻量扫描，不做最终判断：

- 收集 PRD、用户故事、Demo 测试和候选实现文件路径。
- 收集设计、任务、README、AGENTS/CLAUDE、ADR 或架构说明路径。
- 提取模块名、角色名、故事引用、测试引用和关键词。
- 提取目录结构摘要：PRD 分组、backend/frontend/demo/test 主要模块、`.ai/design` 与 `.ai/task` 对应关系。
- 写明本次检查模式、排除项和无法定位的输入。
- 将上下文包传给所有参与的 subagent。

### 3. 并行评估上下文与结构健康
默认先启动两个专项只读 agent：

- `context-curator`：判断 PRD、用户故事、设计、任务、Demo 注释中哪些是当前权威事实，哪些是历史过程、重复描述、冲突规则、过期术语或容易误导 agent 的上下文。
- `structure-review`：判断文档目录、代码目录、模块边界、测试布局、Demo 布局和运行时产物是否支持快速定位、窄范围修改和可靠验证。

专项 agent 只输出候选问题和整理建议，不直接修改文件。PRD 治理模式下，主线程必须二次验证后再执行写入。

### 4. 并行提取"描述声明"与"实现事实"
从 PRD、用户故事和 Demo 测试中提取可核验声明，并按目标项目真实结构定位实现。提取类别（能力边界、数据与状态、验证规则、权限与租户边界、业务流程、验收描述）、实现事实定位指引和后端模块检查的输入规则统一按 `${CLAUDE_PLUGIN_ROOT}/protocols/dream-report-contract.md` 的"提取类别与差异分级"执行。

### 5. 并行对比描述与事实
逐项判断每个描述声明是否准确；差异的 P0/P1/P2 分级和"修正文档 / 修正实现 / 需确认"判定统一按 `${CLAUDE_PLUGIN_ROOT}/protocols/dream-report-contract.md` 的"差异分级"执行。

### 6. Traceability 检查
检查 PRD、用户故事、设计、任务、实现、测试、Demo 之间是否存在可追踪关系：

- PRD 中的核心能力应能找到用户故事、设计或任务承接；缺失时记录为 P1 或 P2。
- 用户故事或 Demo 测试引用的能力应能找到当前权威 PRD；找不到或引用过期 PRD 时记录为 P1。
- 设计/任务描述的模块和代码目录应能相互定位；无法定位时记录为 P1。
- 测试或 Demo 覆盖应能回连到对应用户故事或验收目标；断链时记录为 P1 或 P2。
- 重点检查产品能力、模块边界、验收路径和关键业务规则的追踪关系。

### 7. 后端深度一致性
默认后端维度由 `general_agent` 完成证据提取和对比；在 `--deep` 或 `--backend-only` 时，对每个后端模块额外调用 `backend-consistency`。

按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 通过 `Agent(subagent_type="backend-consistency")` 启动，prompt 必须包含：
- 模块名。
- PRD 路径；路径来自 `docs/prd/**/*.md` 的实际匹配结果。
- 当前检查范围。
- `t-dream` 调用标记：只读返回，不写入 `.ai/quality/consistency-*` 独立报告。
- 要求输出 API 能力边界、数据模型、验证规则、权限、业务逻辑五个维度评分。
- 要求标明每条差异应修正文档、实现还是需要产品确认。

agent 失败时记录失败模块为 P1，并继续其他模块（`--all` 模式）。

### 8. 候选问题验证
并行发现结束后，必须进行验证步骤。验证可由主线程完成，也可额外启动一个 `general_agent` 作为"候选问题验证"维度。

验证动作：
- 重新读取关键文件片段，确认描述声明和实现事实是否真实存在。
- 过滤没有文件定位、证据不足、只属于风格偏好的候选问题。
- 校准严重级别和置信度。
- 合并重复问题，保留最具体的文件位置和证据。
- 判断修复方向是修正文档、修正实现还是产品确认。
- 低置信度但值得关注的问题放入"未能确认"。

### 9. 主线程合并与裁决
所有 subagent 返回后，主线程执行汇总：

- 合并验证后的问题，保留最具体的文件位置和证据。
- 对冲突结论进行二次读取验证；无法裁决时标记为"产品确认"。
- 校验每个 P0/P1/P2 是否有文档位置、实现证据和修复方向。
- 重新计算总分；不得直接平均 subagent 分数。
- 检查是否存在 subagent 漏跑、范围不一致或输出结构不合格；存在时记录为 P1。

### 10. 评分计算与写入报告
评分权重（默认 audit / deep / backend-only）与报告结构以 `${CLAUDE_PLUGIN_ROOT}/protocols/dream-report-contract.md` 为准，不得在此另立第二套权重。

写入 `.ai/quality/dream-check-[YYYYMMDD-HHMMSS].md`。默认 audit 的实现一致性分只对已抽样核验的关键声明负责；报告中必须列出抽样范围和未覆盖范围，不得暗示已完成全量实现审计。

## 失败处理
- 参数为空且无法确定范围：提示使用 `/t-dream [feature]` 或 `/t-dream --all`。
- 找不到 PRD：标记 P1，并列出检索路径。
- 找不到相关用户故事或 Demo 测试：标记 P1，但继续检查 PRD 与实现。
- 找不到实现证据：标记 P1 或 P2，并说明检索路径和关键词。
- 任一 subagent 调用失败：记录对应维度为 P1，继续合并其他维度。
- subagent 输出结构不合格：主线程补充最小必要复核，并将该维度标记 P1。
- 候选问题验证未执行：不得生成 ACCEPTABLE / PASS 类结论，只能输出阻塞报告。
- 深度检查 agent 失败：标记 P1，记录失败模块和错误摘要。
- 报告写入失败：停止并提示检查 `.ai/quality/` 权限。

## 质量门禁
- 只读检查；除写入质量报告外，不修改目标项目代码或文档。
- 所有差异项必须可定位到文件或 PRD 条目；所有统计项必须有数据来源。
- 每个参与评分的维度必须有对应 subagent 输出；未执行时必须说明原因。
- 最终 P0/P1 问题必须经过验证步骤，且置信度不低于 80。
- 评分公式必须可复算，分项分值之和必须等于总分。
- 报告必须落盘。
- PRD 只承载产品规则、能力边界和验收目标；接口或路由说明问题作为描述准确性问题单独记录。
