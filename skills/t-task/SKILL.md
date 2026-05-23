---
name: t-task
description: Convert technical design documents into executable phased task plans with work breakdown and dependencies.
argument-hint: [任务名称] [--phase <backend|frontend|miniapp|demo>]
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Task
  - Write
  - Bash
  - Agent
---

# 任务规划生成

运行时边界统一参考：`protocols/runtime-boundaries.md`

任务拆分必须服务于简单、外科式、可验证的执行；如果设计文档、guide 或 protocol 冲突，停止并说明冲突。

## Input Contract

上游输入（来自 `/t-design` 产出）：
- `.ai/design/[feature].md` — 技术设计文档（必须存在）
  - 必须包含：目标、范围、API 接口设计、数据库设计、测试策略
  - 应包含：现有实现分析、用户故事/PRD 引用、文件影响范围

可选输入：
- `.ai/task/[feature]/.state.json` — 已有任务状态（增量生成时）
- `docs/prd/**/*.md` — PRD 文档
- `docs/user-stories/**/*.md` — 用户故事
- `${CLAUDE_PLUGIN_ROOT}/guides/` — 开发规范

## Output Contract

下游产出（供 `/t-task-check` 和 `/t-run` 使用）：
- `.ai/task/[feature]/.state.json` — 任务状态文件，包含 phase/slot/item 层级状态
- `.ai/task/[feature]/<phase>/index.md` — 阶段总览
- `.ai/task/[feature]/<phase>/<slot>.md` — Slot manifest（导航与依赖）
- `.ai/task/[feature]/<phase>/<slot>/<ITEM-ID>-*.md` — 可执行的 item 文件
  - 每个 item 包含：id, title, agent, scope, inputs, steps, expected_files, validation, depends_on, handoff_summary, completion_criteria
- `.ai/task/[feature]/backend/finalize.md` — backend 阶段收口流程（仅 backend）

## Purpose
- 从 `.ai/design/[feature].md` 生成 `.ai/task/[feature]/` 任务目录和 `.state.json`。
- 固定使用 `phase -> slot -> item` 模型。
- 生成可供 `/t-run` 串行执行的 item 文件，而不是把 manifest 当执行输入。
- backend 阶段额外生成 `finalize.md`，由 `/t-backend-finalize` 独立执行。

## Args
| 参数 | 说明 |
|---|---|
| `[feature]` | 功能名（必填） |
| `--phase <backend\|frontend\|miniapp\|demo>` | 指定阶段生成；未指定时自动选择第一未完成阶段 |

## Preconditions
- `.ai/design/[feature].md` 必须存在。
- 阶段依赖、slot 顺序、执行单元统一参考：`protocols/task-phase-execution.md`
- `frontend` 阶段生成前必须先执行 `cd frontend && npm run generate-api && cd ../`
- `miniapp` 是可选阶段：仅当项目根目录存在 `miniapp/`，或设计文档明确包含小程序交付内容时启用。
- 未启用 miniapp 的项目不得自动生成 `.ai/task/[feature]/miniapp/`；显式请求 `--phase miniapp` 时应返回“当前项目未启用 miniapp 阶段”。
- 启用 miniapp 时，默认阶段顺序为 `backend -> frontend -> miniapp -> demo`。
- `generate-api` 失败时立即终止，不生成当前阶段任务文件。

## Output Layout
backend 阶段：
```text
.ai/task/[feature]/backend/
├── index.md
├── dev.md
├── dev/
│   ├── BE-D01-*.md
│   └── ...
├── test.md
├── test/
│   ├── BE-T01-*.md
│   └── ...
├── accept.md
├── accept/
│   ├── BE-A01-*.md
│   └── ...
└── finalize.md
```

frontend 阶段：
```text
.ai/task/[feature]/frontend/
├── index.md
├── dev.md
├── dev/FE-D01-*.md
├── test.md
├── test/FE-T01-*.md
├── accept.md
└── accept/FE-A01-*.md
```

