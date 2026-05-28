---
name: t-task-check
description: Validate task plan executability and consistency with a 100-point score and P0/P1/P2 fix list.
disable-model-invocation: true
argument-hint: "[任务名称] [--phase <backend|frontend|miniapp|demo>]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Task
  - Write
  - Agent
---

# 任务规划质量检查

运行时边界统一参考：`protocols/runtime-boundaries.md`

## 目标
- 评估任务文档可执行性与一致性。
- 验证 `phase -> slot -> item` 结构。
- 给出可复查的 100 分量化结果。
- 输出 P0/P1/P2 修复清单。
- 必须按当前阶段调度对应 sub agent 做专业校验，再由主流程聚合结论。

评分、阻塞条件、报告要求、跨轮收敛和 agent 评审边界统一参考：`protocols/task-check-rubric.md`

## 事实优先级（强制）
证据优先级和争议处理统一参考：`protocols/task-check-rubric.md`

## 使用方式
```bash
/t-task-check [feature] [--phase <backend|frontend|miniapp|demo>]
```

| 参数 | 说明 |
|---|---|
| `[feature]` | 功能名（必填） |
| `--phase <phase>` | 指定阶段检查；未指定时检查 `.state.json` 当前阶段 |

## 输入范围
- 设计文档：`.ai/design/[feature].md`
- 状态文件：`.ai/task/[feature]/.state.json`
- 阶段目录：`.ai/task/[feature]/[phase]/`
- 阶段索引：`index.md`
- slot manifest：
  - backend/frontend/miniapp: `dev.md`、`test.md`、`accept.md`
  - demo: `dev.md`、`accept.md`
- item 文件：
  - backend/frontend/miniapp: `dev/*.md`、`test/*.md`、`accept/*.md`
  - demo: `dev/*.md`、`accept/*.md`
- backend 额外文件：`finalize.md`

## Schema 校验
`.state.json` 的 schema 要求统一参考：

- `protocols/task-state-contract.md`
- `protocols/task-check-rubric.md`

任一项缺失或非法即返回 `TASK_SCHEMA_INVALID`

## 执行流程
- 校验设计文档是否存在。
- 读取 `.state.json` 并验证 schema。
- 若指定 `--phase`，仅检查该阶段；否则检查当前阶段。指定阶段必须存在于 `.state.json.phases` 的 active phases 中。
- 校验阶段依赖正确性。
- 读取阶段目录下的 `index.md`、slot manifest 和 item 文件。
- 按 `protocols/task-check-rubric.md` 校验 item DAG 与 manifest 覆盖关系。
- 验证 item 文件结构与内容：
   - 必须包含 `id/title/agent/scope/inputs/steps/expected_files/validation/depends_on/handoff_summary/completion_criteria`
   - backend/test item 必须声明 `test_item_type: authoring|runner`
   - backend/test runner item 必须声明 `uses_skill: skills/t-backend-test-run/SKILL.md`
   - 每个 backend/test authoring item 必须有对应 runner item，且 runner 依赖 authoring
   - backend/accept item 必须依赖 runner item，不得只依赖 authoring item
   - 不得把完整 slot 内容塞进一个 item
   - 超过拆分阈值必须有合理说明，否则记 P1
   - scope 中包含两个可独立交付、独立验证的主交付物时，必须拆分，否则记 P1
   - 单个 HTTP/API item 同时包含 5 个以上 endpoint、DTO、路由注册和 OpenAPI/schema 更新时，必须拆分，否则记 P1
   - 单个 demo item 同时创建复用 helper 并覆盖多个完整用户故事或多个业务状态流时，必须拆分，否则记 P1
- 核对设计文档与任务文档的一致性。
- 通过 `Agent` tool 调度当前阶段对应 subagent 做专业校验。每个 subagent 独立启动，传入 prompt 包含：item 文件内容、设计文档相关节、验证范围、`protocols/task-check-rubric.md` 中的 agent 评审边界、输出格式要求（score/findings/fixes/summary）。可并行调度同阶段多个 subagent。
   - backend: subagent_type="backend-dev", "backend-test", "backend-accept"
   - frontend: subagent_type="frontend-dev", "frontend-test", "frontend-accept"
   - miniapp: subagent_type="miniapp-dev", "miniapp-test", "miniapp-accept"
   - demo: subagent_type="demo-dev", "demo-accept"
