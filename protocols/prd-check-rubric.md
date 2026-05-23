# PRD Check Rubric

定义 `t-prd-check` 的统一评分、扣分和问题分级标准。

## Evaluation Goals

- 验证 PRD 文档完整性和规范性
- 检查 PRD HTML Preview 的存在性、可审阅性和 PRD 一致性
- 评估用户故事质量
- 检查 PRD 与用户故事的一致性
- 检查是否错误混入接口、建表、schema 等实现细节

## PRD Checks

### Base Sections

权重 50%。

| 检查项 | 模式 | 权重 |
|---|---|---:|
| 标题元数据 | `^\*\*创建时间\*\*\|^\*\*优先级\*\*` | 5 |
| 相关用户故事 | `^## 1\. 相关用户故事` | 10 |
| 范围界定 | `^## 2\. 范围界定` | 20 |
| 需求概述 | `^## 3\. 需求概述` | 10 |
| 业务规则与状态 | `^## 4\. 业务规则与状态` | 5 |
| 功能需求 | `^## 5\. 功能需求` | 10 |
| API 相关约束 | `^## [0-9]+\. API 相关约束` | 10 |
| 前端/交互约束 | `^## [0-9]+\. 前端/交互约束` | 10 |
| 已确认决策与待确认假设 | `^## [0-9]+\. 已确认决策` | 5 |
| 参考资料 | `^## [0-9]+\. 参考资料` | 15 |

### User Story References

权重 20%。

| 检查项 | 验证方式 | 权重 |
|---|---|---:|
| 用户故事链接有效性 | 检查引用链接是否存在 | 10 |
| 优先级标注 | 是否有 P0/P1/P2 标注 | 5 |
| 优先级汇总表 | 是否有优先级汇总章节 | 5 |

### Layering and Forbidden Content

权重 30%。

| 检查项 | 验证内容 | 扣分 |
|---|---|---:|
| 接口说明引用 | API 章节包含相关接口说明或设计文档引用 | 0 / -5 |
| 能力边界 | API 章节描述能力范围、访问控制、边界原则 | 0 / -5 |
| 端点明细 | 不出现 `GET /api`、`POST /api`、`PUT /api`、`DELETE /api` | 0 / -10 |
| schema 表格 | 不出现请求/响应字段表或参数表 | 0 / -5 |
| 数据库设计 | 不出现 `CREATE TABLE`、`ALTER TABLE`、`migration`、`数据库表` | 0 / -5 |
| 代码类型示例 | 不出现 `pub struct`、`interface Xxx`、技术代码块 | 0 / -5 |
| 技术设计承接 | 不出现 `技术设计承接`、`.ai/design/`、`.ai/future/` | 0 / -10 |
| 过去时/历史内容 | 不出现 `已废弃`、`旧系统`、`原有`、`重设计前`、`架构迁移说明` | 0 / -5 |
| 代码文件索引 | 不出现 `相关文件索引` 章节或具体代码文件路径列表 | 0 / -10 |
| 实施进度状态 | 不出现 `当前实现状态`、`已完成`、`未完成`、`已实现`、`未实现`、`完成比例`、`实现进度` 等易过期任务状态 | 0 / -10 |

### HTML Preview Checks

权重 20%。具体契约参考 `protocols/prd-preview-contract.md`。

| 检查项 | 验证内容 | 权重 / 扣分 |
|---|---|---:|
| Preview 存在性 | `docs/prd/<domain>/<feature>.html` 与 PRD 同目录同名 | 5 |
| 来源可追溯 | 包含来源 PRD 路径和 `data-prd-source` | 3 |
| 固定审阅区域 | 包含 `Overview`、`Scope`、`Flow`、`States`、`Rules`、`Acceptance`、`Assumptions` | 5 |
| 技术栈无关 | 不依赖 npm、构建工具、CDN、目标项目组件或外部脚本样式 | 3 |
| 示例数据声明 | 使用示例数据时标注“示例数据，不是接口契约” | 2 |
| UI 目标体验边界 | 前端/交互 Preview 聚焦 PRD 定义的目标体验和关键状态，不复刻已有实现 | 0 / -5 |
| PRD 一致性 | 与 PRD 的目标、范围、流程、业务状态、规则和验收目标一致，不引入未声明的新业务规则、权限规则或验收目标 | 0 / -10 |
| Preview 禁止内容 | 不出现端点清单、schema、建表、迁移、类型定义 | 0 / -10 |

