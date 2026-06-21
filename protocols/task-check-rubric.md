# Task Check Rubric

## Source Of Truth Boundaries

单一真相源：

- 状态字段、状态取值和聚合规则只以 `${CLAUDE_PLUGIN_ROOT}/protocols/task-state-contract.md` 为准。
- phase/slot/item 执行顺序、active phases、backend test item 类型只以 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 为准。
- 评分、严重度和报告字段只以本文件为准。
- skill、agent、README 可以引用上述协议，但不得复制出第二套冲突规则。

## Evidence Priority

最终结论的证据优先级必须为：

`docs/`、`.ai/tech-research/`、`${CLAUDE_PLUGIN_ROOT}/guides/` 与仓库实际文件 > 当前 phase 任务文档 > sub agent 评审意见

规则：

- sub agent 只能提供候选问题，不能直接充当最终裁决
- 可从仓库发现的事实必须由主流程再次核验
- 规范冲突应标记为“规范冲突/待澄清”，不得直接记为 P0

## Schema Checks

`.state.json` 必须满足：

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

结构真相以 `${CLAUDE_PLUGIN_ROOT}/protocols/task-state-contract.md` 为准。

## Execution Checks

主流程检查：

- 设计文档存在
- `.state.json` schema 有效
- 阶段依赖正确
- `index.md`、slot manifest、item 文件齐备
- item DAG 合法：
   - item ID 唯一
   - `depends_on` 指向存在 item
   - 无依赖环
   - item 文件路径与 state 一致
   - manifest 覆盖全部 items
- item 文件包含必填字段
- 若当前阶段为 backend，backend/test slot 符合 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 的 authoring/集中 runner 覆盖与 `uses_skill` 要求
- 若当前阶段为 backend，backend/accept item 依赖 runner item，不只依赖 authoring item
- 若当前阶段为 frontend/miniapp/demo，涉及测试代码 authoring 时必须有集中定向执行 item，且不得默认规划全量测试
- 大范围重构、旧架构替换或旧模块迁移任务包含旧代码清理清单，并按 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 先删除旧实现再改写新结构
- 设计文档与任务文档一致
- 调用当前阶段对应 agents 做专业校验
- 主流程复核后生成最终结论

### Context Budget Rules

默认读取顺序：

- 先读取 `.state.json`、当前 phase `index.md` 和 slot manifest。
- 再抽取 item 关键字段，建立轻量 item 表。
- DAG、manifest 覆盖、agent/slot 匹配、backend test authoring/集中 runner 覆盖等结构检查优先基于轻量 item 表完成。
- 只有以下情况才读取 item 全文：
  - 关键字段缺失或冲突，需要定位具体证据。
  - 拆分阈值、职责混杂、设计一致性存在疑点。
  - subagent finding 需要主流程复核。
  - P0/P1 需要补齐任务文档证据。

subagent 上下文必须按 agent/slot 裁剪。不得默认向每个 subagent 传入当前 phase 的全部 item 全文；应传入相关 item 路径、关键字段摘要、必要片段和直接依赖 handoff 摘要。

## Agent Review Contract

每个被调度 agent 输出至少包含：

- `score`
- `findings`
- `fixes`
- `summary`

agent 评审边界：

- 只报告会影响 `/t-run` 执行、item 可恢复性、设计一致性或验收闭环的问题。
- P2 文风、命名、排版类建议默认不阻塞，不得升级为 P0/P1。
- 不得因为 agent 自身偏好的实现方式不同而报告问题；必须引用任务文档或真源规范。
- 同类问题应合并为一条 finding，并列出受影响 item，避免跨轮重复刷屏。

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
| 内容一致性 | 20 | 与设计文档、PRD、用户故事、技术预研、仓库路径和术语一致 |
| 依赖与恢复 | 15 | item DAG 合法、handoff 可追溯、失败可恢复 |
| 文档规范 | 10 | Markdown 结构和格式规范 |
| 代码示例质量 | 5 | 示例可读、可执行、不误导 |

## Severity

### P0

- `.state.json` 缺失或格式错误
- 缺少核心 phase/slot/item/finalize 结构
- 阶段目录、manifest、item 文件缺失
- item 依赖不存在或成环
- manifest 未覆盖全部 items
- 阶段依赖关系错误
- backend/test 缺少 runner item、runner 缺少 `uses_skill: skills/t-backend-test-run/SKILL.md`，或存在 authoring item 未被集中 runner 覆盖
- backend/accept item 只依赖 backend/test authoring item，未依赖 runner item
- frontend/miniapp/demo 涉及测试代码 authoring，却缺少依赖全部相关 authoring item 的集中定向执行 item
- 命令、路径、阶段链路经仓库和规范双重验证后确认会直接导致 `/t-run` 无法执行

出现 `confirmed P0` 时，必须拒绝进入 `/t-run`。

### P1

- slot 状态与 item 聚合状态不匹配
- item 缺少关键章节
- item 超过拆分阈值，或职责、验证、恢复边界可疑且无合理说明
- item 职责混杂，单次 agent 调用高概率无法完成
- item 合并多个可独立交付、独立验证的主交付物
- HTTP/API item 覆盖超过 7 个 endpoint，或混合不同资源域、读写操作、状态操作、配置类接口，导致单次执行或验证闭环不可恢复
- item 略大但 scope 单一、验证定向、依赖清晰、handoff 可恢复时不应仅因规模记 P1
- demo item 同时创建复用 helper 并覆盖多个完整用户故事或多个业务状态流
- 大范围重构缺少旧代码清理清单，清单没有说明删除边界与残留搜索方式，或未按 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 的“先删除旧实现再改写新结构”顺序组织
- 没有真实兼容约束（按 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 的兼容性来源判定：PRD、设计文档、外部 API 契约、数据保留、跨版本部署或用户显式要求均不成立）时，任务计划仍以兼容层、adapter、bridge、fallback、双路径分支或“以后再删”作为主路径
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
- P2 不阻塞 `/t-run`
