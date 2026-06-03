# Task Phase Execution Contract

定义 `t-task` 与 `t-run` 共用的 phase/slot/item 编排规则。

## Supported And Active Phases

`supported_phases` 固定为：

- `backend`
- `frontend`
- `miniapp`
- `demo`

`active_phases` 是当前项目/feature 实际启用的阶段列表，只包含本次任务需要生成和执行的阶段。

默认检测规则：

- 项目根目录存在 `miniapp/` 时启用 `miniapp`
- 设计文档明确包含小程序交付内容时启用 `miniapp`
- 否则不启用 `miniapp`，不得生成或要求执行 miniapp 阶段

依赖关系：

- `backend` 无前置
- `frontend` 依赖 `backend == completed`
- `miniapp` 依赖 `frontend == completed`
- `demo` 依赖 `active_phases` 中排在它之前的最后一个交付阶段 completed

默认阶段顺序：

- 无 miniapp：`backend -> frontend -> demo`
- 有 miniapp：`backend -> frontend -> miniapp -> demo`

## Slot Order

- backend: `dev -> test -> accept`，随后由用户显式运行 `/t-backend-finalize [feature]`
- frontend: `dev -> test -> accept`
- miniapp: `dev -> test -> accept`
- demo: `dev -> accept`

## Execution Unit

`/t-run` 只执行 item 文件：

- `backend/dev/*.md`
- `backend/test/*.md`
- `backend/accept/*.md`
- `frontend/dev/*.md`
- `frontend/test/*.md`
- `frontend/accept/*.md`
- `miniapp/dev/*.md`
- `miniapp/test/*.md`
- `miniapp/accept/*.md`
- `demo/dev/*.md`
- `demo/accept/*.md`

不直接执行：

- `index.md`
- `dev.md`
- `test.md`
- `accept.md`
- `finalize.md`

backend 的 `finalize.md` 只作为 `/t-backend-finalize` 输入，不得由 `/t-run` 自动执行。

## Item Selection Rules

- 读取目标 phase 的 slot 清单。
- 按 slot 顺序扫描 items。
- 同一 slot 内按 DAG 拓扑顺序找可执行 item。
- 同时存在多个可执行 item 时，优先 slot manifest 顺序；缺失时按 item ID 字典序。
- 仅执行 `pending` 或 `failed` item。
- 重试 `failed` item 前，依赖必须全部 `completed`。
- 依赖未满足时不得跳过执行下游 item。
- 任意时刻最多只允许一个 item 处于 `running`。

## Required Context for Item Agents

启动 item agent 时最少提供：

- agent 规范文件
- `feature`, `phase`, `slot`, `item_id`
- 当前 item 文件全文
- 当前阶段 `index.md`
- 直接依赖 item 的 handoff 摘要与文件路径

可选增强：

- 当前 slot manifest
- 由 `context-isolator` 提取的设计摘要
- 当前 phase 的最小状态切片
- 当前 item 的 completion criteria / validation

## Test Execution Consolidation

测试规划必须遵循集中执行原则：

- 测试运行 item 汇总本轮相关测试 authoring item 的产物。
- 测试运行 item 依赖本轮全部相关 authoring item，并记录覆盖来源。
- 测试运行 item 只运行能覆盖这些来源的最小可靠定向测试、类型检查或构建命令，不默认全量测试。
- 如果定向运行需要等待 Rust 编译、TypeScript 编译、Vite/Vitest 预构建、Taro 构建或 Playwright 项目启动，这属于允许的执行成本；item 必须记录实际命令和失败/耗时证据。
- 只有定向范围无法可靠覆盖风险，或发布/验收门禁明确要求时，才升级全量测试，并说明原因。

适用阶段：

- backend/test：用集中 runner item 执行定向后端测试。
- frontend/test：在全部 Vitest/MSW authoring item 后执行定向 `npm run test:run -- [pattern]`，按需加 `type-check`。
- miniapp/test：在全部测试或验证资产写完后执行相关 `typecheck`、构建或专项 gate。
- demo/dev：在全部 Demo/E2E、fixture、Page Object 写完后执行相关 `demo-test-runner.py [test-file] --grep [pattern]` 或少量相关文件。

## Backend Test Item Types

backend/test item 必须声明 `test_item_type`：

- `authoring`：由 `backend-test` 编写或维护场景测试、helper、模块注册，只做编译验证。
- `runner`：由 `general-purpose` 加载 `skills/t-backend-test-run/SKILL.md`，汇总相关 authoring item 后执行定向测试、失败分类、生产代码修复委派和重测。

backend/test slot 必须显式规划测试执行闭环：

- 每个新增或修改场景测试的 `authoring` item 必须被 runner 的覆盖来源显式纳入。
- runner 的拆分以验证范围为准：同一业务场景或 package/module 优先合并，互不相干且会影响恢复性的范围可拆分。
- `runner` item 的 `agent` 必须为 `general-purpose`，并声明 `uses_skill: skills/t-backend-test-run/SKILL.md`。
- `runner` item 必须依赖本轮全部相关 `authoring` item。
- backend/accept item 必须依赖至少一个 `runner` item，不得只依赖 `authoring` item。
- `t-backend-test-run` 不得作为 agent 出现在 item 中。

缺少 `test_item_type`、类型非法、runner 缺少 `uses_skill`、或把 `t-backend-test-run` 当作 agent 时，执行应终止并提示重新运行 `/t-task-check` 或重建任务。

## Failure Handling

- 状态文件缺失或损坏：终止并提示先运行 `/t-task`
- DAG 成环、依赖缺失、item 文件缺失：终止并提示运行 `/t-task-check`
- item 执行失败：写回 `last_error`，阻断依赖该 item 的后续执行
- 同时发现已有 `running` item：终止，不启动新 agent
