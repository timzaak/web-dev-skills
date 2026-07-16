# T-Tools 的 Skill 与 Subagent 设计思路

T-Tools 不是一组零散 prompt，而是一套面向工程交付的 AI 编程工作流。它把 Claude Code 从“临时问答工具”约束成“可执行、可恢复、可验收”的协作系统。

核心分工：

- `skills/`：流程编排，负责阶段推进、前置校验、状态更新和失败恢复。
- `agents/`：专业执行，按 dev / test / accept / diagnose 等角色拆分。
- `protocols/`：共享契约，定义状态结构、输出结构、评分规则和门禁标准。
- `guides/`：工程规范，承载后端、前端、Demo、产品和通用质量规则。
- `.ai/` 与 `docs/`：目标项目的运行时产物和长期业务事实。
- 人：表达真实意图、裁决取舍、指出细节偏好，并在 Preview、check 和 accept 中校准 AI 产物。

做需求、PRD 或技术预研前，可以先使用 [莫要偷懒](speech-template.md)。它让人按标题自然口述起步目标、用户故事、UI/UX、第三方对接、第三方库引入和结尾要求；AI 吞吐后再做可执行性、可行性、查漏补缺和待确认问题整理，并按需沉淀到 `.ai/future/[feature].md`。

## 四层结构

### Skills：流程控制器

Skill 是命令式工作流入口，不是“让模型自由发挥的一段提示词”。它通常会：

- 校验输入和前置条件。
- 读取上游文档与状态。
- 调度合适的 subagent。
- 写入标准化产物。
- 推进 `.ai/task/**/.state.json`。
- 在失败时给出可恢复路径。

主链路是：

```text
t-decision -> t-tech-research -> t-prd -> t-prd-check
-> t-design -> t-design-check
-> t-task -> t-task-check
-> t-run
-> t-demo-run -> t-demo-accept
-> t-prd-publish -> t-push -> t-release
```

并不是每个项目都需要完整跑完所有阶段。随着 AI 能力提升，`t-prd-check`、`t-design-check`、`t-task-check` 是可选质量检查：复杂、高风险或多人协作时用于阻止上游问题继续进入下游；简单低风险变更可以直接进入下一阶段。实现后的 accept 阶段仍负责验收收口。

### Agents：专业执行者

Subagent 按工程角色拆分，而不是让一个 agent 同时承担所有职责：

- `backend-dev` / `frontend-dev` / `miniapp-dev`：实现。
- `backend-test` / `frontend-test` / `miniapp-test`：测试。
- `backend-accept` / `frontend-accept` / `miniapp-accept`：默认只读验收并输出证据。
- `demo-dev` / `demo-accept` / `demo-diagnose`：维护、验收和诊断 Playwright Demo/E2E。
- `context-curator` / `structure-review` / `backend-consistency`：上下文、结构和实现一致性审计。
- `html-show`：把 Markdown 转成 HTML Preview。

这种拆分的重点是职责边界。失败时由流程 handoff 回到合适角色，而不是让一个 agent 在同一轮里实现、测试、验收和解释所有问题。

### Protocols：共享契约

`protocols/` 是跨 skill 和 agent 的单一真相源，定义：

- `.ai/task/[feature]/.state.json` 的状态结构。
- `phase -> slot -> item` 的执行顺序。
- agent 完成或失败时的结构化输出。
- 修复后必须返回的 `tests_to_run`。
- PRD Preview 的文件位置、内容模型和检查范围。
- PRD、设计、任务、Demo、t-dream 等检查的评分与阻塞规则。

共享规则优先改 protocol，不要复制到多个 skill 或 agent 文档里再手工同步。

### Guides：工程规范

`guides/` 承载具体工程实践：

- `backend/`：后端架构、开发、测试、验证、TDD 和质量门禁。
- `frontend/`：前端开发模式、测试策略、`data-testid` 和质量门禁。
- `miniapp/`：小程序开发、测试、验证和质量门禁。
- `demo/`：E2E、选择器、Page Object、诊断和常见失败处理。
- `product/`：产品文档和用户故事规范。
- `core/`：环境配置和通用质量标准。

Agent 文档只说明什么时候读 guide、如何执行、返回什么，不重复搬运 guide 里的规则。

## 关键设计

### PRD：先让人看懂 AI 的产品理解

`t-prd` 会先写 `.ai/prd` 与 `.ai/user-stories` 草稿。Markdown 是正式契约，也是人类审阅 AI 产品理解的入口。

