# Task Phase Execution Contract

## Phases

`supported_phases` 固定为 `backend`, `frontend`, `miniapp`, `flutter`, `demo`。

`active_phases` 只包含当前 feature 需要生成和执行的阶段。`miniapp` 仅在项目根目录存在 `miniapp/`，或设计文档明确包含小程序交付时启用。`flutter` 仅在目标项目/子目录的 `pubspec.yaml` 声明 Flutter SDK，或设计文档明确包含 Flutter 交付时启用。

默认顺序：

- Web 项目：`backend -> frontend -> demo`
- 多端项目：`backend -> frontend/miniapp/flutter -> demo`，中间阶段只包含实际交付端，固定排序为 `frontend -> miniapp -> flutter`

## Slot Order

- backend: `dev -> test -> accept`
- frontend: `dev -> test -> accept`
- miniapp: `dev -> test -> accept`
- flutter: `dev -> test -> accept`
- demo: `dev -> accept`

## Execution Unit

`/t-run` 只执行以下 item 文件：

- `{backend,frontend,miniapp,flutter}/{dev,test,accept}/*.md`
- `demo/{dev,accept}/*.md`

不直接执行 `index.md`, `dev.md`, `test.md`, `accept.md`。

## Item Selection

- 首次选择 item 前，按 `${CLAUDE_PLUGIN_ROOT}/protocols/task-state-contract.md` 的 Execution Entry Transition 将目标 phase 的 `generated` item 归一化为 `pending` 并持久化；归一化失败时不得启动 agent。
- 按 [Slot Order](#slot-order) 扫描目标 phase；同一 slot 内严格按 slot manifest 的 item 表格从上到下执行。
- manifest 必须覆盖 `.state.json` 中当前 slot 的全部 item，且每个 item 只能出现一次；顺序缺失或不一致时终止执行。
- 选择顺序中的第一个 `pending` 或 `failed` item；后续 item 不得越过它提前执行。
- `completed` 或 `skipped` item 直接越过，不重复执行。
- 除上述一次性启动归一化外，`/t-run` 在调度单个 item 前不更新状态；中断恢复时重新选择顺序中的第一个 `pending` 或 `failed` item。

## Agent Context

启动 item agent 时至少提供：

- agent 规范文件（调用规则见 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md`）
- `feature`, `phase`, `slot`, `item_id`
- 当前 item 文件全文
- 当前阶段 `index.md`
- 当前 item 之前已完成 item 的状态、文件路径与必要 `Handoff` 片段

可选提供当前 slot manifest、阶段设计摘要、最小状态切片、completion criteria / validation。

当前阶段 `index.md` 必须包含 `Decision ID | Status | Task/Item Location | Notes` 追踪表，覆盖影响该 phase 的 Active Decision。受具体决定约束的 item 在 `Goal` 或 `Handoff` 引用稳定 DEC ID；不得采用 Superseded Decision。

## Item Contract

每个 item 必须能让 `/t-run` 单独恢复执行，并包含：

- `id`: 稳定 ID，例如 `BE-D01`, `FE-T02`, `MA-A01`, `FL-T01`, `DE-A01`
- `title`
- `agent`

item 正文只使用以下章节：

- `## Goal`：当前 item 的交付目标、边界和失败归因。
- `## Work`：当前 agent 需要执行的具体动作。
- `## Files`：预计新增、修改或重点检查的目标项目路径。
- `## Validation`：目标项目真实命令、脚本或验收证据。
- `## Handoff`：给顺序中后续 item 或 slot 的必要交接信息；没有交接内容时写 `None`。

backend/test item 还必须符合 [Backend Test Item Types](#backend-test-item-types)。

规划原则：

- 单个 item 应能由一个 agent 在一次可独立验收的执行中完成。
- item 默认承载一个可独立交付的责任闭环；同一业务能力、接口能力、页面主流程、组件族或测试资产闭环内的强耦合改动应优先合并。
- 技术层、文件类型或实现步骤只能作为辅助线索；拆分必须让每个 item 都能独立验证，并降低失败归因成本。
- 不合并弱相关、验证命令不同或失败归因会互相污染的主交付物。
- 测试代码编写与测试运行/修复闭环必须拆开。
- 不把大范围跨模块重构、多个页面域或多个完整用户故事塞进同一 item。
- 验证命令必须来自目标项目实际脚本、package 名或配置。涉及 Maven module 时，item 中任何带 `--module <name>` 的命令的 `<name>` 必须是 `backend/` 下实际存在的 Maven reactor module（见父 `pom.xml` 的 `<modules>` 段或对应子目录的 `pom.xml`）；不得假设 module 名等于目录名。生成 item 前先 `Read` 对应 `pom.xml` 核对，再写入 validation 或 steps。

## Refactor And Legacy Cleanup

当设计文档或用户要求大范围重构、替换旧架构、迁移旧模块、移除旧接口/状态/字段，且没有真实外部兼容约束时，`/t-task` 必须按“先清理旧实现，再重写目标结构”规划任务。

真实兼容约束只来自 PRD、设计文档、外部 API 契约、数据保留、跨版本部署或用户显式要求；“先共存以后再删”不是兼容理由。

此类任务至少包含一张旧代码清理清单，作为独立 item 或写入相关 item 的 `## Handoff`。清单必须覆盖：

- 待迁移或删除的旧代码、入口、配置、测试、文档引用和数据结构。
- 删除边界：必须删除项，以及因真实兼容约束暂时保留项。
- 执行顺序：先删旧实现和旧引用，再改写或新增代码。
- 残留检查：用 `rg` 或项目等价工具搜索旧路径、旧符号、旧接口和旧状态名。

禁止在无真实兼容要求时新增 adapter、bridge、fallback、alias、deprecated wrapper、双路径分支或双写逻辑；也不得只新增新实现而不删除被替代的旧入口、旧测试和旧文档引用。

## Splitting Heuristics

按复杂度增加流程重量：

- 简单任务保持轻量：单一领域、单一交付物、少量文件、验证明确时可合并。
- 中等任务按责任闭环拆分；强耦合且同一验证命令覆盖的实现动作优先放在同一 item，降低 handoff 和上下文切换成本。
- 复杂任务必须拆细，尤其是跨领域、跨用户故事、跨测试闭环、跨外部契约或失败后难恢复的任务。

### Slot Item Count Limits

为避免任务被过度拆分，每个 slot 的 item 数量设置默认上限：

| slot | 默认上限 |
|---|---|
| dev | 3 |
| test | 2 |
| accept | 2 |

demo 阶段的 `accept` slot 同样适用 `accept` 上限。

超过上限时的处理规则：

- slot agent 必须返回 `needs_user_answer`；由 `t-task` 使用 `AskUserQuestion` 确认是否允许更多拆分，回答前不得写入该 slot。
- 向用户确认时应说明：当前 slot、建议 item 数量、超过上限的理由（如跨领域、跨测试闭环、失败后难恢复等）、合并后可能导致的单次执行规模或失败归因风险。
- 用户允许后，在 slot manifest 或相关 item 的 `Handoff` 中记录上限、实际数量和授权理由；用户未允许时，合并到上限以内。
- 合并后单个 item 变大但责任闭环单一、验证命令定向、失败可定位的，不应因此记 P1。

优先合并的情况：

- 同一资源或业务操作的 DTO、domain、repository、service/use case、HTTP/OpenAPI 改动强耦合，并由同一组定向检查或场景测试覆盖。
- 同一页面域的 API/type 适配、状态管理、主流程、错误态、权限态由同一页面验证闭环覆盖。
- 同一测试场景下的 fixture、helper、mock、测试文件注册需要一起变更，且单独拆开不能独立验收。
- 多个步骤失败时都会回到同一 agent、同一文件集和同一验证命令，拆开只会增加 handoff。

任一条件成立时必须拆分：

- 预计超过 2 天。
- 预计修改超过 10 个核心文件。
- 跨越超过 3 个领域模块或页面域。
- 超过 14 个主要步骤。
- 单个 item 文件预计超过 30KB，且不是验收清单。
- `Goal` 或 `Work` 包含两个弱相关、可独立交付、独立验证的主交付物。
- 单个 HTTP/API item 覆盖超过 10 个 endpoint，或混合不同资源域、读写操作、状态操作、配置类接口，导致验证命令、失败归因或 review 边界不清。
- 单个 demo item 同时创建复用 helper 并覆盖多个完整用户故事或多个业务状态流，导致失败时无法区分测试基础设施问题和故事流程问题。

推荐拆分维度：

- backend dev：按资源能力、业务操作、外部集成或 SDK/API 影响闭环拆分；不要仅因数据库、domain、repository、service、HTTP/OpenAPI 分层不同而拆。
- backend HTTP/API：读模型、写操作、状态操作、配置类接口可作为拆分线；同一资源的少量强耦合端点可合并，前提是能用定向 Maven 编译测试或场景测试验证。
- backend unit test：低价值单测不单独规划；必要的高价值单测归入对应 backend/dev item。
- frontend dev：按页面域、用户流程、可复用组件族或数据闭环拆分；同一页面闭环内的 API/type、schema/query/store、主流程、状态与错误处理、权限与空态可合并。
- miniapp dev：按页面域、平台能力或模板/主题闭环拆分；页面注册、组件主流程、主题接线、token/icon 集成在同一闭环内可合并。
- flutter dev：按 feature、用户流程、平台能力或数据闭环拆分；同一 feature 内的 View、Notifier、Repository 适配与关键状态可合并。
- demo dev：按用户故事、业务状态流或测试基础设施闭环拆分；同一故事内强相关的 fixture/helper/Page Object authoring 可合并。
- accept：design consistency、public API contract、business rules、permission/security、test evidence、demo readiness；纯技术方案聚焦技术目标、兼容性、公共契约、迁移/配置影响、测试证据和回归风险。

backend/test、frontend/test、miniapp/test、flutter/test、demo/dev 的测试拆分与执行见 [Test Execution Consolidation](#test-execution-consolidation) 与 [Backend Test Item Types](#backend-test-item-types)。

## Test Execution Consolidation

测试规划遵循集中执行：

- authoring item 负责写测试资产；runner item 汇总本轮相关 authoring 产物并执行。
- runner 必须排在其覆盖的全部相关 authoring item 之后，并记录覆盖来源。
- runner 必须包含 `Expected Test Manifest`：测试文件、测试函数/用例标题、来源 authoring item、预期 runner 命令。
- runner 只运行覆盖来源所需的最小可靠定向测试、类型检查或构建命令；全量测试只在定向范围无法覆盖风险，或发布/验收门禁要求时使用，并说明原因。
- Java/Maven 编译、TypeScript 编译、Vite/Vitest 预构建、Taro 构建或 Playwright 项目启动等等待成本允许存在，但 item 必须记录实际命令和失败/耗时证据。
- 可用 `uv run scripts/check-test-runner-coverage.py <feature> --layer <backend|frontend|miniapp|flutter|demo>` 校验 runner 覆盖关系；backend 做动态命中校验，frontend/miniapp/flutter/demo 默认做静态命令覆盖校验。

适用阶段：

- backend/test：集中 runner 执行定向后端测试。
- frontend/test：全部 Vitest/MSW authoring 后执行定向 `npm run test:run -- [pattern]`，按需加 `type-check`。
- miniapp/test：测试或验证资产完成后执行相关 `typecheck`、构建或专项 gate。
- flutter/test：单元/widget 测试资产完成后执行相关定向 `flutter test`；按改动范围执行 integration_test、Patrol、analyze 或构建门禁。
- demo/dev：Demo/E2E、fixture、Page Object 完成后执行相关 `demo-test-runner.py [test-file] --grep [pattern]` 或少量相关文件。

## Backend Test Item Types

backend/test item 必须声明 `test_item_type`：

- `authoring`：由 `backend-test` 编写或维护场景测试、helper、模块注册，只做编译验证。
- `runner`：由 `general-purpose` 按 `${CLAUDE_PLUGIN_ROOT}/protocols/backend-test-execution.md` 汇总 authoring item 后执行定向测试、失败分类、生产代码修复委派和重测。

backend/test slot 必须显式规划测试执行闭环：

- 每个新增或修改场景测试的 `authoring` item 必须被 runner 覆盖。
- runner 按验证范围拆分；同一业务场景或 package/module 优先合并。
- `runner.agent` 必须为 `general-purpose`。
- runner 必须排在本轮全部相关 `authoring` item 之后。
- runner 必须在 `Work` 或 `Validation` 中引用 `${CLAUDE_PLUGIN_ROOT}/protocols/backend-test-execution.md`，并按该协议执行。
- runner 中每条后端测试命令都必须以 `uv run scripts/backend-test.py --` 开头；没有 filter 时也保留结尾 `--`。
- runner 默认必须带 filter 或 `-E` 表达式来收敛到 Expected Test Manifest 覆盖范围；只有定向范围无法可靠覆盖风险或存在明确门禁要求时，才允许规划全量 `uv run scripts/backend-test.py --`，并必须写明升级原因。
- 不得写 `${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py`，不得省略 `--`，目标项目本地脚本失败时不得改用插件脚本绕过。
- backend/accept 由固定 slot 顺序保证在 backend/test 之后执行；backend/test 必须至少包含一个 runner，且 runner 位于相关 authoring item 之后。

缺少 `test_item_type`、类型非法、runner 未引用后端测试执行协议、或 runner agent 不是 `general-purpose` 时，执行应终止并提示重新运行 `/t-task-check` 或重建任务。

## Failure Handling

- 状态文件缺失或损坏：终止并提示先运行 `/t-task`
- manifest 顺序无效、覆盖不完整或 item 文件缺失：终止并提示运行 `/t-task-check`
- item 执行失败：写回 `last_error`，停止当前 phase；再次运行时从该失败 item 恢复
