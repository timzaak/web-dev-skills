# T-Tools 的 Skill 与 Subagent 设计思路

T-Tools 不是一组零散 prompt，而是一套面向工程交付的 AI 编程工作流。它的目标是把 Claude Code 从“临时问答工具”约束成“可执行、可恢复、可验收”的协作系统。

核心思路可以概括为：

- `skills/` 负责流程编排。
- `agents/` 负责专业执行。
- `protocols/` 负责共享契约。
- `guides/` 负责工程规范。
- `.ai/` 与 `docs/` 负责目标项目的运行时产物和业务事实。

## 四层结构

### Skills：流程控制器

Skill 是命令式工作流入口，例如：

- `/t-tools:t-prd`
- `/t-tools:t-design`
- `/t-tools:t-task`
- `/t-tools:t-run`
- `/t-tools:t-demo-run`
- `/t-tools:t-demo-accept`

Skill 的职责不是“写一段提示词让模型自由发挥”，而是控制阶段推进：

- 校验输入和前置条件。
- 读取上游文档与状态。
- 调度合适的 subagent。
- 写入标准化产物。
- 更新任务状态。
- 在失败时给出可恢复路径。

因此，skill 更接近一个轻量工作流引擎。

### Agents：专业执行者

Subagent 按工程角色拆分，例如：

- `backend-dev`：Rust 后端功能实现。
- `backend-test`：后端场景测试、集成测试、验收测试。
- `backend-accept`：后端只读验收。
- `frontend-dev`：React 前端实现。
- `frontend-test`：Vitest、Testing Library、MSW 测试。
- `frontend-accept`：前端只读验收。
- `demo-dev`：基于用户故事维护独立的 Playwright Demo/E2E 测试。
- `demo-accept`：验收 Demo 测试与用户故事、执行结果和测试质量是否一致。

这种拆分的重点是职责边界。开发 agent 可以修改代码；测试 agent 专注测试；accept agent 默认只读并输出证据报告。失败时通过 handoff 回到合适角色，而不是让一个 agent 同时承担所有职责。

### Protocols：共享契约

`protocols/` 是跨 skill 和 agent 的单一真相源，定义：

- `.ai/task/[feature]/.state.json` 的状态结构。
- `phase -> slot -> item` 的执行顺序。
- agent 完成或失败时的结构化输出。
- 修复后需要返回的 `tests_to_run` 补测集合。
- PRD、设计、任务检查的评分与阻塞规则。

这样可以避免每个 skill 或 agent 重复定义一套字段、状态机和质量标准。更新共享规则时，优先改 protocol，而不是在多个 agent 文档里复制同步。

### Guides：工程规范

`guides/` 承载具体工程规范，例如：

- 后端架构、测试、验证、质量门禁。
- 前端开发模式、测试策略、`data-testid` 规范。
- Demo 测试、选择器、Page Object、常见失败处理。
- 产品文档和用户故事规范。

Agent 文档只说明“什么时候读这些 guide、如何执行、返回什么”，不把 guide 里的规则再写一遍。这样可以减少规则漂移。

## 从 PRD 到交付的流程

T-Tools 推荐的完整链路是：

```text
PRD
-> PRD Check
-> Design
-> Design Check
-> Task
-> Task Check
-> Run
-> Backend Finalize
-> Demo Run
-> Demo Accept
```

这条链路把 AI 编程拆成产品、设计、任务规划、实现、测试、验收、Demo 交付多个阶段。每个阶段都有输入契约、输出契约和质量门禁。

关键点是不要跳过 check / accept。这个项目的价值不只是生成内容，而是在每个阶段收口，避免把上游问题带到下游。

## Demo 的独立质量验证

Demo 阶段不是后端测试或前端测试的重复，而是一条独立的质量验证线。它以用户故事为依据，用 Playwright E2E 测试验证真实用户路径能否跑通，并把测试代码本身也纳入验收。

`demo-dev` 的重点是把用户故事转成可执行的演示测试：

