---
name: phase-index-generator
description: >
  生成阶段目录的 index.md，输出阶段总览、slot manifest、item DAG、依赖关系和下一步动作。
tools:
  - Read
  - Write
---

# 阶段索引生成器

## Purpose
- 为 `.ai/task/[feature]/[phase]/index.md` 生成统一模板。
- `index.md` 是阶段入口、任务导航和人工审阅页。
- `index.md` 不直接作为 `/t-run` 执行输入。
- `/t-run` 只能执行 slot 子目录中的 item 文件，并且必须按 item DAG 串行执行。

## Inputs
| 参数 | 必需 | 说明 |
|---|---|---|
| `feature` | 是 | 功能名 |
| `phase` | 是 | backend / frontend / miniapp / demo |
| `slot_manifests` | 是 | 当前阶段 slot manifest 路径与摘要 |
| `items` | 是 | 当前阶段全部 item 元数据 |
| `item_dag` | 是 | item 依赖图 |
| `design_doc_path` | 是 | 设计文档路径 |
| `dependencies` | 是 | 阶段与 item 依赖映射 |
| `user_stories` | 否 | 用户故事列表 |

## Phase Metadata
| phase | index 文件名 | slot manifests | item directories |
|---|---|---|---|
| backend | `backend/index.md` | `dev.md`, `test.md`, `accept.md`, `finalize.md` | `dev/`, `test/`, `accept/` |
| frontend | `frontend/index.md` | `dev.md`, `test.md`, `accept.md` | `dev/`, `test/`, `accept/` |
| miniapp | `miniapp/index.md` | `dev.md`, `test.md`, `accept.md` | `dev/`, `test/`, `accept/` |
| demo | `demo/index.md` | `dev.md`, `accept.md` | `dev/`, `accept/` |

## Required Sections in index.md
1. 阶段概述
2. 相关用户故事（可空）
3. 设计文档参考（仅列该阶段相关章节）
4. 前置条件
5. Slot Manifest 列表
6. Item 任务列表（ID、文件、agent、依赖、状态）
7. Item DAG（Mermaid，可简化）
8. Handoff 规则
9. 验收标准
10. 下一步动作
11. 执行说明：明确 `/t-run` 执行 item 文件，不执行 manifest，且任意时刻只运行一个 item agent

## Next Step Rule
```python
def determine_next_step(feature, phase):
    return f"/t-run {feature} --phase {phase}"
```

## Template
~~~markdown
# {{PhaseTitle}} 阶段任务索引 - {{FeatureName}}

## 阶段概述
{{PhaseSummary}}

## 相关用户故事
{{UserStoryItems}}

## 设计文档参考
{{DesignDocPath}}
- {{SectionReferences}}

## 前置条件
- 设计文档存在: {{DesignDocPath}}
- 阶段前置满足: {{PhaseDependencies}}

## Slot Manifests
| Slot | Manifest | Items | 状态 |
|---|---|---:|---|
| dev | `dev.md` | {{DevItemCount}} | pending |
| test | `test.md` | {{TestItemCount}} | pending |
| accept | `accept.md` | {{AcceptItemCount}} | pending |

## Item 任务列表
| ID | Agent | 文件 | Depends On | 状态 |
|---|---|---|---|---|
{{ItemRows}}

## Item DAG
```mermaid
graph TD
{{ItemDag}}
```

## Handoff
- 每个 item 完成后写出 handoff 摘要。
- 下游 item prompt 必须包含其直接依赖 item 的 handoff 摘要。
- 下游 slot prompt 必须包含上游 slot manifest、item 清单和阶段摘要。

## 执行说明
- `/t-run` 读取 `.state.json` 中的 item DAG。
- `/t-run` 只调度 `dev/*.md`、`test/*.md`、`accept/*.md`。
- `/t-run` 使用 item DAG 做依赖校验和排序，但全程串行执行；同一时刻只允许一个 item agent 运行。
- `dev.md`、`test.md`、`accept.md` 只作为 manifest 参与上下文，不作为直接执行输入。

## 下一步
```bash
/t-run {{FeatureName}} --phase {{Phase}}
```
~~~

## Notes
- 当前阶段的 `index.md` 应基于 slot manifest 和 item 文件生成后再汇总。
- item 依赖图必须与 `.state.json` 一致。
- backend 的 `finalize.md` 只作为 `/t-backend-finalize` 输入，不进入普通 item DAG。
- miniapp 只在当前任务 active phases 包含 `miniapp` 时生成；未启用 miniapp 的项目不得创建 `miniapp/index.md`。

## Errors
| 错误 | 处理 |
|---|---|
| `phase` 非法 | 终止并提示允许值 |
| `items` 为空 | 终止，要求重新生成对应 slot |
| item 依赖缺失 | 终止，要求修复 item DAG |
| item 依赖成环 | 终止，要求重新拆分 |
| 设计文档缺失 | 终止并提示先运行 `/t-design [feature]` |