## User Story Checks

### Structure

权重 30%。

| 检查项 | 验证方式 | 权重 |
|---|---|---:|
| 用户故事格式 | 检查“作为 / 我希望 / 从而”三要素 | 10 |
| GWT 验收标准 | 检查 Given/When/Then 格式 | 15 |
| 场景完整性 | 至少 1 个成功场景 + 关键失败场景 | 5 |

### INVEST

权重 40%。

- Independent
- Negotiable
- Valuable
- Estimable
- Small
- Testable

### Forbidden Content

权重 30%。

| 类型 | 检查模式 | 扣分 |
|---|---|---:|
| 技术实现章节 | `【技术实现】` | -10 |
| 技术视角 | `系统支持\|后端需要\|使用 Redis\|数据库表` | -5 |
| 技术表格 | `Provider 表\|provider 表\|oauth_provider_config` | -5 |
| 实现细节 | `验证码 60 秒\|调用.*接口\|前端使用\|API 路径\|新增字段\|数据库迁移` | -5 |
| 代码示例 | ```(javascript\|typescript\|rust\|python\|go\|java)` | -5 |
| 无用户/价值 | `增加按钮\|实现导出\|优化流程` | -5 |
| 模糊表述 | `良好体验\|合理处理\|适当提示` | -3 |
| API 文档 | `GET /api\|POST /api\|HTTP 状态码` | -5 |
| 数据设计 | `CREATE TABLE\|ALTER TABLE\|索引\|建表` | -5 |

### New-Document Gate

创建时间少于 7 天的新文档必须满足：

- 无【技术实现】章节
- 无技术表格
- 无代码示例
- 无 API 文档
- 无建表、迁移、schema、类型定义等实现细节

违反任一规则 => P0。

## Consistency Score

- 用户故事链接有效性 × 5
- 优先级一致性 × 5
- 角色引用正确性 × 5

## Final Score

- `PRD Score = 基础章节得分 + 用户故事引用得分 - PRD 分层扣分`
- `Preview Score = Preview 存在性 + 来源可追溯 + 固定审阅区域 + 技术栈无关 + 示例数据声明 - Preview 一致性扣分 - Preview 禁止内容扣分`
- `User Story Score = 故事结构得分 + INVEST 得分 - 禁止内容扣分 - 质量门禁扣分`
- `Consistency Score = 链接有效性 + 优先级一致性 + 角色引用正确性`
- `Total Score = (PRD Score × 45%) + (User Story Score × 40%) + (Preview Score × 15%) + Consistency Score`

## Severity

### P0

- 缺少核心 PRD 章节
- 用户故事无验收标准
- 新文档含【技术实现】章节
- PRD 含端点、schema、建表等实现细节
- PRD 含技术设计承接、`.ai/` 路径引用或代码文件索引
- PRD 含当前任务是否完成、是否实现、完成比例、实现进度等易过期实施状态
- HTML Preview 含端点、schema、建表、迁移、类型定义等禁止内容

### P1

- PRD 缺少必要接口说明引用
- 验收标准模糊
- INVEST 原则明显违反
- 旧文档含技术表格
- 缺失同目录同名 HTML Preview
- HTML Preview 与 PRD 在目标、范围、流程、业务状态、规则或验收目标上描述不一致
- HTML Preview 依赖目标项目技术栈、构建工具或外部 CDN

### P2

- 前端/交互约束不完整
- 一般格式问题
- HTML Preview 缺少必要审阅区域、来源 PRD 路径或示例数据声明

## Output Requirements

控制台摘要和报告都必须包含：

- 总分与评级
- P0/P1/P2 统计
- 质量门禁结果
- PRD 分层检查结果
- HTML Preview 检查结果
- 前 3 个关键问题
- 报告路径

详细报告应包含：

- 总体评估
- 质量门禁
- PRD 分层检查
- HTML Preview 检查
- 各功能详细得分
- P0/P1/P2 问题
- 优先修复建议
