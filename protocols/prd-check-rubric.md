# PRD Check Rubric

## Evaluation Goals

- 验证 PRD 文档完整性和规范性
- 评估用户故事质量
- 检查 PRD 与用户故事的一致性
- 检查 `.ai/prd` 草稿与 `docs/prd` 已发布基线是否存在未说明冲突
- 检查 `.ai/user-stories` draft 与 `docs/user-stories` 已发布基线是否存在未说明冲突
- 检查是否错误混入接口、建表、schema 等实现细节
- 检查是否把用户决策静默写成待确认、假设、风险或模糊占位

## Scoring

本评分与 `${CLAUDE_PLUGIN_ROOT}/protocols/design-check-rubric.md`、`${CLAUDE_PLUGIN_ROOT}/protocols/task-check-rubric.md` 采用同一计分约定：

- 评分对象按制品拆为两类，各出一份 **100 分** 分数：`PRD Score` 和 `User Story Score`。
- 每份分数的维度分值之和必须等于 100；维度内逐项检查，达标得分，违规扣分，扣到 0 为止，不计负。
- 一致性不产生数值分，作为独立的 **pass / fail 门禁**。
- `needs_user_answer` 不参与任何扣分或 P0 计数，是评分前的阻塞状态。

| 分数 | 维度 | 分值 | 说明 |
|---|---|---:|---|
| PRD Score | 基础章节 | 40 | 必需章节齐备且标题规范 |
| PRD Score | 用户故事引用 | 20 | 引用有效、优先级标注完整、含汇总章节 |
| PRD Score | 分层与禁止内容 | 25 | 不混入实现细节、接口明细、建表、文件索引或过期实施状态 |
| PRD Score | 草稿与发布基线 | 15 | draft 与 published 的发布目标和差异可解释，无未说明冲突 |
| User Story Score | 结构 | 30 | 三要素、GWT 验收标准、场景完整性 |
| User Story Score | INVEST | 40 | 六原则逐项判定 |
| User Story Score | 禁止内容与门禁 | 30 | 不含技术实现、表格、代码、API、建表；新文档满足 New-Document Gate |

### PRD Score — 基础章节（40）

| 检查项 | 模式 | 分值 |
|---|---|---:|
| 标题元数据 | `^\*\*创建时间\*\*\|^\*\*优先级\*\*` | 2 |
| 相关用户故事 | `^## 1\. 相关用户故事` | 4 |
| 范围界定 | `^## 2\. 范围界定` | 8 |
| 需求概述 | `^## 3\. 需求概述` | 4 |
| 业务规则与状态 | `^## 4\. 业务规则与状态` | 2 |
| 功能需求 | `^## 5\. 功能需求` | 4 |
| API 相关约束 | `^## [0-9]+\. API 相关约束` | 4 |
| 前端/交互约束 | `^## [0-9]+\. 前端/交互约束` | 4 |
| 已确认决策 | `^## [0-9]+\. 已确认决策` | 2 |
| 参考资料 | `^## [0-9]+\. 参考资料` | 6 |

缺失章节扣除其对应分值；多余/无关章节不额外扣分。

### PRD Score — 用户故事引用（20）

| 检查项 | 验证方式 | 分值 |
|---|---|---:|
| 用户故事链接有效性 | 引用链接存在且可定位 | 10 |
| 优先级标注 | 含 P0/P1/P2 标注 | 5 |
| 优先级汇总表 | 含优先级汇总章节 | 5 |

用户故事链接可以指向 `docs/user-stories/...` 或 `.ai/user-stories/...`。`.ai/user-stories` 是发布前候选来源；检查报告必须标注其 draft 来源属性。

### PRD Score — 分层与禁止内容（25）

