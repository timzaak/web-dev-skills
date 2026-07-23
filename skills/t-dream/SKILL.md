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

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`。需求来源边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`。候选问题、评分和报告结构统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/dream-report-contract.md`。

## 目标
- 把 PRD、用户故事、设计、任务、Demo 注释、实现事实和项目结构重新收敛成当前可信上下文。
- 识别并减少错误信息累积：重复 PRD、历史过程文档、过期术语、失效设计、冲突业务规则、错误能力承诺和误导性实现说明。
- 评估 PRD 目录、代码目录、模块边界、测试布局、Demo 布局、`.ai/` 运行时产物组织是否合理，是否支持后续 AI agent 快速定位、窄范围修改和可靠验证。
- 建立 PRD -> 用户故事 -> 设计/任务 -> 代码 -> 测试/Demo 的 traceability 视图，指出断链、错链、重复链和缺失证据。
- 对比 PRD 与实现事实，检查能力边界、模型约束、校验、权限、业务逻辑、前端可见行为和 Demo 覆盖事实的差异。
- 通过专用 subagent 和多个 `general_agent` 按维度并行检查，主流程只负责编排、验证、合并、裁决和必要写入。
- 输出可追溯证据、差异分级和应修正文档还是实现的建议。
- 在用户明确要求“整理 PRD / 合并 PRD / 删除过期过程文档 / 精简为权威需求源”时，执行 PRD 治理模式：合并重复文档、删除过期迭代记录、更新索引和引用，并用链接检查验证。

`t-dream` 聚焦目标项目当前上下文是否干净、可信、结构合理，并能继续支撑后续 AI 编程流程。

PRD 治理模式只保留当前产品规则、用户可见契约、范围边界和验收目标，删除或降级已经被实现过程替代的临时方案、迁移过程和重复技术细节。

## 使用方式
```bash
/t-dream realm
/t-dream --all
/t-dream realm --deep
/t-dream realm --backend-only
/t-dream realm --govern-prd
/t-dream 整理 document PRD
/t-dream 合并 infrastructure PRD
```

## 参数
| 参数 | 说明 |
|---|---|
| `[feature]` | 可选。聚焦指定功能、模块或领域关键词 |
| `--all` | 检查全部可识别 PRD / 模块 |
| `--deep` | 启用后端模块级深度一致性检查 |
| `--backend-only` | 只执行 PRD 与后端实现一致性检查 |
| `--govern-prd` | 显式进入 PRD 治理写入模式 |

默认模式是只读 audit：包含上下文整理、结构组织评估、traceability 和轻量描述/实现一致性抽样，不修改目标项目文档或代码。`--deep` 才启用模块级后端深度一致性检查。`--backend-only` 隐含 `--deep`，并跳过 PRD 治理和前端/Demo/结构维度。未传入 `[feature]` 或 `--all` 时，先提示可用模块来源是 `docs/prd/**/*.md`，再建议用户指定范围。

当用户请求整理、合并、精简、删除过期过程文档或更新 PRD 结构，或显式传入 `--govern-prd` 时，进入 PRD 治理模式。PRD 治理模式是写入模式，可以修改 `docs/prd/**`、相关索引和必要引用，但不得修改实现代码。用户只要求“检查/评估/排查准确性”时，保持只读 audit 模式。

删除是高风险操作：除非用户明确说“删除旧 PRD / 删除过期文档”，否则 PRD 治理默认归档到 `docs/prd/archive/...` 或生成合并计划，不直接删除文件。

## 输入范围
- PRD：`docs/prd/**/*.md`（排除模板、索引和说明文件）
- 用户故事：`docs/user-stories/**/*.md`、`.ai/user-stories/**/*.md`
- PRD 草稿：`.ai/prd/**/*.md`
- 设计与任务：`.ai/design/**/*.md`、`.ai/task/**`
- Demo 测试：`demo/e2e/**/*.e2e.ts`
- 实现代码：按目标项目真实结构定位 backend、frontend、demo 相关实现
- 项目结构：`docs/`、`.ai/`、backend/frontend/demo/test 目录、README、AGENTS/CLAUDE 类上下文入口、ADR 或架构说明（如存在）
- PRD 上下文治理：复用 `context-curator` agent
- 结构组织评估：复用 `structure-review` agent
- 后端深度检查：复用 `backend-consistency` agent

## 执行模型

`t-dream` 是主控编排 skill，不应由主线程独自完成所有检查。主线程负责确定范围、构造共享上下文、并行启动 subagent、验证候选问题、合并结果、写入最终报告，并在 PRD 治理模式下执行经过验证的文档改动。

整体采用类似 code review 的两阶段机制：
- 并行发现：专用 subagent 与多个 `general_agent` 从不同维度独立发现候选问题。
- 统一验证：主线程或专门的验证 subagent 根据真实文件证据过滤误报、去重、定级和评分。

默认聚焦 context health：当前上下文是否准确、收敛、可导航、可追踪、结构上可持续。措辞、格式、风格偏好仅在导致业务含义失真、查找成本显著增加或后续 agent 容易误用时进入问题清单。

模式边界：
- `audit`（默认）：只读审计，写入 `.ai/quality/dream-check-[YYYYMMDD-HHMMSS].md`。对实现一致性只做关键声明抽样，不追求全量代码覆盖。
- `govern-prd`：先完成 audit 和治理计划，再按计划改写 PRD、索引和引用；默认归档旧文档，只有用户明确要求删除时才删除。
- `backend-only`：只检查 PRD 与后端实现一致性，适合实现阶段收口；不输出上下文治理或结构组织结论。
- `deep`：在 audit 的基础上，对选中模块额外调用 `backend-consistency` 做后端深度检查。

`--all` 预算策略：
- 默认先做索引级健康扫描：PRD 文件、标题、索引引用、用户故事引用、draft story 引用、设计/任务入口、明显重复/过期关键词和结构入口。
- 只对高风险模块深挖。高风险信号包括：索引缺失、同名/近义 PRD 重复、用户故事或 Demo 指向旧 PRD、PRD 声明和代码关键词明显错位、权限/租户/状态规则冲突信号。
- 若用户要求全量深挖，必须显式使用 `--all --deep`。

## PRD 治理模式

当用户要求整理 PRD 时，目标是让 `docs/prd/**` 成为当前权威需求源。执行时遵守以下原则：

- 先读后写：先读取目标目录的所有 PRD、`docs/prd/00-index.md`、总览/领域模型、相关已发布用户故事、相关 draft 用户故事和明显相关实现事实。
- 合并按稳定能力命名。例如 document 可收敛为 lifecycle / ingestion / retrieval-and-citations；infrastructure 可收敛为 storage / model-providers / observability / auth。
- 权威 PRD 只写当前规则：用户价值、范围、业务规则、状态、API 用户可见约束、验收目标、参考资料。
- 删除或压缩过程性内容：技术迁移步骤、依赖升级过程、旧实现替换流水账、已落地的临时方案、代码文件清单、数据库建表细节。
- 重复旧文档按用户授权归档或删除。未明确允许删除时，旧文档默认归档并标注非权威；用户明确允许删除时，才能删除被合并的旧迭代 PRD。
- 代码现状只用于校验当前事实；产品规则仍以当前需求判断表达。
- 冲突规则按更具体、更新、已实现或已被索引标为权威的来源裁决，并在新 PRD 中只保留裁决后的规则。
- 保持链接可达：更新 `docs/prd/00-index.md`、总览、领域模型、聊天 PRD、用户故事引用和相关 PRD 参考。
- 写入治理时先区分 `.ai/user-stories` 候选来源与 `docs/user-stories` 已发布基线；不得把 draft story 静默当成已发布事实。

### PRD 治理流程

1. **盘点范围**
   - 列出目标目录下 PRD 文件、大小、标题和状态。
   - 用 grep 查找重复或过期信号：`row_index`、`indexed`、`仅支持 xlsx`、旧 provider 名、旧存储名、`当前`、`迁移`、`实现`、`替换`。
   - 区分当前权威规则、历史背景和纯过程记录。

2. **设计合并目标**
   - 为每个能力域定义 2-5 个稳定权威 PRD。
   - 每个旧 PRD 必须映射到一个新 PRD、确认归档或在用户明确授权下确认删除。
   - 保留边界清晰的独立安全/集成 PRD，例如 API Token、Widget。
   - 写入前输出合并 / 归档 / 删除映射表；如存在待产品裁决的冲突，先列为决策项。

3. **编写新权威 PRD**
   - 每份新 PRD 使用紧凑结构：
     - 标题、状态、创建时间、优先级、权威范围。
     - 相关用户故事表，只列 ID、标题、影响说明。
     - 范围界定：包含/不包含。
     - 当前业务规则和状态。
     - API/前端用户可见约束。
     - 验收目标。
     - 参考资料。
   - 正文以当前规则为主线；如需说明历史，仅保留一句旧术语的非权威状态。

4. **删除或迁移旧 PRD**
   - 默认移动到 `docs/prd/archive/...`，并在文件顶部标注“不再作为权威需求源”。
   - 只有用户明确允许删除时，才删除被合并旧文档。
   - 无论删除还是归档，都必须清理正式索引中旧文件入口。

5. **更新引用**
   - 更新 `docs/prd/00-index.md`，只列正式权威 PRD；如保留 archive，单独列归档且标明非权威。
   - 更新 `01-product-overview.md`、`02-domain-model.md`、相关 chat/integration/core PRD 的引用。
   - 更新 `api-token-auth.md` 等仍指向旧文件的参考资料。
   - 使用 grep 确认旧文件名、旧路径和旧术语没有作为当前权威规则残留。

6. **验证**
   - 运行项目已有 Markdown 链接检查脚本，例如 `python scripts/check-markdown-links.py`。
   - 检查所有 `docs/prd/**/*.md` 都出现在 `docs/prd/00-index.md`，除非明确是 archive 且索引策略排除。
   - 运行 grep 确认旧 PRD 路径、删除文件和过期当前规则没有死引用。
   - 汇报删除了哪些旧文档、新增了哪些权威文档、验证结果和任何保留风险。

### PRD 合并判定

建议合并：
- 多个 PRD 描述同一对象的不同迭代，例如 xlsx 导入、Markdown 上传和 page_id 统一都属于文档摄入。
- 文档大部分在讲“从旧实现迁移到新实现”，而当前代码已实现。
- 不同文档重复状态机、ID 语义、metadata 字段、provider 配置或存储边界。
- 旧文档标题是一次性方案名。

建议保留独立：
- 安全边界独立且影响多类 API，例如 API Token 鉴权。
- 对外集成契约独立，例如嵌入式 Widget。
- 用户可见体验明显独立，例如聊天 UI、多轮记忆。
- 尚未稳定的候选方案；它应放在 `.ai/future/**`，不作为正式 PRD。

### PRD 治理输出

最终答复必须包含：
- 新权威 PRD 列表。
- 删除或归档的旧 PRD 列表。
- 主要规则收敛点，例如状态、ID、格式、provider、存储。
- 验证命令和结果。
- 未处理的风险或用户需要决策的问题。

### 并行 subagent 维度
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

`--backend-only` 只启动“后端实现一致性”“后端深度一致性”和“候选问题验证”。`--deep` 在“后端实现一致性”之外，额外按模块调用 `backend-consistency` 做专项深度检查。`backend-consistency` 在 `t-dream` 调用下必须只返回结构化结果，不自行写入独立一致性报告。

### subagent 调用要求
- 使用 `Task` 或 `Agent` 启动 `subagent_type="context-curator"`、`subagent_type="structure-review"`、`subagent_type="general_agent"`。
- subagent 调用按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 执行；`general_agent` 为内置 agent，按协议跳过注入。
- 可并发/后台执行时，同时启动各维度 subagent。
- 各 subagent 必须只读检查，不修改代码或文档。
- 各 subagent 必须接收同一份共享上下文包，保持检查范围一致。
- 各 subagent 的候选问题字段必须一致，便于主线程合并；允许保留维度专属摘要，例如权威上下文地图、结构地图或模块评分。
- 并行执行时，不让某个维度的结论污染其他维度；主线程或验证 subagent 在汇总阶段处理冲突。
- subagent 只输出候选问题，不直接决定最终报告结论。

共享上下文包必须包含：
- 检查范围：`[feature]` / `--all` / `--backend-only` / `--deep` / `--govern-prd`。
- PRD 文件列表和目标模块列表。
- 相关用户故事、Demo 测试和实现检索路径。
- 设计、任务、README、AGENTS/CLAUDE、ADR 或架构说明路径（如存在）。
- 上下文健康判定规则、结构组织判定规则、描述准确性判定规则、P0/P1/P2/P3 分级规则和 `${CLAUDE_PLUGIN_ROOT}/protocols/dream-report-contract.md` 报告格式要求。
- 当前目标是整理和重组当前工程上下文。

每个 `general_agent` 必须返回符合 `${CLAUDE_PLUGIN_ROOT}/protocols/dream-report-contract.md` 的候选问题结构：
```text
维度:
范围:
分数:
已核验声明:
候选问题:
  - 标题:
    严重级别: P0|P1|P2
    置信度: 0-100
    描述位置:
    实现证据:
    判断依据:
    修复方向: 修正文档|修正实现|产品确认
    可能误报原因:
未能确认:
```

专项 agent 可按自身文档增加 `权威上下文地图`、`整理计划`、`结构地图`、`结构建议` 等字段，但 `候选问题` 中必须保留标题、严重级别、置信度、位置/证据、判断依据、整理或修复方向、可能误报原因。

候选问题置信度建议：
- 90-100：文档声明和实现事实存在直接、可定位冲突。
- 80-89：证据充分，但需要轻微推理。
- 60-79：有风险信号，但证据不完整；默认进入“未能确认”或 P2。
- 0-59：不得进入最终问题清单。

最终报告只纳入置信度不低于 80 的 P0/P1；低于 80 的发现只能进入“未能确认 / 观察项”，除非主线程二次验证后提高置信度。

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

### 4. 并行提取“描述声明”
从 PRD、用户故事和 Demo 测试中提取可核验声明：

- 能力边界：功能做什么、不做什么、角色能执行哪些操作。
- 数据与状态：关键实体、状态、字段约束、唯一性和生命周期。
- 验证规则：必填、长度、格式、边界条件和失败条件。
- 权限与租户边界：角色、权限、realm / tenant 隔离、跨租户访问限制。
- 业务流程：核心步骤、状态流转、错误处理和关键分支。
- 验收描述：用户故事 GWT、Demo 测试映射、关键断言和验收标准。

只记录可被文件证据验证的声明。

### 4. 并行提取”实现事实”
按目标项目真实结构定位实现，不假定固定目录；若采用常见 Java Spring Boot 布局，可优先检查：

- Domain：`backend/**/src/**/[module]*/`、实体、服务、策略和领域规则。
- HTTP/API：Controller 映射、DTO、validator、OpenAPI 注解。
- Infrastructure：repository、外部集成、持久化约束和事务边界。
- Frontend：页面、组件、路由、查询/变更、权限可见性。
- Demo：`demo/e2e/**/*.e2e.ts` 中的场景、注释、断言和日志。

后端模块检查的输入规则：
- 必须能在 `docs/prd/**/*.md` 中定位与 `[module]` 对应的 PRD。
- 目标仓库中与 `[module]` 对应的后端领域实现目录必须能被定位；若未采用固定布局，基于仓库真实结构搜索模块代码。
- HTTP/接口实现目录若不存在，记录为信息项，不直接判失败。

### 6. 并行对比描述与事实
逐项判断每个描述声明是否准确：

- PRD 声明的能力边界、权限规则或业务规则在代码中缺失 → P0。
- PRD 与代码在关键校验、权限、租户隔离或业务流程上冲突 → P0。
- PRD / 用户故事 / Demo 描述承诺了尚未实现或测试未覆盖的行为 → P0 或 P1，按影响定级。
- 代码已扩展新能力但 PRD 未更新语义说明 → P1。
- 用户故事或 Demo 描述与 PRD 不一致，但未发现实现冲突 → P1。
- 接口说明、路由名、字段名、示例数据或非关键说明失真 → P2；作为描述准确性问题单独记录。

每条差异必须判断优先修正文档还是实现：
- 文档错：实现事实合理，但 PRD / 故事 / Demo 描述失真。
- 实现错：PRD 描述合理且处于有效需求范围，但代码未实现或实现冲突。
- 需确认：缺少证据或存在产品决策空白。

### 7. Traceability 检查
检查 PRD、用户故事、设计、任务、实现、测试、Demo 之间是否存在可追踪关系：

- PRD 中的核心能力应能找到用户故事、设计或任务承接；缺失时记录为 P1 或 P2。
- 用户故事或 Demo 测试引用的能力应能找到当前权威 PRD；找不到或引用过期 PRD 时记录为 P1。
- 设计/任务描述的模块和代码目录应能相互定位；无法定位时记录为 P1。
- 测试或 Demo 覆盖应能回连到对应用户故事或验收目标；断链时记录为 P1 或 P2。
- 重点检查产品能力、模块边界、验收路径和关键业务规则的追踪关系。

### 8. 后端深度一致性
默认后端维度由 `general_agent` 完成证据提取和对比；在 `--deep` 或 `--backend-only` 时，对每个后端模块额外调用 `backend-consistency`。

按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 通过 `Agent(subagent_type="backend-consistency")` 启动，prompt 必须包含：
- 模块名。
- PRD 路径；路径来自 `docs/prd/**/*.md` 的实际匹配结果。
- 当前检查范围。
- `t-dream` 调用标记：只读返回，不写入 `.ai/quality/consistency-*` 独立报告。
- 要求输出 API 能力边界、数据模型、验证规则、权限、业务逻辑五个维度评分。
- 要求标明每条差异应修正文档、实现还是需要产品确认。

agent 失败时记录失败模块为 P1，并继续其他模块（`--all` 模式）。

### 9. 候选问题验证
并行发现结束后，必须进行验证步骤。验证可由主线程完成，也可额外启动一个 `general_agent` 作为“候选问题验证”维度。

验证输入：
- 所有 subagent 的候选问题。
- 共享上下文包。
- 候选问题引用的文档位置和实现证据。

验证动作：
- 重新读取关键文件片段，确认描述声明和实现事实是否真实存在。
- 过滤没有文件定位、证据不足、只属于风格偏好的候选问题。
- 校准严重级别和置信度。
- 合并重复问题，保留最具体的文件位置和证据。
- 判断修复方向是修正文档、修正实现还是产品确认。
- 低置信度但值得关注的问题放入“未能确认”。

### 10. 主线程合并与裁决
所有 subagent 返回后，主线程执行汇总：

- 合并验证后的问题，保留最具体的文件位置和证据。
- 对冲突结论进行二次读取验证；无法裁决时标记为“产品确认”。
- 校验每个 P0/P1/P2 是否有文档位置、实现证据和修复方向。
- 重新计算总分；不得直接平均 subagent 分数。
- 检查是否存在 subagent 漏跑、范围不一致或输出结构不合格；存在时记录为 P1。

### 11. 评分计算
评分权重以 `${CLAUDE_PLUGIN_ROOT}/protocols/dream-report-contract.md` 为准。当前约定如下：
默认模式总分 100：
- 上下文治理健康度：25
- 结构组织合理性：20
- Traceability 完整性：20
- 关键描述与实现事实一致性：25
- 证据链完整性：10

默认 audit 的实现一致性分只对已抽样核验的关键声明负责；报告中必须列出抽样范围和未覆盖范围，不得暗示已完成全量实现审计。

深度模式总分 100：
- 上下文治理健康度：20
- 结构组织合理性：15
- Traceability 完整性：15
- 基础描述与实现事实一致性：25
- 后端深度一致性：25

后端深度一致性内部权重：
- API 能力边界：30%
- 数据模型一致性：25%
- 验证规则一致性：20%
- 权限一致性：15%
- 业务逻辑一致性：10%

`--backend-only` 模式只计算 PRD 与后端实现一致性，按 100 分折算，并在报告中标注未覆盖上下文治理、结构组织、用户故事、Demo 和前端描述准确性。

### 12. 写入报告
写入 `.ai/quality/dream-check-[YYYYMMDD-HHMMSS].md`。

报告结构以 `${CLAUDE_PLUGIN_ROOT}/protocols/dream-report-contract.md` 为准，必须包含：
- 执行摘要、范围、模式和总分。
- 审计模式说明：只读 audit / govern-prd / backend-only / deep，以及 `--all` 是否只做索引级扫描。
- 当前权威上下文地图：PRD、用户故事、设计/任务、代码、测试/Demo 的主要入口。
- 上下文治理问题：重复、过期、冲突、过程化、非权威或误导性信息。
- 结构组织问题：目录边界、模块归属、测试布局、Demo 布局和 `.ai/` 产物组织问题。
- Traceability 断链、错链、重复链和缺失证据。
- 被核验的描述声明清单。
- 分项得分、扣分原因和可复算公式。
- 实现一致性抽样范围、未覆盖范围和高风险模块选择依据。
- P0 / P1 / P2 差异列表。
- 未能确认 / 低置信度观察项；与正式问题分栏展示。
- 每条差异的文档位置、实现证据、判断依据。
- 每条差异的置信度。
- 每条差异的修复方向：修正文档 / 修正实现 / 产品确认。
- 深度模式下的模块评分表。
- subagent 执行矩阵：维度、状态、范围、问题数量、是否参与总分。
- 下一步修复建议。

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
- 所有差异项必须可定位到文件或 PRD 条目。
- 所有统计项必须有数据来源。
- 每个参与评分的维度必须有对应 subagent 输出；未执行时必须说明原因。
- 最终 P0/P1 问题必须经过验证步骤，且置信度不低于 80。
- 评分公式必须可复算，分项分值之和必须等于总分。
- 报告必须落盘。
- PRD 只承载产品规则、能力边界和验收目标；接口或路由说明问题作为描述准确性问题单独记录。
- 阶段质量收口仍由专门命令承担：`/t-prd-check`、`/t-design-check`、`/t-task-check` 是可选质量检查，`/t-demo-accept` 是 Demo 验收。