miniapp 阶段：
```text
.ai/task/[feature]/miniapp/
├── index.md
├── dev.md
├── dev/MA-D01-*.md
├── test.md
├── test/MA-T01-*.md
├── accept.md
└── accept/MA-A01-*.md
```

demo 阶段：
```text
.ai/task/[feature]/demo/
├── index.md
├── dev.md
├── dev/DE-D01-*.md
├── accept.md
└── accept/DE-A01-*.md
```

## State Shape
`.state.json` 的完整结构、兼容性规则和状态聚合规则统一参考：

- `protocols/task-state-contract.md`

## Generation Flow
1. 校验 `.ai/design/[feature].md` 存在。
2. 解析 `[feature]` 和 `--phase`；根据 `protocols/task-phase-execution.md` 检测 active phases；未传 `--phase` 时自动选择第一未完成 active phase。
3. 按 `protocols/task-phase-execution.md` 校验阶段前置和 slot 顺序；未启用的 phase 不参与校验或生成。
4. 如目标阶段为 `frontend`，先运行 `generate-api`。
5. 按当前阶段 slot 串行调度相应 agent。每个 slot agent 必须通过 `Agent` tool 启动，`subagent_type` 按 Agent Dispatch Mapping 映射。传入 prompt 必须包含：设计文档相关节、上游 slot handoff（如有）、guide 路径、Agent Output Contract 要求的字段列表。
   - prompt 必须引用 `protocols/task-check-rubric.md`，要求 agent 在返回前自检 P0/P1 规则。
   - prompt 必须引用 `protocols/task-phase-execution.md`，避免生成无法被 `/t-run` 执行的 item。
6. 每个 slot agent 必须返回：
   - slot manifest 正文
   - item 文件集合
   - item DAG
   - slot completion criteria
   - handoff summary
   - self_check：对必填字段、DAG、拆分阈值、backend test item 类型和 finalize 规则的自检结果
7. 主流程在每个 slot 返回后先执行写入前硬校验：
   - item 必填字段齐备
   - item ID 唯一，依赖存在且无环
   - manifest 覆盖全部 items，路径与 item 文件一致
   - item 未触发必须拆分规则；触发时必须返回拆分后的 items
   - backend/test item 含合法 `test_item_type`，runner 含 `uses_skill: skills/t-backend-test-run/SKILL.md`
   - accept item 不得只依赖 backend/test authoring item
8. 硬校验失败时终止当前 slot，不写入成功状态，要求重新生成该 slot。
9. 硬校验通过后写入当前 slot manifest 和 item 文件，再继续调用下游 slot。
10. 当前阶段 slot 齐备后生成 `<phase>/index.md`。
11. 写入或更新 `.state.json`。
12. 返回下一步建议：`/t-task-check [feature] --phase [phase]`。

## Agent Dispatch Mapping

| phase | slot | subagent_type |
|-------|------|---------------|
| backend | dev | backend-dev |
| backend | test | backend-test |
| backend | accept | backend-accept |
| frontend | dev | frontend-dev |
| frontend | test | frontend-test |
| frontend | accept | frontend-accept |
| miniapp | dev | miniapp-dev |
| miniapp | test | miniapp-test |
| miniapp | accept | miniapp-accept |
| demo | dev | demo-dev |
| demo | accept | demo-accept |

## Slot Manifest Contract
每个 slot manifest 必须包含：
- slot 目标和边界
- item 表格：`id | title | agent | file | depends_on | status`
- item DAG 或执行顺序
- 上游输入和下游 handoff
- slot 级完成标准
- 测试或验收策略摘要

manifest 不得包含完整实现步骤；完整步骤必须写入 item 文件。

## Agent Output Contract
slot agent 输出必须至少包含：
- `slot`: `dev|test|accept`
- `manifest_target_file`
- `manifest_content`
- `items`: item 对象列表，每个 item 包含 `id/file/agent/depends_on/content`
- `item_dag`
- `completion_criteria`
- `handoff_summary`
- `self_check`: 必填字段、DAG、拆分、阶段执行规则和 P0/P1 风险自检结果