- 从用户故事识别角色、场景和验收目标。
- 对照前端实现和共享选择器维护稳定测试。
- 优先验证用户可观察行为，而不是内部实现细节。
- 失败时判断问题属于 Demo 测试、前端实现还是后端实现，再 handoff 给对应 agent。

`demo-accept` 的重点是验证 Demo 质量：

- 测试是否覆盖了对应用户故事。
- 角色、场景、断言是否与验收目标一致。
- 测试是否能编译和执行。
- 选择器、等待、Page Object、测试数据构造是否符合规范。
- 每条结论是否有测试文件、日志或命令输出作为证据。

因此，Demo 阶段承担的是“交付可演示性”和“用户故事闭环”的质量门禁。它验证的不只是代码能不能编译、接口能不能返回，还包括用户从入口到结果的完整体验是否符合产品意图。

## 核心执行模型：phase -> slot -> item

`/t-tools:t-task` 会把设计文档拆成标准任务目录：

```text
.ai/task/[feature]/
├── .state.json
├── backend/
├── frontend/
└── demo/
```

执行模型分三层：

- `phase`：`backend -> frontend -> demo`
- `slot`：例如 `dev -> test -> accept`
- `item`：真正可执行的最小任务文件

`/t-tools:t-run` 只执行 item，不直接执行 `index.md`、`dev.md`、`test.md`、`accept.md` 这类 manifest。manifest 负责导航、依赖和摘要；item 才包含具体步骤、输入、预期文件、验证命令和完成标准。

这种设计让任务可以被拆小、排序、重试和审计。

## 为什么串行调度 item

`/t-tools:t-run` 任意时刻最多只允许一个 item 处于 `running`。它会：

1. 读取 `.state.json`。
2. 校验 phase、slot、item 和 DAG。
3. 找到第一个依赖已满足的 `pending` 或 `failed` item。
4. 标记为 `running`。
5. 调度对应 subagent。
6. 根据结果写回 `completed` 或 `failed`。
7. 聚合 slot 和 phase 状态。

这套机制牺牲了一些并发速度，但换来更强的可控性：

- 上下文更小。
- 失败更容易定位。
- 状态更容易恢复。
- 下游 item 不会在上游失败时继续乱跑。
- 每个 handoff 都能被记录。

对于长期项目，这种确定性比一次性并发更重要。

## 质量门禁与恢复机制

T-Tools 把质量控制做成显式流程：

- `/t-tools:t-prd-check` 检查 PRD 与 user story。
- `/t-tools:t-design-check` 检查技术设计。
- `/t-tools:t-task-check` 检查任务拆分、DAG、item 可执行性。
- `backend-accept`、`frontend-accept`、`demo-accept` 输出只读验收报告。
- `/t-tools:t-demo-run` 失败时先诊断，再分发给 `demo-dev`、`frontend-dev` 或 `backend-dev` 修复。

修复 agent 必须返回 `tests_to_run`，说明修复后应该补测哪些后端、前端或 Demo 命令。这样 Demo 通过但底层回归失败的风险会被显式暴露。

## 设计取舍

这套设计的核心取舍是：用更多结构换更少自由发挥。

它不会追求让 AI 一次性“把所有事情做完”，而是强调：

- 需求语义先落到 `docs/`。
- 技术方案先落到 `.ai/design/`。
- 执行计划先落到 `.ai/task/`。
- 每个 item 有明确输入、步骤、边界和验证。
- 每个 agent 有明确职责和输出契约。
- 每个阶段都有检查或验收。

因此，T-Tools 更像是给 AI 编程建立工程轨道：模型仍然负责推理和实现，但它必须沿着文档、状态、契约和门禁前进。

## 一句话总结

T-Tools 的设计重点不是让模型更自由，而是让模型更可控：用 skill 编排流程，用 subagent 分工执行，用 protocol 固化契约，用 guide 保持工程一致性，最终把 AI 编程变成可追踪、可恢复、可验收的长期工作流。