逐项核验，命中即扣对应分值；扣完 25 分为止。下列部分项命中同时升级为 P0（见 [Severity](#severity)），扣分与严重度独立记录。

| 检查项 | 验证内容 | 扣分 |
|---|---|---:|
| 接口说明引用 | API 章节包含相关接口说明或设计文档引用（缺失扣） | -2 |
| 能力边界 | API 章节描述能力范围、访问控制、边界原则（缺失扣） | -3 |
| 端点明细 | 不出现 `GET /api`、`POST /api`、`PUT /api`、`DELETE /api` | -5 |
| schema 表格 | 不出现请求/响应字段表或参数表 | -3 |
| 数据库设计 | 不出现 `CREATE TABLE`、`ALTER TABLE`、`migration`、`数据库表` | -3 |
| 代码类型示例 | 不出现 `pub struct`、`interface Xxx`、技术代码块 | -3 |
| 技术设计承接 | 不出现 `技术设计承接`、`.ai/design/`、`.ai/future/` | -3 |
| 过去时/历史内容 | 不出现 `已废弃`、`旧系统`、`原有`、`重设计前`、`架构迁移说明` | -2 |
| 代码文件索引 | 不出现 `相关文件索引` 章节或具体代码文件路径列表 | -3 |
| 实施进度状态 | 不出现 `当前实现状态`、`已完成`、`未完成`、`已实现`、`未实现`、`完成比例`、`实现进度` 等易过期任务状态 | -3 |

接口说明引用、能力边界两项为“应存在而缺失”的扣分；其余各项为“不应存在而出现”的扣分。

### PRD Score — 草稿与发布基线（15）

仅当 `.ai/prd/<domain>/<feature>.md` 存在时启用；草稿不存在则本维度按 0 分计，且不视为扣分。

| 检查项 | 验证内容 | 分值 |
|---|---|---:|
| 发布目标明确 | 能定位到 `docs/prd/<domain>/<feature>.md` 作为 create/update 目标 | 5 |
| 差异可解释 | 草稿相对正式 PRD 的目标、范围、规则、状态和验收目标变化可被识别 | 5 |
| 无核心冲突 | 草稿与正式 PRD 在业务边界、权限规则或验收目标上不存在未说明冲突 | 5 |

核心冲突（第三项未通过）同时记为 P0；前两项未通过记为 P1。

### User Story Score — 结构（30）

| 检查项 | 验证方式 | 分值 |
|---|---|---:|
| 用户故事格式 | 含“作为 / 我希望 / 从而”三要素 | 10 |
| GWT 验收标准 | 含 Given/When/Then 格式 | 15 |
| 场景完整性 | 至少 1 个成功场景 + 关键失败场景 | 5 |

### User Story Score — INVEST（40）

| 原则 | 判定 | 分值 |
|---|---|---:|
| Independent | 故事之间无强制交付顺序耦合 | 7 |
| Negotiable | 可协商，未把实现方案写死 | 6 |
| Valuable | 对用户/业务有清晰价值 | 7 |
| Estimable | 范围足够明确，可粗略估算 | 7 |
| Small | 单个故事可在一次迭代内交付 | 6 |
| Testable | 验收标准可被测试覆盖 | 7 |

INVEST 明显违反（如故事无法独立验收、价值不清或无法测试）同时记为 P1。

### User Story Score — 禁止内容与门禁（30）

| 检查项 | 检查模式 | 扣分 |
|---|---|---:|
| 技术实现章节 | `【技术实现】` | -8 |
| 技术视角 | `系统支持\|后端需要\|使用 Redis\|数据库表` | -4 |
| 技术表格 | `Provider 表\|provider 表\|oauth_provider_config` | -4 |
| 实现细节 | `验证码 60 秒\|调用.*接口\|前端使用\|API 路径\|新增字段\|数据库迁移` | -4 |
| 代码示例 | ```(javascript\|typescript\|rust\|python\|go\|java)` | -4 |
| 无用户/价值 | `增加按钮\|实现导出\|优化流程` | -3 |
| 模糊表述 | `良好体验\|合理处理\|适当提示` | -3 |
| API 文档 | `GET /api\|POST /api\|HTTP 状态码` | -4 |
| 数据设计 | `CREATE TABLE\|ALTER TABLE\|索引\|建表` | -4 |

扣完 30 分为止，不计负。

### New-Document Gate

创建时间少于 7 天的新文档必须满足：

- 无【技术实现】章节
- 无技术表格
- 无代码示例
- 无 API 文档
- 无建表、迁移、schema、类型定义等实现细节

违反任一规则直接判 **P0**，不参与上述扣分计算。

## Consistency Gate

一致性不产生数值分，作为独立的 pass / fail 门禁。任一项 fail 则一致性门禁 fail，并在报告中列出阻塞项。

| 检查项 | 验证方式 | 通过条件 |
|---|---|---|
| 用户故事链接 | PRD 中引用的链接可定位 | 全部有效 |
| 优先级一致 | PRD 与用户故事中的优先级一致 | 无冲突 |
| 角色引用 | 用户故事中的角色存在于 `docs/user-stories/_roles.md` | 全部存在 |

draft story / 草稿 PRD 与已发布基线的差异按 [PRD Score — 草稿与发布基线（15）](#prd-score--草稿与发布基线15) 计分；一致性门禁只看 PRD 与 user story 之间是否自洽，不重复计分。

## Final Score

- `PRD Score = 基础章节(40) + 用户故事引用(20) + 分层与禁止内容(25) + 草稿与发布基线(15)`，范围 0–100。
- `User Story Score = 结构(30) + INVEST(40) + 禁止内容与门禁(30)`，范围 0–100。
- 一致性：`pass / fail`。
- 不再有跨制品合并的 `Total Score`；报告同时给出两个分数与一致性门禁结论。

## Severity

### P0

- 缺少核心 PRD 章节
- 用户故事无验收标准
- 新文档含【技术实现】章节
- PRD 含端点、schema、建表等实现细节
- PRD 含技术设计承接、`.ai/` 路径引用或代码文件索引
- PRD 含当前任务是否完成、是否实现、完成比例、实现进度等易过期实施状态
- PRD 草稿与正式 PRD 在核心业务边界、权限规则或验收目标上存在未说明冲突
- Draft user story 与已发布 user story 在核心角色、权限规则或验收目标上存在未说明冲突
- 新文档违反 New-Document Gate 任一规则

`needs_user_answer` 不计入 P0/P1/P2；它是评分前阻塞状态，必须先完成用户裁决和源文档修正。

### P1

- PRD 缺少必要接口说明引用
- 验收标准模糊
- INVEST 原则明显违反
- 旧文档含技术表格
- PRD 草稿与正式 PRD 存在需要发布确认的差异但未说明差异性质
- Draft user story 与已发布 user story 存在需要发布确认的差异但未说明差异性质

### P2

- 前端/交互约束不完整
- 一般格式问题

## Hard Gates

- `PRD Score` 与 `User Story Score` 各自维度的分值之和必须等于 100。
- 每个扣分项必须有文件定位。
- 存在 `confirmed P0` 时，对应制品判不通过（PRD P0 → PRD 不通过；User Story P0 → User Story 不通过）。
- 一致性门禁 fail 时，整体判不通过，无论分数高低。
- 存在 `needs_user_answer` 时，不得给出通过结论，必须先用 `AskUserQuestion` 获取答案。
- `disputed` 或 `assumption` 不得计入 P0。
- P2 不阻断结论，仅作修复建议。

## Grade Bands

| 分数 | 等级 | 建议 |
|---|---|---|
| 90–100 | 优秀 | 可进入下游 |
| 75–89 | 良好 | 建议先修 P1 |
| 60–74 | 需改进 | 必须修 P0/P1 |
| <60 | 不合格 | 建议重写关键章节 |

PRD Score 与 User Story Score 分别按此表评级；一致性门禁 fail 或存在 confirmed P0 时，无论分数均判不通过。

## Decision Closure Gate

评分前必须按 `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md` 执行：

1. 读取 `.ai/decision-log/<feature>.md`（如存在）。
2. 运行 `python ${CLAUDE_PLUGIN_ROOT}/scripts/check-decision-closure.py <prd-path>`。
3. 对命中项区分 `fact_lookup`、`agent_decision`、`needs_user_answer`、`verification_action`。
4. 存在 `needs_user_answer` 时立即使用 `AskUserQuestion`；回答前不得评分或给出通过结论。
5. 回答写入 Decision Log 后，必须先由 `/t-prd` 更新 PRD，再重新扫描和检查。

PRD 完成态必须满足：

- `needs_user_answer=0`。
- “已确认决策”只包含带稳定 DEC ID 的已确认结论。
- 影响 PRD 的 Active Decision 均有追踪，不引用 Superseded Decision。
- 不含“待确认”“需确认”“待定”“TBD”“需要用户决定”“后续确认”“暂定”等未决表达。

## Output Requirements

控制台摘要和报告都必须包含：

- `PRD Score` 与 `User Story Score`（各自的总分、等级、分维度得分）
- 一致性门禁结论：`pass` / `fail`（fail 时列出阻塞项）
- P0/P1/P2 统计
- 质量门禁结果（New-Document Gate、Decision Closure Gate）
- PRD 分层检查结果
- 前 3 个关键问题
- 报告路径
- 用户澄清状态：无阻塞澄清 / 已通过 `AskUserQuestion` 解决 / 等待用户回答
- Decision Log 路径与决策闭合扫描结果

详细报告应包含：

- 总体评估
- 质量门禁
- PRD 分层检查
- 各功能详细得分（按本文件的维度表逐项）
- P0/P1/P2 问题
- 优先修复建议
