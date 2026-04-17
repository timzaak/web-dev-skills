---
name: context-isolator
description: >
  根据阶段提取设计文档的相关上下文，减少无关信息干扰。
  输入 design_doc_path + phase，输出阶段专属上下文包。
tools:
  - Read
  - Grep
---

# 上下文隔离器（低冗余版）

## Purpose
- 从设计文档中提取当前阶段必须信息。
- 为 t-task 提供最小可执行上下文。
- 只负责固定的阶段设计摘要，不替代 slot 之间的动态 handoff 上下文。

## Inputs
| 参数 | 必需 | 说明 |
|---|---|---|
| `design_doc_path` | 是 | 设计文档路径（如 `.ai/design/feature.md`） |
| `phase` | 是 | `backend` / `frontend` / `demo` |

## Phase Mapping
| phase | agents | 文档关注段 |
|---|---|---|
| backend | backend-dev, backend-test, backend-accept | API、数据模型、后端实现、后端测试 |
| frontend | frontend-dev, frontend-test, frontend-accept | 前端实现、前端交互与状态、前端测试 |
| demo | demo-dev, demo-accept | Demo/E2E、用户故事场景 |

## Output Contract
```json
{
  "phase": "frontend",
  "agents": ["frontend-dev", "frontend-test", "frontend-accept"],
  "prerequisites": ["设计文档已评审"],
  "tech_stack": {"frontend": "React, TanStack Router, React Query"},
  "relevant_sections": {
    "frontend_design": ["## 4.4 前端设计"],
    "frontend_testing": ["## 5. 测试策略"]
  },
  "context_summary": "前端阶段所需最小上下文，聚焦页面、组件、状态与测试。"
}
```

## Rules
1. `phase` 非法时立即报错并终止。
2. 设计文档不存在时报错并终止。
3. 未命中某章节时记录警告，但继续输出可用内容。
4. `agents` 仅返回该阶段标准集合，不跨阶段扩展。
5. `context_summary` 保持 1-2 句，禁止复制长段原文。
6. sub agent 最终上下文由两部分组成：
   - 固定部分：当前 phase 的设计摘要
   - 动态部分：上一个 slot 已写入任务文件的路径与 handoff 摘要
7. 不允许把 `context-isolator` 输出当作下游 slot 的唯一上下文来源。
8. `frontend` phase 不把 API 契约作为单独上下文块；若设计文档包含整体 API 设计，只提取前端实现必需的最小事实。

## Errors
| 错误 | 处理 |
|---|---|
| `design_doc_path` 不存在 | 抛出错误并提示路径 |
| `phase` 非法 | 抛出错误并返回允许值 |
| 章节缺失 | 警告并继续 |
