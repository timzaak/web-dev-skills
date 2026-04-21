---
name: t-task
context: fork
argument-hint: [任务名称] [--phase <backend|frontend|demo>]
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Task
  - Write
  - Bash
---

# 任务规划生成

运行时边界统一参考：`protocols/runtime-boundaries.md`

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
| `--phase <backend\|frontend\|demo>` | 指定阶段生成；未指定时自动选择第一未完成阶段 |

## Preconditions
- `.ai/design/[feature].md` 必须存在。
- 阶段依赖、slot 顺序、执行单元统一参考：`protocols/task-phase-execution.md`
- `frontend` 阶段生成前必须先执行 `cd frontend && npm run generate-api && cd ../`
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
2. 解析 `[feature]` 和 `--phase`；未传 `--phase` 时自动选择第一未完成阶段。
3. 按 `protocols/task-phase-execution.md` 校验阶段前置和 slot 顺序。
4. 如目标阶段为 `frontend`，先运行 `generate-api`。
5. 按当前阶段 slot 串行调度相应 agent。
6. 每个 slot agent 必须返回：
   - slot manifest 正文
   - item 文件集合
   - item DAG
   - slot completion criteria
   - handoff summary
7. 主流程在每个 slot 返回后立即写入 manifest 与 item 文件。
8. 当前阶段 slot 齐备后生成 `<phase>/index.md`。
9. 写入或更新 `.state.json`。
10. 返回下一步建议：`/t-run [feature] --phase [phase]`。

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

主流程必须：
- 校验 `slot` 与被调度 agent 是否匹配。
- 校验 item 依赖合法且无环。
- 先写入当前 slot manifest 和 item 文件，再继续调用下游 slot。
- 在当前阶段要求的 slot 结果齐备后再生成 `index.md`。
- 文档写入与 `.state.json` 更新保持同轮完成。

## Item Contract
每个 item 文件必须包含：
- `id`: 稳定 ID，例如 `BE-D01`、`FE-T02`、`DE-A01`
- `title`: 子任务标题
- `agent`: 执行 agent
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

推荐拆分方式：
- backend dev：数据库/实体、domain、repository、service/use case、HTTP/OpenAPI、外部集成、SDK/API 影响点。
- backend test：domain/unit、repository/integration、API scenario、regression、高风险业务规则。
- frontend dev：API/type 适配、schema/query/store、页面主流程、状态与错误处理、权限与空态。
- accept：design consistency、public API contract、business rules、permission/security、test evidence、demo readiness。

## Backend Finalize
- backend 阶段必须额外生成 `<phase>/finalize.md`。
- `finalize.md` 必须明确：
  - `/simplify` 目标范围
  - `cargo clippy --fix --allow-dirty --allow-staged --all-targets --all-features`
  - `cargo fmt --all`
  - 全量 `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py`
  - OpenAPI 导出与前端 API 生成
  - 失败后从失败步骤恢复
- `finalize.md` 不拆 item，不由 `/t-run` 执行。

## Forbidden
- 生成或依赖旧状态字段。
- 生成或依赖 `agents` 根字段。
- 支持旧参数。
- 生成根级 `backend-dev.md`、`backend-test.md`、`frontend-dev.md`、`agents.json` 等旧结构文件。
- 把 `dev.md`、`test.md`、`accept.md` 当作 `/t-run` 的直接执行输入。
- 在单个 item 中塞入跨多模块、多天或不可恢复的大任务。
- 当前阶段 slot 并行生成；slot 必须按依赖串行。
- 未写入上游 manifest 和 item 文件就调用下游 slot agent。
- backend 阶段遗漏 `finalize.md`。

## Failure
- 设计文档不存在：提示先运行 `/t-design [feature]`。
- 前置阶段未完成：返回阻塞阶段与阻塞 items。
- `frontend` 阶段 `npm run generate-api` 失败：立即终止，并返回失败命令与错误摘要。
- 任一 slot agent 生成失败：终止本次任务生成，不写入该 slot 的成功状态，并返回失败 agent 与失败原因。
- slot agent 返回 item 缺少必填字段、依赖不存在或形成环：拒绝写入成功状态，要求重新生成该 slot。

## Examples
```bash
# 生成 backend 阶段任务
/t-task realm-user-rbac --phase backend

# 未指定 phase 时自动选择第一未完成阶段
/t-task realm-user-rbac
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
下一步: /t-run realm-user-rbac --phase backend
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
