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

## 任务列表
- {{AgentA}} -> dev.md
- {{AgentB}} -> test.md (depends: {{AgentA}})
- {{AgentC}} -> accept.md (depends: {{AgentA}}, {{AgentB}})

## Handoff
- `{{AgentB}}` 必须读取 `dev.md` 的文件路径与摘要
- `{{AgentC}}` 必须读取上一 slot 已写入文件的路径与摘要

## 执行说明
- `/t-run` 必须按 slot 顺序和 item DAG 串行执行 item 文件：
  - `{{AgentA}} -> dev/*.md`
  - `{{AgentB}} -> test/*.md`
  - `{{AgentC}} -> accept/*.md`
- 同一时刻只允许一个 item agent 运行；即使多个 item 依赖均已满足，也必须逐个执行
- `index.md` 只作为阶段概览、依赖与导航入口，不替代 slot 任务文件
- `/t-task` 生成时必须先写入上游 slot 文件，再调用下游 slot agent

## 执行流程
```mermaid
graph TD
    A[{{AgentA}}] --> B[{{AgentB}}]
    B --> C[{{AgentC}}]
    C --> D{通过?}
    D -->|Yes| E[完成]
    D -->|No| F[返回开发]
```

## 下一步
```bash
/t-task {{FeatureName}} --phase {{NextPhase}}
```