主流程必须：
- 校验 `slot` 与被调度 agent 是否匹配。
- 校验 item 依赖合法且无环。
- 校验 manifest、item 文件路径和 `.state.json` 计划一致。
- 校验 `self_check` 存在且未声明未解决 P0/P1。
- 先写入当前 slot manifest 和 item 文件，再继续调用下游 slot。
- 在当前阶段要求的 slot 结果齐备后再生成 `index.md`。
- 文档写入与 `.state.json` 更新保持同轮完成。

## Item Contract
每个 item 文件必须包含：
- `id`: 稳定 ID，例如 `BE-D01`、`FE-T02`、`MA-A01`、`DE-A01`
- `title`: 子任务标题
- `agent`: 执行 agent
- backend/test item 必须额外包含 `test_item_type: authoring|runner`
- backend/test runner item 必须包含 `uses_skill: skills/t-backend-test-run/SKILL.md`；authoring item 必须为 `uses_skill: none` 或省略
- `scope`: 本 item 的明确边界
- `inputs`: 必读设计、规范、上游 handoff 和相关文件
- `steps`: 可执行步骤
- `expected_files`: 预计新增或修改的文件/目录
- `validation`: 该 item 的最小验证命令或检查方式
- `depends_on`: 依赖的 item ID 列表
- `handoff_summary`: 完成后传给下游 item/slot 的摘要要求
- `completion_criteria`: 完成标准

状态字段、执行顺序、依赖选择统一以 `protocols/task-state-contract.md` 和
`protocols/task-phase-execution.md` 为准，不在本文件重复定义第二套状态机。

## Splitting Rules
必须拆分 item，如果任一条件成立：
- 预计超过 1 天才能完成。
- 预计修改超过 5 个核心文件。
- 跨越超过 2 个领域模块或页面域。
- 超过 8 个主要步骤。
- 单个 item 文件预计超过 12KB 且不是验收清单。
- scope 中包含两个可独立交付、独立验证的主交付物（例如 `A + B`、两个页面、页面 + 弹窗、helper + 场景测试）。
- 单个 HTTP/API item 同时包含 5 个以上 endpoint、DTO、路由注册和 OpenAPI/schema 更新。
- 单个 demo item 同时创建复用 helper 并覆盖多个完整用户故事或多个业务状态流。

推荐拆分方式：
- backend dev：数据库/实体、domain、repository、service/use case、HTTP/OpenAPI、外部集成、SDK/API 影响点。
- backend HTTP/API：DTO 与路由骨架、读模型/list/detail、写操作/create/update、状态操作、配置类接口分别拆分；每个 item 必须能用定向 `cargo check` 或场景测试验证。
- backend test：按场景测试 authoring 与测试执行 runner 拆分；不要把创建场景测试和修复实现直到测试通过放在同一个 item。
- backend unit test：不得规划“为新增 struct/DTO/builder/getter/常量补单测”这类低价值 item。
- frontend dev：API/type 适配、schema/query/store、页面主流程、状态与错误处理、权限与空态。
- frontend dev：一个 item 默认只交付一个页面域或一个可复用组件族；配置页、用户页、管理页、dialog 等可独立验证的 UI 不应合并。
- miniapp dev：页面注册、组件主流程、主题接线、token/icon 集成、平台差异处理。
- miniapp test：typecheck、weapp/h5 构建、模板门禁、页面注册与资源产物回归。
- demo dev：先拆 fixtures/helpers，再拆主流程、异常/校验场景、权限场景；不要把 helper 和完整业务流放在同一个 item。
- accept：design consistency、public API contract、business rules、permission/security、test evidence、demo readiness。

## Backend Finalize
- backend 阶段必须额外生成 `<phase>/finalize.md`。
- `finalize.md` 必须明确：
  - `/simplify` 目标范围
  - `cargo clippy --fix --allow-dirty --allow-staged --all-targets --all-features`
  - `cargo fmt --all`
  - OpenAPI 导出与前端 API 生成
  - 失败后从失败步骤恢复
