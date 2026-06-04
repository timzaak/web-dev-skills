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
- `/t-tools:t-html-show`
- `/t-tools:t-prd-check`
- `/t-tools:t-design`
- `/t-tools:t-design-check`
- `/t-tools:t-task`
- `/t-tools:t-task-check`
- `/t-tools:t-run`
- `/t-tools:t-demo-run`
- `/t-tools:t-demo-accept`
- `/t-tools:t-dream`
- `/t-tools:t-push`

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

- `backend-dev`：Java Spring Boot 后端功能实现。
- `backend-test`：后端场景测试、集成测试、验收测试。
- `backend-accept`：后端只读验收。
- `frontend-dev`：React 前端实现。
- `frontend-test`：Vitest、Testing Library、MSW 测试。
- `frontend-accept`：前端只读验收。
- `html-show`：把 Markdown 文档转成 HTML Preview，用于人类审阅。PRD 和任意文档均适用。
- `demo-dev`：基于用户故事维护独立的 Playwright Demo/E2E 测试。
- `demo-accept`：验收 Demo 测试与用户故事、执行结果和测试质量是否一致。
- `backend-consistency`：后端模块级深度一致性检查，按 API 能力边界、数据模型、校验规则、权限和业务逻辑五个维度对比 PRD 与实现。

这种拆分的重点是职责边界。开发 agent 可以修改代码；测试 agent 专注测试；accept agent 默认只读并输出证据报告。失败时通过 handoff 回到合适角色，而不是让一个 agent 同时承担所有职责。

### Protocols：共享契约

`protocols/` 是跨 skill 和 agent 的单一真相源，定义：

- `.ai/task/[feature]/.state.json` 的状态结构。
- `phase -> slot -> item` 的执行顺序。
- agent 完成或失败时的结构化输出。
- 修复后需要返回的 `tests_to_run` 补测集合。
- PRD HTML Preview 的文件位置、内容模型、技术边界和检查范围。
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
-> Dream Check（描述准确性排查，可随时单独执行）
```

这条链路把 AI 编程拆成产品、设计、任务规划、实现、测试、验收、Demo 交付多个阶段。每个阶段都有输入契约、输出契约和质量门禁。

关键点是不要跳过 check / accept。这个项目的价值不只是生成内容，而是在每个阶段收口，避免把上游问题带到下游。

## t-prd 的设计思路：让 AI 产物先被人看懂

`/t-tools:t-prd` 的核心变化不是“多生成一个 HTML 文件”，而是改变人类审阅 AI 产物的方式。

传统 PRD 流程里，AI 很容易产出一千行 Markdown。它对模型来说结构清楚，但对人类来说阅读成本很高：要在长文里找目标、范围、流程、状态、权限、异常和验收标准，还要自己判断这些内容是否互相矛盾。人在这个阶段看不懂或看不完，后面的设计、任务和实现就会沿着错误理解继续放大。

HTML Preview 的设计目的，是把 AI 对需求的理解转换成更容易被人快速浏览、质疑和修正的形态。人不需要先完整读完 Markdown，先看 Preview 就能知道：

- AI 认为这个功能要解决什么问题。
- 用户会经过哪些关键路径。
- 哪些状态、边界、异常和权限被考虑到了。
- 哪些地方仍然只是待确认假设。
- 这个需求进入设计阶段前是否已经足够清楚。

因此，`/t-tools:t-prd` 更像是一个“产品理解可视化”阶段。Markdown 仍然是正式契约，但 Preview 是人类审阅契约的入口。它把长文档里的产品语义变成可扫描、可讨论、可反馈的界面，让人类更早发现 AI 的误解，而不是等到技术设计或代码实现后才发现方向偏了。

这个思路也改变了 `/t-tools:t-prd-check` 的意义。PRD Check 不只是检查文档格式，而是确认”AI 写下的产品理解”和”人类通过 Preview 看到的产品理解”是否一致。只有这两者对齐，后续 `/t-tools:t-design` 才有稳定输入。

`/t-html-show` 已从 `/t-prd` 中提取为独立 skill，并泛化为支持任意 Markdown 文档的可视化。`/t-prd` 在流程中会自动触发它，但也可以单独调用。Preview 输出到 `.ai/preview/` 下，不进入版本控制。

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

- 读取 `.state.json`。
- 校验 phase、slot、item 和 DAG。
- 找到第一个依赖已满足的 `pending` 或 `failed` item。
- 标记为 `running`。
- 调度对应 subagent。
- 根据结果写回 `completed` 或 `failed`。
- 聚合 slot 和 phase 状态。

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

## 描述准确性排查：t-dream

`/t-tools:t-dream` 不是阶段门禁，而是一个跨阶段的描述准确性验证工具。它的核心问题是：PRD、用户故事、Demo 测试注释和相关产品描述是否准确反映实现事实。

与 `/t-tools:t-prd-check` 等阶段检查不同，t-dream 不检查文档格式或结构完整性，而是直接对比文档声明和代码实现：

- PRD 声明的能力边界是否被代码支撑。
- 用户故事的验收描述是否与实际行为一致。
- Demo 测试注释和断言是否准确反映覆盖事实。
- 后端 API、数据模型、校验规则、权限和业务逻辑是否与 PRD 描述对齐。

### 并行验证模型

t-dream 采用类似 code review 的两阶段机制：

1. **并行发现**：多个 `general_agent` 从不同维度独立发现候选差异——PRD 描述准确性、用户故事与验收描述、Demo 描述与覆盖事实、后端/前端实现一致性。
2. **统一验证**：主线程或专门验证 subagent 根据真实文件证据过滤误报、去重、定级。

这种设计确保各维度独立判断，避免某个维度的结论污染其他维度。所有候选问题必须经过验证，置信度不低于 80 的 P0/P1 才进入最终报告。

### 使用场景

t-dream 适合在以下时机使用：

- 实现阶段完成后，验证文档与实现对齐。
- Demo 交付前，确认描述准确性。
- 长期迭代中，定期排查文档与实现的漂移。
- 不替代任何阶段门禁，而是作为补充验证。

`--deep` 模式额外调用 `backend-consistency` agent 做后端模块级深度检查，覆盖 API 能力边界、数据模型、验证规则、权限和业务逻辑五个维度。`--backend-only` 模式只聚焦 PRD 与后端实现一致性，适合后端迭代频繁的场景。

## 提交前的本地 CI 收口

`/t-tools:t-push` 是日常提交入口，不替代完整发布流程。它根据 git diff 判断变更范围：

- `backend/**` 触发 Backend CI。
- `frontend/**` 触发 Frontend CI。
- `demo/**` 触发 Demo CI。
- 仅文档、脚本或配置变更时跳过业务区域 CI，直接进入提交确认。

所有受影响检查通过后，它会 `git add -A`，基于暂存 diff 生成符合项目惯例的 commit message，经用户确认后执行 `git commit` 和 `git push`。如果任一 CI 失败，流程停止，不提交、不推送。

正式版本发布仍由 `/t-tools:t-release [版本号]` 约束；版本文件使用不带 `v` 的 semver，git tag 使用 `v` 前缀。

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
