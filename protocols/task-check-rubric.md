# Task Check Rubric

定义 `t-task-check` 的统一评分、阻塞条件和报告要求。

## Evidence Priority

最终结论的证据优先级必须为：

`docs/` 与 `${CLAUDE_PLUGIN_ROOT}/guides/` 与仓库实际文件 > 当前 phase 任务文档 > sub agent 评审意见

规则：

- sub agent 只能提供候选问题，不能直接充当最终裁决
- 可从仓库发现的事实必须由主流程再次核验
- 规范冲突应标记为“规范冲突/待澄清”，不得直接记为 P0

## Schema Checks

`.state.json` 必须满足：

- 不包含旧状态字段或 `agents` 根字段
- `feature` 存在
- `phase` 为 supported phases：`backend|frontend|miniapp|demo`
- `phases` 包含当前任务的 active phases；未启用 miniapp 的项目不要求包含 `miniapp`
- `phases[*].status` 存在
- `tasks[phase]` 存在
- backend/frontend/miniapp 含 `dev/test/accept`
- demo 含 `dev/accept`
- 每个 slot 含 `status/manifest/items`
- 每个 item 含 `status/file/agent/depends_on`
- backend 含 `tasks.backend.finalize.file` 和 `tasks.backend.finalize.status`

缺失或非法 => `TASK_SCHEMA_INVALID`

结构真相以 `protocols/task-state-contract.md` 为准。

## Execution Checks

主流程检查：

1. 设计文档存在
2. `.state.json` schema 有效
3. 阶段依赖正确
4. `index.md`、slot manifest、item 文件齐备
5. item DAG 合法：
   - item ID 唯一
   - `depends_on` 指向存在 item
   - 无依赖环
   - item 文件路径与 state 一致
   - manifest 覆盖全部 items
6. 无旧结构残留
7. item 文件包含必填字段
8. 设计文档与任务文档一致
9. 调用当前阶段对应 agents 做专业校验
10. 主流程复核后生成最终结论

## Agent Review Contract

每个被调度 agent 输出至少包含：

- `score`
- `findings`
- `fixes`
- `summary`

主流程补全每条 finding：

- `status`: `confirmed | disputed | assumption`
- `task_file`
- `source_of_truth`
- `repo_evidence`
- `why_blocking`
- `fix`

## Scoring

总分 100：

| 维度 | 分值 | 说明 |
|---|---:|---|
| 状态文件结构 | 15 | `.state.json` 的 `phase/phases/tasks/slot/items` 结构完整性 |
| 文档完整性 | 15 | `index.md`、slot manifest、item 文件和 backend `finalize.md` |
| Item 可执行性 | 20 | item 足够小、步骤明确、验证命令明确、边界清晰 |
| 内容一致性 | 20 | 与设计文档、PRD、用户故事、仓库路径和术语一致 |
| 依赖与恢复 | 15 | item DAG 合法、handoff 可追溯、失败可恢复 |
| 文档规范 | 10 | Markdown 结构和格式规范 |
| 代码示例质量 | 5 | 示例可读、可执行、不误导 |

## Severity

### P0

- `.state.json` 缺失或格式错误
- `.state.json` 含旧状态字段或 `agents` 根字段
- 缺少核心 phase/slot/item/finalize 结构
- 阶段目录、manifest、item 文件缺失
- item 依赖不存在或成环
- manifest 未覆盖全部 items
- 新旧结构混用
- 阶段依赖关系错误
- 命令、路径、阶段链路经仓库和规范双重验证后确认会直接导致 `/t-run` 无法执行

出现 `confirmed P0` 时，必须拒绝进入 `/t-run`。

### P1

- slot 状态与 item 聚合状态不匹配
- item 缺少关键章节
- item 超过拆分阈值且无合理说明
- item 职责混杂，单次 agent 调用高概率无法完成
- 下游 item 缺少 handoff 追溯
- backend 缺少 `awaiting_finalize` 收口语义
- `finalize.md` 缺少必要收口/重试说明
- 设计文档与任务文档严重不一致但暂不直接阻塞执行

### P2

- 示例可读性差
- Markdown 结构可优化
- 表达不够具体但不影响执行
- item 命名可读性不足

## Report Requirements

报告必须包含：

- 总分、等级、是否可进入 `/t-run`
- 状态文件验证结果
- 阶段依赖验证结果
- item DAG 验证结果
- 旧结构残留检查结果
- 每个维度得分与扣分证据
- 实际调用的 agent 集合
- `confirmed / disputed / assumption` 分类摘要
- P0/P1/P2 问题列表
- 明确修复步骤
- 已排除的误报/争议项（如有）

等级建议：

- `90-100`: 优秀，可进入实施
- `75-89`: 良好；仅在无 `confirmed P0` 时可进入实施
- `60-74`: 需改进；有 `confirmed P0` 时必须先修
- `<60`: 不合格，建议重新规划

## Hard Gates

- 分项分值之和必须等于 100
- 每个扣分项必须有文件定位
- 每个 P0/P1 必须同时有任务文档证据和真源证据
- `confirmed P0 > 0` 时，不得进入 `/t-run`
- `disputed` 或 `assumption` 不得计入 P0
