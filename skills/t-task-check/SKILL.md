---
name: t-task-check
description: >
  任务规划质量检查。对 .ai/task/[feature]/ 下的新 item 任务结构进行量化评分并输出修复清单。
argument-hint: [任务名称] [--phase <backend|frontend|demo>]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Task
  - Write
---

# 任务规划质量检查

运行时边界统一参考：`protocols/runtime-boundaries.md`

## 目标
- 评估任务文档可执行性与一致性。
- 验证 `phase -> slot -> item` 结构。
- 给出可复查的 100 分量化结果。
- 输出 P0/P1/P2 修复清单。
- 必须按当前阶段调度对应 sub agent 做专业校验，再由主流程聚合结论。

评分、阻塞条件和报告要求统一参考：`protocols/task-check-rubric.md`

## 事实优先级（强制）
证据优先级和争议处理统一参考：`protocols/task-check-rubric.md`

## 使用方式
```bash
/t-task-check [feature] [--phase <backend|frontend|demo>]
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
  - backend/frontend: `dev.md`、`test.md`、`accept.md`
  - demo: `dev.md`、`accept.md`
- item 文件：
  - backend/frontend: `dev/*.md`、`test/*.md`、`accept/*.md`
  - demo: `dev/*.md`、`accept/*.md`
- backend 额外文件：`finalize.md`

## Schema 校验
`.state.json` 的 schema 要求统一参考：

- `protocols/task-state-contract.md`
- `protocols/task-check-rubric.md`

任一项缺失或非法即返回 `TASK_SCHEMA_INVALID`

## 执行流程
1. 校验设计文档是否存在。
2. 读取 `.state.json` 并验证 schema。
3. 若指定 `--phase`，仅检查该阶段；否则检查当前阶段。
4. 校验阶段依赖正确性。
5. 读取阶段目录下的 `index.md`、slot manifest 和 item 文件。
6. 按 `protocols/task-check-rubric.md` 校验 item DAG 与 manifest 覆盖关系。
7. 检查旧结构残留：
   - 根级 `backend-dev.md`
   - 根级 `backend-test.md`
   - 根级 `frontend-dev.md`
   - 根级 `demo-dev.md`
   - 根级 `README.md`
   - 根级 `agents.json`
   - 其他混用旧结构的任务文件
8. 验证 item 文件结构与内容：
   - 必须包含 `id/title/agent/scope/inputs/steps/expected_files/validation/depends_on/handoff_summary/completion_criteria`
   - 不得把完整 slot 内容塞进一个 item
   - 超过拆分阈值必须有合理说明，否则记 P1
9. 核对设计文档与任务文档的一致性。
10. 调用当前阶段对应 agent 进行专业校验：
   - backend: `backend-dev`, `backend-test`, `backend-accept`
   - frontend: `frontend-dev`, `frontend-test`, `frontend-accept`
   - demo: `demo-dev`, `demo-accept`
11. 聚合 agent 结果并进行主流程复核。
12. 按评分体系生成评分与问题清单。
13. 执行报告一致性自检。
14. 写入报告：`.ai/quality/task-check-[feature]-[YYYYMMDD-HHMMSS].md`。

## Agent Review Contract
当前阶段 agent 输出字段和主流程补证要求统一参考：

- `protocols/task-check-rubric.md`

## 评分与问题分级
评分体系、P0/P1/P2 定义和报告结构统一参考：`protocols/task-check-rubric.md`

## 错误处理
| 错误码 | 触发条件 | 用户可见提示 | 恢复动作 |
|---|---|---|---|
| `DESIGN_DOC_MISSING` | 设计文档不存在 | 未找到设计文档 | 先运行 `/t-design [feature]` |
| `STATE_FILE_MISSING` | 任务目录或 `.state.json` 缺失 | 状态文件不存在 | 运行 `/t-task [feature] --phase backend` 重建 |
| `STATE_JSON_INVALID` | `.state.json` 格式错误 | 状态文件解析失败 | 修复 JSON 后重试；或重建任务目录 |
| `TASK_SCHEMA_INVALID` | 缺少 `phase/phases/tasks/status/manifest/items` 字段 | 任务状态结构不完整 | 运行 `/t-task [feature] --phase [phase]` 重建 |
| `LEGACY_STRUCTURE_FOUND` | 发现旧结构字段或旧任务文件 | 旧结构残留 | 删除旧任务目录后重新运行 `/t-task` |
| `PHASE_INVALID` | `--phase` 不是 `backend|frontend|demo` | 非法阶段，仅支持 backend/frontend/demo | 使用合法参数后重试 |
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
旧结构残留检查: 通过

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
1. BE-D03 超过拆分阈值，建议拆为 repository trait 与 repository implementation 两个 item

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
- `agents/demo-accept.md`
