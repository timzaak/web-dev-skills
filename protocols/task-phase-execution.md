# Task Phase Execution Contract

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
- 当前 phase 的设计摘要
- 当前 phase 的最小状态切片
- 当前 item 的 completion criteria / validation

## Item Contract

每个 item 文件必须包含足够让 `/t-run` 单独恢复执行的信息：

- `id`: 稳定 ID，例如 `BE-D01`、`FE-T02`、`MA-A01`、`DE-A01`
- `title`
- `agent`
- `scope`
- `inputs`
- `steps`
- `expected_files`
- `validation`
- `depends_on`
- `handoff_summary`
- `completion_criteria`

backend/test item 额外要求见 [Backend Test Item Types](#backend-test-item-types)。

item 规划原则：

- 单个 item 应可由一个 agent 在一次可恢复执行中完成。
- 不合并可独立交付、独立验证的主交付物。
- 不把测试代码编写和测试运行/修复闭环放在同一个 item。
- 不把大范围跨模块重构、多个页面域或多个完整用户故事塞进同一 item。
- 验证命令必须来自目标项目实际脚本、package 名或配置。涉及 Cargo package 名时，item 中任何 `cargo check|run|test|clippy|nextest --package <name>` 的 `<name>` 必须与 `backend/<dir>/Cargo.toml` 中 `[package]` 段的 `name = "..."` 实际值一致；不得假设包名等于目录名（典型反例：`backend/core/` 的包名通常是 `<crate>-core`，而非 `core`）。生成 item 前先 `Read` 对应 `Cargo.toml` 核对，再写入 validation 或 steps。

## Refactor And Legacy Cleanup

当设计文档或用户明确要求大范围重构、替换旧架构、迁移旧模块、移除旧接口/状态/字段，且没有真实外部兼容约束时，`/t-task` 必须按“清理旧实现后重写”的方式规划任务。

兼容性只在 PRD、设计文档、外部 API 契约、数据保留、跨版本部署或用户显式要求时成立。仅为了让旧代码和新代码短期共存，不算兼容性理由。

这类任务至少要有一张旧代码清理清单，可以是独立 item，也可以写入相关 item 的 `handoff_summary`。清单按以下顺序组织：

1. 梳理所有要迁移或删除的旧代码、旧入口、旧配置、旧测试、旧文档引用和旧数据结构。
2. 写明删除边界：哪些必须删，哪些因真实兼容约束暂时保留。
3. 先删除旧实现和旧引用，再在目标结构中改写或新增代码。
4. 用 `rg` 或项目等价工具搜索旧路径、旧符号、旧接口和旧状态名，确认没有无意义的过渡代码残留。

禁止项：

- 没有真实兼容要求时，为旧实现新增 adapter、bridge、fallback、alias、deprecated wrapper、双路径分支或双写逻辑。
- 把“先兼容、以后再删”作为默认实现策略。
- 只新增新实现而不删除已被替代的旧入口、旧测试和旧文档引用。

## Splitting Heuristics

任务拆分遵循“按复杂度增加流程重量”：

- 简单任务优先保持轻量：单一领域、单一主交付物、少量文件、验证命令明确且失败后容易恢复时，可以合并为一个 item。
- 中等任务按可独立验证的交付物拆分：拆分应减少恢复成本、review 成本和上下文漂移，而不是机械追求更细。
- 复杂任务必须拆细：跨领域、跨用户故事、跨测试闭环、跨外部契约或失败后难以恢复时，优先拆成可单独执行、单独验证、单独交接的 item。

以下触发条件任一成立，必须拆分：

- 预计超过 2 天才能完成。
- 预计修改超过 10 个核心文件。
- 跨越超过 3 个领域模块或页面域。
- 超过 14 个主要步骤。
- 单个 item 文件预计超过 30KB 且不是验收清单。
- scope 包含两个可独立交付、独立验证的主交付物（例如 `A + B`、两个页面、页面 + 弹窗、helper + 场景测试）。
- 单个 HTTP/API item 覆盖超过 10 个 endpoint，或把不同资源域、读写操作、状态操作、配置类接口混在同一 item 中。
- 单个 demo item 同时创建复用 helper 并覆盖多个完整用户故事或多个业务状态流。

各阶段推荐拆分维度：

- backend dev：数据库/实体、domain、repository、service/use case、HTTP/OpenAPI、外部集成、SDK/API 影响点。
- backend HTTP/API：DTO 与路由骨架、读模型/list/detail、写操作/create/update、状态操作、配置类接口分别拆分；每个 item 必须能用定向 `cargo check` 或场景测试验证。
- backend unit test：不得规划“为新增 struct/DTO/builder/getter/常量补单测”这类低价值 item；确有必要的高价值单元测试归入对应 backend/dev item。
- frontend dev：API/type 适配、schema/query/store、页面主流程、状态与错误处理、权限与空态；一个 item 默认只交付一个页面域或一个可复用组件族，配置页、用户页、管理页、dialog 等可独立验证的 UI 不应合并。
- miniapp dev：页面注册、组件主流程、主题接线、token/icon 集成、平台差异处理。
- demo dev：先拆 fixtures/helpers，再拆主流程、异常/校验场景、权限场景；不要把 helper 和完整业务流放在同一个 item。
- accept：design consistency、public API contract、business rules、permission/security、test evidence、demo readiness。纯技术方案不涉及业务逻辑变动时，accept 应聚焦技术目标、兼容性、公共契约、迁移/配置影响、测试证据和回归风险，不强行补业务规则验收项。

backend/test、frontend/test、miniapp/test、demo/dev 的测试拆分与集中执行见 [Test Execution Consolidation](#test-execution-consolidation) 与 [Backend Test Item Types](#backend-test-item-types)。

## Test Execution Consolidation

测试规划必须遵循集中执行原则：

- 测试运行 item 汇总本轮相关测试 authoring item 的产物。
- 测试运行 item 依赖本轮全部相关 authoring item，并记录覆盖来源。
- 测试运行 item 必须包含 `Expected Test Manifest`，逐项列出本轮 authoring item 产生或修改的测试文件、测试函数/用例标题、来源 authoring item 和预期 runner 命令。
- 测试运行 item 只运行能覆盖这些来源的最小可靠定向测试、类型检查或构建命令，不默认全量测试。
- 如果定向运行需要等待 Rust 编译、TypeScript 编译、Vite/Vitest 预构建、Taro 构建或 Playwright 项目启动，这属于允许的执行成本；item 必须记录实际命令和失败/耗时证据。
- 只有定向范围无法可靠覆盖风险，或发布/验收门禁明确要求时，才升级全量测试，并说明原因。
- 可用 `uv run scripts/check-test-runner-coverage.py <feature> --layer <backend|frontend|miniapp|demo>` 校验 runner item 的预期测试清单与定向命令覆盖关系；backend 会通过 `cargo nextest list` 做动态命中校验，frontend/miniapp/demo 默认做静态命令覆盖校验。

适用阶段：

- backend/test：用集中 runner item 执行定向后端测试。
- frontend/test：在全部 Vitest/MSW authoring item 后执行定向 `npm run test:run -- [pattern]`，按需加 `type-check`。
- miniapp/test：在全部测试或验证资产写完后执行相关 `typecheck`、构建或专项 gate。
- demo/dev：在全部 Demo/E2E、fixture、Page Object 写完后执行相关 `demo-test-runner.py [test-file] --grep [pattern]` 或少量相关文件。

## Backend Test Item Types

backend/test item 必须声明 `test_item_type`：

- `authoring`：由 `backend-test` 编写或维护场景测试、helper、模块注册，只做编译验证。
- `runner`：由 `general-purpose` 加载 `${CLAUDE_PLUGIN_ROOT}/skills/t-backend-test-run/SKILL.md`，汇总相关 authoring item 后执行定向测试、失败分类、生产代码修复委派和重测。

backend/test slot 必须显式规划测试执行闭环：

- 每个新增或修改场景测试的 `authoring` item 必须被 runner 的覆盖来源显式纳入。
- runner 的拆分以验证范围为准：同一业务场景或 package/module 优先合并，互不相干且会影响恢复性的范围可拆分。
- `runner` item 的 `agent` 必须为 `general-purpose`，并声明 `uses_skill: skills/t-backend-test-run/SKILL.md`。
- `runner` item 必须依赖本轮全部相关 `authoring` item。
- `runner` item 中出现的每条后端测试命令都必须以 `uv run scripts/backend-test.py --` 开头；没有 filter 时也写成 `uv run scripts/backend-test.py --`。
- 不得写 `${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py`，也不得省略 `--`；目标项目本地脚本失败时不得改用插件脚本绕过。
- backend/accept item 必须依赖至少一个 `runner` item，不得只依赖 `authoring` item。
- `t-backend-test-run` 不得作为 agent 出现在 item 中。

缺少 `test_item_type`、类型非法、runner 缺少 `uses_skill`、或把 `t-backend-test-run` 当作 agent 时，执行应终止并提示重新运行 `/t-task-check` 或重建任务。

## Failure Handling

- 状态文件缺失或损坏：终止并提示先运行 `/t-task`
- DAG 成环、依赖缺失、item 文件缺失：终止并提示运行 `/t-task-check`
- item 执行失败：写回 `last_error`，阻断依赖该 item 的后续执行
- 同时发现已有 `running` item：终止，不启动新 agent
