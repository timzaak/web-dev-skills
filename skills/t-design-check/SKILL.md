---
name: t-design-check
argument-hint: [方案名称]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Task
  - Write
---

# 技术设计质量检查

运行时边界统一参考：`protocols/runtime-boundaries.md`

## 目标
- 评估技术设计文档的可实施性、完整性与一致性。
- 给出可复查的 100 分量化结果。
- 输出 P0/P1/P2 修复清单。
- 为后续任务拆解提供明确的设计质量门禁结论。

评分维度、严重级别和报告要求统一参考：`protocols/design-check-rubric.md`

## 使用方式
```bash
/t-design-check [方案名称]
```

| 参数 | 说明 |
|---|---|
| `[feature]` | 方案名称（必填） |

## 输入范围
- 设计文档：`.ai/design/[feature].md`
- 需求来源：`docs/user-stories/**/*.md`、`docs/prd/**/*.md`
- 规范来源：
  - `${CLAUDE_PLUGIN_ROOT}/guides/core/environment-and-testing-guide.md`
  - `${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md`
  - `${CLAUDE_PLUGIN_ROOT}/guides/backend/development.md`
  - `${CLAUDE_PLUGIN_ROOT}/guides/frontend/development.md`
  - `AGENTS.md`

## 执行流程
1. 校验设计文档是否存在。
2. 从设计文档提取引用的用户故事、PRD、接口、数据库变更、前端范围、测试策略。
3. 核对设计文档与需求来源的一致性。
4. 核对设计文档与项目规范的一致性。
5. 按 `protocols/design-check-rubric.md` 检查 API、数据库、前端与测试策略。
6. 生成评分与问题清单。
7. 写入报告：`.ai/quality/design-check-[feature]-[YYYYMMDD-HHMMSS].md`。

## 错误处理

| 错误码 | 触发条件 | 用户可见提示 | 恢复动作 |
|---|---|---|---|
| `DESIGN_DOC_MISSING` | 设计文档不存在 | 未找到设计文档 | 先运行 `/t-design [feature]` |
| `DESIGN_DOC_INVALID` | 设计文档缺少标题或主要章节结构 | 设计文档结构不完整 | 按模板补齐章节后重试 |
| `REQUIREMENT_SOURCE_MISSING` | 无法定位任何关联的用户故事或 PRD | 未找到可追溯的需求来源 | 在设计文档中补充引用后重试 |
| `REPORT_WRITE_FAILED` | 质量报告写入失败 | 无法写入检查报告 | 检查 `.ai/quality/` 目录权限后重试 |

## 示例

```bash
/t-design-check realm-user-rbac
```

输出：
```text
总分: 91/100 (优秀，可进入后续拆解)

需求追溯性: 19/20 (-1: 缺少一个用户故事来源)
现有实现分析准确性: 15/15
API 设计完整性: 18/20 (-2: 缺少 409 错误响应说明)
数据库设计完整性: 20/20
前端设计完整性: 9/10 (-1: 空态说明不足)
测试与验收策略: 10/10
文档规范与假设显式化: 5/5

P1 问题:
1. `4.2 API 接口设计` 缺少冲突场景错误响应说明

修复步骤:
1. 在关键写接口下补充 409/422 等业务错误响应
```

## 质量门禁
- 分项分值之和必须等于 100。
- 每个扣分项必须有文件定位。
- 结论必须可追溯到证据。

## 相关引用

- `protocols/runtime-boundaries.md`
- `protocols/design-check-rubric.md`