- `finalize.md` 不拆 item，不由 `/t-run` 执行。

## Backend Test Planning Rules

backend/test slot 必须按当前契约生成，不做旧格式兼容：

| 类型 | agent | test_item_type | uses_skill | depends_on |
|---|---|---|---|---|
| authoring | backend-test | authoring | none | 对应 backend-dev item |
| runner | backend-test | runner | `skills/t-backend-test-run/SKILL.md` | 对应 authoring item |

authoring item 只创建或修改场景测试、测试 helper 和模块注册；完成标准只要求编译验证或建议 runner 命令，不要求目标测试全部通过。

runner item 只执行定向测试、分析失败、委派生产代码修复和重测；测试语义可能错误时停止并输出诊断报告。

backend/test slot 不规划源文件内单元测试；确有必要的高价值单元测试归入对应 backend/dev item。

accept item 必须依赖 runner item，不能只依赖 authoring item。`t-backend-test-run` 是 skill，不是 agent；不得生成 `agent: backend-test-run`。

## Forbidden
- 生成或依赖旧状态字段。
- 生成或依赖 `agents` 根字段。
- 支持旧参数。
- 生成根级 `backend-dev.md`、`backend-test.md`、`frontend-dev.md`、`miniapp-dev.md`、`agents.json` 等旧结构文件。
- 把 `dev.md`、`test.md`、`accept.md` 当作 `/t-run` 的直接执行输入。
- 在单个 item 中塞入跨多模块、多天或不可恢复的大任务。
- 当前阶段 slot 并行生成；slot 必须按依赖串行。
- 未写入上游 manifest 和 item 文件就调用下游 slot agent。
- backend 阶段遗漏 `finalize.md`。
- 生成缺少 `test_item_type: authoring|runner` 的 backend/test item。
- 生成 `agent: backend-test-run` 的 item。

## Failure
- 设计文档不存在：提示先运行 `/t-design [feature]`。
- 前置阶段未完成：返回阻塞阶段与阻塞 items。
- `frontend` 阶段 `npm run generate-api` 失败：立即终止，并返回失败命令与错误摘要。
- 任一 slot agent 生成失败：终止本次任务生成，不写入该 slot 的成功状态，并返回失败 agent 与失败原因。
- slot agent 返回 item 缺少必填字段、依赖不存在或形成环：拒绝写入成功状态，要求重新生成该 slot。
- slot agent 返回缺失 `self_check`、manifest 覆盖不完整、backend/test 类型非法或触发必须拆分规则：拒绝写入成功状态，要求重新生成该 slot。

## Examples
```bash
# 生成 backend 阶段任务
/t-task <feature> --phase backend

# 未指定 phase 时自动选择第一未完成阶段
/t-task <feature>
```

期望响应：
```text
已生成 backend 阶段任务：
- index.md
- dev.md + dev/*.md
- test.md + test/*.md
- accept.md + accept/*.md
- finalize.md

状态已更新：phase=backend, phases.backend.generated_at=<timestamp>
下一步: /t-task-check <feature> --phase backend
```

## 相关引用
- `protocols/runtime-boundaries.md`
- `protocols/task-state-contract.md`
- `protocols/task-phase-execution.md`
- [context-isolator.md](/skills/t-task/references/context-isolator.md)
- [phase-validator.md](/skills/t-task/references/phase-validator.md)
- [phase-index-generator.md](/skills/t-task/references/phase-index-generator.md)
- [compat-all-mode.md](/skills/t-task/examples/compat-all-mode.md)
- [frontend-blocked-by-backend.md](/skills/t-task/examples/frontend-blocked-by-backend.md)
- [phased-backend-success.md](/skills/t-task/examples/phased-backend-success.md)
- [error-response-template.md](/skills/t-task/templates/error-response-template.md)
- [phase-index-template.md](/skills/t-task/templates/phase-index-template.md)
