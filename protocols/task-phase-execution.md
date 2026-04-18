# Task Phase Execution Contract

定义 `t-task` 与 `t-run` 共用的 phase/slot/item 编排规则。

## Phase Order

- `backend`
- `frontend`
- `demo`

依赖关系：

- `backend` 无前置
- `frontend` 依赖 `backend == completed`
- `demo` 依赖 `frontend == completed`

## Slot Order

- backend: `dev -> test -> accept`, 完成后进入 `finalize`
- frontend: `dev -> test -> accept`
- demo: `dev -> accept`

## Execution Unit

`/t-run` 只执行 item 文件：

- `backend/dev/*.md`
- `backend/test/*.md`
- `backend/accept/*.md`
- `frontend/dev/*.md`
- `frontend/test/*.md`
- `frontend/accept/*.md`
- `demo/dev/*.md`
- `demo/accept/*.md`

不直接执行：

- `index.md`
- `dev.md`
- `test.md`
- `accept.md`
- `finalize.md`

## Item Selection Rules

1. 读取目标 phase 的 slot 清单。
2. 按 slot 顺序扫描 items。
3. 同一 slot 内按 DAG 拓扑顺序找可执行 item。
4. 同时存在多个可执行 item 时，优先 slot manifest 顺序；缺失时按 item ID 字典序。
5. 仅执行 `pending` 或 `failed` item。
6. 重试 `failed` item 前，依赖必须全部 `completed`。
7. 依赖未满足时不得跳过执行下游 item。
8. 任意时刻最多只允许一个 item 处于 `running`。

## Required Context for Item Agents

启动 item agent 时最少提供：

1. agent 规范文件
2. `feature`, `phase`, `slot`, `item_id`
3. 当前 item 文件全文
4. 当前阶段 `index.md`
5. 直接依赖 item 的 handoff 摘要与文件路径

可选增强：

- 当前 slot manifest
- 由 `context-isolator` 提取的设计摘要
- 当前 phase 的最小状态切片
- 当前 item 的 completion criteria / validation

## Failure Handling

- 状态文件缺失或损坏：终止并提示先运行 `/t-task`
- DAG 成环、依赖缺失、item 文件缺失：终止并提示运行 `/t-task-check`
- item 执行失败：写回 `last_error`，阻断依赖该 item 的后续执行
- 同时发现已有 `running` item：终止，不启动新 agent