有效顺序不是顺着 AI 的生成物读，而是先脱离生成物，按 [莫要偷懒](speech-template.md) 口述一版自己认可的需求：它解决什么痛点、哪个用户路径最重要、UI/UX 第一眼要看懂什么、异常状态如何反馈、第三方能力和第三方库是否真的适配。然后要求 AI 对照修正 PRD 和 user story。

`t-prd-check` 是可选质量检查，检查的不是格式本身，而是 AI 写下的产品理解、用户故事和正式文档之间是否一致。跳过它时，`t-design` 仍要自行混合验证草稿与已发布基线的关键冲突。实现、测试和 Demo 验收完成后，`t-prd-publish` 再把仍然成立的长期事实合并回 `docs/`。

### Tech Research：先把可行性问题说完整

`t-tech-research` 用来判断需求能不能做、需要什么依赖、会影响哪些现有模块，以及哪些风险会改变 PRD 或设计方向。口播模板不是技术预研报告的替代品，而是让人先把第三方 API 预期、技术栈兼容性、前后端 SDK、数据幂等、Webhook 乱序和权限边界讲清楚。

AI 收到口播后，应区分用户已确认的技术约束、需要查官方文档的事实、可从代码库验证的现状，以及必须追问用户的产品或技术决策。不能把口播里的猜测直接写成已确认结论。

### Design：由人明确 UX 取舍

`t-design` 不只是把 PRD 翻译成模块、接口和状态。只要功能涉及前端界面，人就需要从用户视角重新走一遍体验：

- 用户从哪里进入，第一眼应该理解什么。
- 每一步如何知道下一步该做什么。
- 加载、空状态、错误、权限不足、危险操作和成功反馈如何表现。
- 默认值、撤销、确认、保存和离开页面如何影响信任。
- 哪些交互是好的，哪些虽然能用但不符合预期。

AI 可以补流程和边界，但“好的 UX”是品味和取舍，不能默认交给模型按通用模板生成。

### Demo：独立验证用户故事闭环

Demo 阶段不是后端或前端测试的重复。它用 Playwright E2E 按用户故事验证真实路径，并把测试代码本身纳入验收。

- `demo-dev` 把用户故事转换成可执行 Demo 测试。
- `demo-accept` 检查测试覆盖、角色、场景、断言、执行结果和证据。
- `demo-diagnose` 在失败时判断责任属于 Demo 测试、前端实现还是后端实现，再 handoff 给对应 agent。

它验证的是交付可演示性和用户故事闭环，而不只是代码能不能编译。

## 执行模型

`t-task` 会把设计拆成标准任务目录：

```text
.ai/task/[feature]/
├── .state.json
├── backend/
├── frontend/
└── demo/
```

执行模型是 `phase -> slot -> item`：

- `phase`：通常是 `backend -> frontend -> demo`。
- `slot`：例如 `dev -> test -> accept`。
- `item`：真正可执行的最小任务文件。

`t-run` 只执行 item，不直接执行 `index.md`、`dev.md`、`test.md`、`accept.md` 这类 manifest。任意时刻最多一个 item 处于 `running`，这样牺牲一些并发速度，换来更小上下文、更清楚的失败定位和可恢复状态。

修复 agent 必须返回 `tests_to_run`，说明修复后应该补跑哪些后端、前端或 Demo 命令，避免“Demo 通过但底层回归失败”的风险被藏起来。

## 辅助治理

`t-dream` 是跨阶段的上下文整理和结构漂移审计工具。它默认只读检查 PRD、用户故事、设计、任务、代码、测试和 Demo 是否存在过期、重复、冲突、断链或实现不一致；需要写入 PRD 治理时才使用 `--govern-prd`。

`t-push` 是提交前的本地 CI 收口入口。它根据 diff 判断 backend / frontend / demo 影响范围，运行对应检查，通过后再提交和推送。正式版本发布仍由 `t-release` 约束，版本文件使用不带 `v` 的 semver，git tag 使用 `v` 前缀。

## 设计取舍

T-Tools 的核心取舍是：用更多结构减少不可控自由发挥。

它不会追求让 AI 一次性把所有事情做完，而是让需求、设计、任务、实现、测试、验收和发布都落到明确的文档、状态、契约和门禁里。模型仍然负责推理和实现，但必须沿着这些工程轨道前进。

一句话总结：T-Tools 用 skill 编排流程，用 subagent 分工执行，用 protocol 固化契约，用 guide 保持工程一致性，把 AI 编程变成可追踪、可恢复、可验收的长期工作流。
