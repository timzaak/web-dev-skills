---
name: t-task-check
description: Validate task plan executability and consistency with a 100-point score and P0/P1/P2 fix list.
argument-hint: "[任务名称] [--phase <backend|frontend|miniapp|flutter|web-demo|flutter-demo>]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Glob
  - Grep
  - Bash
  - Task
  - Write
  - Agent
---

# 任务规划质量检查

运行时边界：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`（判断产物写入位置或脚本入口与插件默认冲突时读）
需求来源边界：`${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`（区分草稿与已发布需求来源或处理两者冲突时读）
决策连续性和用户决策暴露：`${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`（提问、更新决策账本或处理决策暴露门禁时读）
评分、严重度、agent 评审边界、报告结构与硬门禁：`${CLAUDE_PLUGIN_ROOT}/protocols/task-check-rubric.md`（评分或生成分级结论前读）

评估任务文档可执行性与一致性，验证 `phase -> slot -> item` 结构，输出 100 分量化结果和 P0/P1/P2 修复清单。必须按当前阶段调度对应 sub agent 做专业校验，再由主流程按 rubric 聚合结论。本检查为可选，不作为 `/t-run` 的硬性前置；但一旦运行，报告必须严格按 rubric 给出准入风险。

## 使用方式

```bash
/t-task-check [feature] [--phase <backend|frontend|miniapp|flutter|web-demo|flutter-demo>]
```

| 参数 | 说明 |
|---|---|
| `[feature]` | 功能名（必填） |
| `--phase <phase>` | 指定阶段检查；未指定时检查 `.state.json` 当前阶段 |

## 输入范围

- 设计文档：`.ai/design/[feature].md`
- 决策账本：`.ai/decision-log/[feature].md`（存在时必须读取）
- 需求来源：`.ai/user-stories/**/*.md`、`docs/user-stories/**/*.md`、`.ai/prd/**/*.md`、`docs/prd/**/*.md`、`.ai/tech-research/**/*.md`（按设计文档引用读取）
- 状态文件：`.ai/task/[feature]/.state.json`
- 阶段目录：`.ai/task/[feature]/[phase]/` 下的 `index.md`、slot manifest（backend/frontend/miniapp/flutter 为 `dev.md`、`test.md`、`accept.md`；web-demo / flutter-demo 为 `dev.md`、`accept.md`）和 item 文件

## Schema 校验

`.state.json` 的 schema 要求统一参考 `${CLAUDE_PLUGIN_ROOT}/protocols/task-check-rubric.md` 的 Schema Checks 和 `${CLAUDE_PLUGIN_ROOT}/protocols/task-state-contract.md`。任一项缺失或非法即返回 `TASK_SCHEMA_INVALID`。旧格式 item（缺少 `Goal/Work/Files/Validation/Handoff` 五章节）不做兼容迁移；返回结构问题并提示重新运行 `/t-task [feature] --phase [phase]`。

## 执行流程

1. 校验设计文档存在；读取 `.state.json` 并验证 schema。若指定 `--phase`，仅检查该阶段（必须存在于 active phases）；否则检查当前阶段。

1. 校验设计文档存在；读取 `.state.json` 并验证 schema。若指定 `--phase`，仅检查该阶段（必须存在于 active phases）；否则检查当前阶段。
2. 读取阶段目录下的 `index.md`、slot manifest，并按 rubric 的 Context Budget Rules 建立轻量 item 表（先状态/索引/manifest 和关键字段抽取，仅在有疑点或需补证时读 item 全文，大型 phase 先用 `Grep` 定位）。
3. 对当前 phase 全部 Markdown 运行 `python ${CLAUDE_PLUGIN_ROOT}/scripts/check-decision-closure.py <all-phase-markdown-paths>`，并核对 `index.md` 的 Decision Trace 覆盖相关 Active Decision。
4. 按 rubric 的 Execution Checks 和 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 校验 item 结构、拆分阈值、Slot Item Count Limits、测试集中执行与 backend/test 闭环。补充严重度规则：
   - 集中测试执行 item 优先运行 `uv run scripts/check-test-runner-coverage.py [feature] --layer [layer]` 做覆盖校验；backend 动态校验失败记 P1 或 P0（取决于是否导致新增测试无法执行），其他层静态校验失败至少记 P1。
   - 后端测试命令必须使用目标项目内脚本入口 `uv run scripts/backend-test.py -- [filter]`（没有 filter 也保留 `--`）；使用 `mvn spring-boot:run`、裸 `mvn test`、插件根路径或省略 `--` 的记 P1，并改为统一入口。
5. 核对设计文档与任务文档的一致性；纯技术方案任务可只追溯设计文档中的技术预研来源，不得因缺少 PRD/用户故事扣 P0。任务引用 `.ai/user-stories` 时确认其为 draft 候选来源且路径存在；不得要求先发布到 `docs/user-stories` 才能进入 `/t-run`。
6. 通过 `Agent` tool 按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 调度当前阶段对应 subagent 做专业校验（backend: `backend-dev/backend-test/backend-accept`；frontend: `frontend-dev/frontend-test/frontend-accept`；miniapp: `miniapp-dev/miniapp-test/miniapp-accept`；flutter: `flutter-dev/flutter-test/flutter-accept`；web-demo: `web-demo-dev/web-demo-accept`；flutter-demo: `flutter-demo-dev/flutter-demo-accept`），可并行调度。subagent 上下文按 rubric 的 Context Budget Rules 裁剪：
   - dev agent 默认只接收 dev item 与直接影响实现的跨 slot 摘要
   - test agent 默认只接收 test item、相关 dev `Handoff/Files` 摘要和集中定向测试执行闭环约束
   - accept agent 默认只接收 accept item、顺序中相关 runner/dev `Handoff` 摘要和验收闭环约束
7. 聚合 agent 结果并按 rubric 复核：同类问题合并，P0/P1 补齐任务文档证据和真源证据；`needs_user_answer` 按 rubric 的 Clarification Gate 处理（先查 Decision Log，未解决时 `AskUserQuestion` 阻塞提问，回答前不得给出可进入 `/t-run` 的结论）。
8. 按 rubric 生成评分与问题清单，执行报告一致性自检，写入报告 `.ai/quality/task-check-[feature]-[YYYYMMDD-HHMMSS].md`。
9. 输出下一步建议：通过或风险可接受时进入 `/t-run [feature] --phase [phase]`；修复后可重新运行 `/t-task-check [feature] --phase [phase]`。

## 错误处理

| 错误码 | 触发条件 | 用户可见提示 | 恢复动作 |
|---|---|---|---|
| `DESIGN_DOC_MISSING` | 设计文档不存在 | 未找到设计文档 | 先运行 `/t-design [feature]` |
| `STATE_FILE_MISSING` | 任务目录或 `.state.json` 缺失 | 状态文件不存在 | 运行 `/t-task [feature] --phase backend` 重建 |
| `STATE_JSON_INVALID` | `.state.json` 格式错误 | 状态文件解析失败 | 修复 JSON 后重试；或重建任务目录 |
| `TASK_SCHEMA_INVALID` | 缺少 `phase/phases/tasks/status/manifest/items` 字段 | 任务状态结构不完整 | 运行 `/t-task [feature] --phase [phase]` 重建 |
| `PHASE_INVALID` | `--phase` 不是 supported phase | 非法阶段 | 使用合法参数后重试 |
| `PHASE_NOT_ACTIVE` | `--phase` 不在当前任务 active phases 中 | 当前项目未启用该阶段 | 使用 `.state.json.phases` 中存在的阶段，或重新运行 `/t-task` 生成该阶段 |
| `PHASE_DIR_MISSING` | 阶段目录不存在 | 找不到阶段目录 | 运行 `/t-task [feature] --phase [phase]` 生成 |
| `ITEM_SEQUENCE_INVALID` | manifest 未覆盖全部 item、包含重复 item，或 item 表格无法确定从上到下的执行顺序 | 子任务执行顺序非法 | 修复或重新生成该阶段 |
| `REPORT_INCONSISTENT` | 报告中的严重度、总分、准入结论或问题数量互相冲突 | 报告自检失败 | 重新聚合证据并重生成报告 |

信息提示（不阻断）：`PHASE_NOT_CURRENT`（指定阶段非当前阶段时提示后继续）；`PHASE_CHECK_AGENT_SET`（展示本次实际调用的 agent 集合）。
