# Task Phase Execution Contract

## Phases

本节是阶段名称、启用条件和角色映射的唯一来源；解析参数、生成计划、恢复状态前读取。

`supported_phases` 为 `implementation`, `web-demo`。`implementation` 是不预设语言、框架或项目目录的实现阶段；`web-demo` 是保留的 Web 用户故事演示阶段。

`active_phases` 只包含当前设计实际要求的阶段。设计包含实现或测试资产交付时启用 implementation；明确要求 Web 演示且项目有真实 Web 交付面时启用 web-demo。默认顺序为 `implementation -> web-demo`，不适用项跳过。普通测试不自动启用 Demo。

非法或不适用的 `--phase` 必须停止并列出支持值与当前适用阶段。旧领域 phase 不自动映射到 implementation，不转换旧状态；保留原产物，按当前设计重新规划并复核已有证据。

业务验证责任与最终交付门禁见 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`。

## Slot Order

实现阶段默认 `dev -> accept`。需要测试角色新增或修改测试、fixture/helper 或专项验证脚本时使用 `dev -> test -> accept`。仅执行现有测试或静态检查归 dev，至少安排一项真实可执行验证，不为此生成 test。Demo 固定 `dev -> accept`，测试资产与执行均归 dev。

阶段计划记录测试选择理由与验证责任；dev 发现需要测试编写工作时先更新计划和状态再插入 test。accept 独立核查实际证据，不由前置检查替代。

## Design Inputs

规划或恢复时读取 `.ai/design/<feature>.md`；从主文档 §4.2 的实际路径读取适用模块设计，不按 phase 名猜文件名。跨模块依赖从主文档 §4.3 声明的唯一契约源读取。模块名称和边界来自目标项目，不预置领域集合。

## Skill Deliverables

设计涉及项目级 skill 时归 implementation，不新增 phase 或 Demo；dev 加载 `${CLAUDE_PLUGIN_ROOT}/guides/core/skill-authoring.md` 和 `${CLAUDE_PLUGIN_ROOT}/guides/core/skill-testing.md`。Validation 必须包含与风险相称的前向行为用例和触发边界检查，证据遵循验证协议。

## Role Mapping

| phase | dev | test（按需） | accept |
| --- | --- | --- | --- |
| implementation | project-dev | project-test | project-accept |
| web-demo | web-demo-dev | 不适用 | web-demo-accept |

角色规范取 Role Mapping 中同名文件，位于 `${CLAUDE_PLUGIN_ROOT}/agents/` 下。项目工程规则从目标项目 AGENTS.md、实际代码、配置和已确认的项目文档读取；缺失且影响决策时暴露给用户，不回退到预置技术栈。角色加载或调度按对应执行协议处理。

## Execution Unit

`/t-run` 只执行以下 item 文件：

- `<phase>/<slot>/*.md`，phase 按 Phases 校验，slot 按 Slot Order 确定且必须已规划。

不直接执行 `index.md`, `dev.md`, `test.md`, `accept.md`。

## Item Selection

- 选择 item 前核对本次范围内已有完成证据；相关输入已变或证据失效时，先按 `${CLAUDE_PLUGIN_ROOT}/protocols/task-state-contract.md` 的 Evidence Invalidation 重新打开受影响 item 及验收，再扫描顺序。
- 首次选择 item 前，按 `${CLAUDE_PLUGIN_ROOT}/protocols/task-state-contract.md` 的 Execution Entry Transition 将目标 phase 的 `generated` item 归一化为 `pending` 并持久化；归一化失败时不得启动 agent。
- 按 [Slot Order](#slot-order) 扫描目标 phase；同一 slot 内严格按 slot manifest 的 item 表格从上到下执行。
- manifest 必须覆盖 `.state.json` 中当前 slot 的全部 item，且每个 item 只能出现一次；顺序缺失或不一致时终止执行。
- 选择顺序中的第一个 `pending` 或 `failed` item；后续 item 不得越过它提前执行。
- `completed` 或 `skipped` item 直接越过，不重复执行；不存在的可选 test slot 不参与扫描。
- 除上述一次性启动归一化外，`/t-run` 在调度单个 item 前不更新状态；中断恢复时重新选择顺序中的第一个 `pending` 或 `failed` item。

## Agent Context

启动 item agent 时至少提供：

- agent 规范文件（调用规则见 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md`）
- `feature`, `phase`, `slot`, `item_id`
- 当前 item 文件全文
- 当前阶段 `index.md`（含验证责任表及相关上游待验证场景；验证记录遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`）
- 当前 item 之前已完成 item 的状态、文件路径与必要 `Handoff` 片段

可选提供当前 slot manifest、阶段设计摘要、最小状态切片、completion criteria / validation。

当前阶段 `index.md` 必须包含 `Decision ID | Status | Task/Item Location | Notes` 追踪表，覆盖影响该 phase 的 Active Decision。受具体决定约束的 item 在 `Goal` 或 `Handoff` 引用稳定 DEC ID；不得采用 Superseded Decision。

## Item Contract

每个 item 必须能让 `/t-run` 单独恢复执行，并包含：

- `id`: 稳定 ID，例如 `IM-D01`, `IM-T01`, `IM-A01`, `WD-D01`
- `title`
- `agent`

item 正文只使用以下章节：

- `## Goal`：当前 item 的交付目标、边界和失败归因。
- `## Work`：当前 agent 需要执行的具体动作。
- `## Files`：预计新增、修改或重点检查的目标项目路径。
- `## Validation`：目标项目真实命令、脚本或验收证据。
- `## Handoff`：给顺序中后续 item 或 slot 的必要交接信息；没有交接内容时写 `None`。


规划原则：

- 单个 item 应能由一个 agent 在一次可独立验收的执行中完成。
- item 默认承载一个可独立交付的责任闭环；同一业务能力、接口能力、页面主流程、组件族或测试资产闭环内的强耦合改动应优先合并。
- 技术层、文件类型或实现步骤只能作为辅助线索；拆分必须让每个 item 都能独立验证，并降低失败归因成本。
- 不合并弱相关、验证命令不同或失败归因会互相污染的主交付物。
- 测试编写与运行按下方 Test Execution Consolidation 选择合并或集中执行；不为一次小范围验证强制增加 item。
- 选择测试时先写出要防止的可观察回归与现有覆盖缺口，按目标项目已确认策略选择测试层次、框架和验证入口；策略缺失且影响规划时先由用户裁决。不为覆盖率数字或重复路径生成测试，没有增量测试价值时不生成 test slot。
- 不把大范围跨模块重构、多个页面域或多个完整用户故事塞进同一 item。
- validation 必须来自目标项目实际脚本、package 名或配置。

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

web-demo 阶段的 `accept` slot 同样适用 `accept` 上限。

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
- 单个 web-demo item 同时创建复用 helper 并覆盖多个完整用户故事或多个业务状态流，导致失败时无法区分测试基础设施问题和故事流程问题。

推荐按目标项目的能力、模块、用户流程或测试资产闭环拆分；同一闭环内的实现步骤优先合并。accept 覆盖设计一致性、公共契约、业务规则、权限、测试证据与交付准备情况。测试编写与执行按下节规划。

## Test Execution Consolidation

测试资产按责任和执行范围规划（包括 Demo/dev）：

- 同一角色负责、同一场景、验证命令可收敛的小闭环，默认在一个 item 内完成编写与定向执行；不增加独立 runner item，也不增加新的 slot 或状态类型。集中 runner 的定向范围与全量升级限制同样适用于合并 item。
- 多个 authoring item 共用环境/验证范围，或编写与失败修复涉及不同角色时，使用集中 runner；不要让各 authoring item 先重复执行同一套测试。
- 合并 item 的 Validation 使用 `### Expected Test Manifest` 列明测试文件、用例标题、来源 item（自身）及真实命令；运行失败时该 item 为 failed，恢复时先核对已有资产和证据，再完成未通过的验证，不重新生成全部测试。生产缺陷交回编排层分派 dev，测试角色不接管生产修复。

集中 runner 规则：

- authoring item 负责写测试资产；runner item 汇总本轮相关 authoring 产物并执行。
- runner 必须排在其覆盖的全部相关 authoring item 之后，并记录覆盖来源。
- runner 的 Validation 必须包含 `### Expected Test Manifest`：测试文件、测试函数/用例标题、来源 authoring item、预期 runner 命令。
- runner 只运行覆盖来源所需的最小可靠定向测试、类型检查或构建命令；全量测试只在定向范围无法覆盖风险，或发布/验收门禁要求时使用，并说明原因。
- 编译、预构建、项目启动等等待成本允许存在，但 item 必须记录实际命令和失败/耗时证据。
- 按目标项目真实测试入口核对 manifest 与实际选中的测试；零用例、漏选或无法解析都不能当作通过。Web Demo 可使用 `${CLAUDE_PLUGIN_ROOT}/scripts/check-test-runner-coverage.py <feature> --layer web-demo` 辅助静态检查，静态检查不替代运行证据。

## Failure Handling

- 状态文件缺失或损坏：终止并提示先运行 `/t-task`
- manifest 顺序无效、覆盖不完整或 item 文件缺失：终止并提示运行 `/t-task-check`
- item 执行失败：写回 `last_error`，停止当前 phase；再次运行时从该失败 item 恢复