- 聚合 agent 结果并进行主流程复核：同类问题合并，P0/P1 必须补齐任务文档证据和真源证据。
- 按评分体系生成评分与问题清单。
- 执行报告一致性自检。
- 写入报告：`.ai/quality/task-check-[feature]-[YYYYMMDD-HHMMSS].md`。

## Agent Review Contract
调度方式：通过 `Agent(subagent_type="<agent-name>")` 启动。主流程收集所有 subagent 返回后进行交叉验证（证据优先级：仓库证据 > subagent 发现 > 假设）。

当前阶段 agent 输出字段和主流程补证要求统一参考：

- `protocols/task-check-rubric.md`

agent finding 不直接作为最终裁决；主流程必须按 rubric 完成证据复核和同类合并。

## 评分与问题分级
评分体系、P0/P1/P2 定义和报告结构统一参考：`protocols/task-check-rubric.md`

## 错误处理
| 错误码 | 触发条件 | 用户可见提示 | 恢复动作 |
|---|---|---|---|
| `DESIGN_DOC_MISSING` | 设计文档不存在 | 未找到设计文档 | 先运行 `/t-design [feature]` |
| `STATE_FILE_MISSING` | 任务目录或 `.state.json` 缺失 | 状态文件不存在 | 运行 `/t-task [feature] --phase backend` 重建 |
| `STATE_JSON_INVALID` | `.state.json` 格式错误 | 状态文件解析失败 | 修复 JSON 后重试；或重建任务目录 |
| `TASK_SCHEMA_INVALID` | 缺少 `phase/phases/tasks/status/manifest/items` 字段 | 任务状态结构不完整 | 运行 `/t-task [feature] --phase [phase]` 重建 |
| `PHASE_INVALID` | `--phase` 不是 `backend|frontend|miniapp|demo` | 非法阶段，仅支持 backend/frontend/miniapp/demo | 使用合法参数后重试 |
| `PHASE_NOT_ACTIVE` | `--phase` 不在当前任务 active phases 中 | 当前项目未启用该阶段 | 使用 `.state.json.phases` 中存在的阶段，或重新运行 `/t-task` 生成该阶段 |
| `PHASE_DIR_MISSING` | 阶段目录不存在 | 找不到阶段目录 | 运行 `/t-task [feature] --phase [phase]` 生成 |
| `ITEM_DAG_INVALID` | item 依赖缺失或成环 | 子任务依赖非法 | 修复或重新生成该阶段 |
| `REPORT_INCONSISTENT` | 报告中的严重度、总分、准入结论或问题数量互相冲突 | 报告自检失败 | 重新聚合证据并重生成报告 |

信息提示（不阻断）：
- `PHASE_NOT_CURRENT`：指定 `--phase` 非当前阶段时提示"当前阶段为 [state.phase]，继续检查指定阶段"。
- `PHASE_CHECK_AGENT_SET`：展示本次实际调用的 phase agent 集合，便于复查。

## 示例
```bash
/t-task-check sample-feature --phase backend
```

输出：
```text
总分: 92/100 (优秀，可进入实施)

状态文件验证: 通过
Item DAG 验证: 通过

状态文件结构: 15/15
文档完整性: 14/15
Item 可执行性: 18/20
内容一致性: 19/20
依赖与恢复: 15/15
文档规范: 8/10
代码示例质量: 3/5

Agent 集合: backend-dev, backend-test, backend-accept
问题分类摘要: confirmed=2, disputed=0, assumption=0

P1 问题:
- BE-D03 超过拆分阈值，建议拆为 repository trait 与 repository implementation 两个 item

下一步: /t-run sample-feature --phase backend
```

## 质量门禁
硬性门禁统一参考：`protocols/task-check-rubric.md`

## 相关引用
- `protocols/runtime-boundaries.md`
- `protocols/task-state-contract.md`
- `protocols/task-check-rubric.md`
- `skills/t-task/SKILL.md`
- `skills/t-backend-finalize/SKILL.md`
- `skills/t-run/SKILL.md`
- `skills/t-task/references/phase-validator.md`
- `skills/t-task/references/phase-index-generator.md`
- `agents/backend-dev.md`
- `agents/frontend-dev.md`
- `agents/miniapp-dev.md`
- `agents/demo-accept.md`
