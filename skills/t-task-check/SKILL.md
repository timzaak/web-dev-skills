---
name: t-task-check
description: Validate task plan executability and consistency with a 100-point score and P0/P1/P2 fix list.
argument-hint: "[任务名称] [--phase <backend|frontend|miniapp|demo>]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Task
  - Write
  - Agent
---

# 任务规划质量检查

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`
需求来源边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`

## 目标
- 评估任务文档可执行性与一致性。
- 验证 `phase -> slot -> item` 结构。
- 给出可复查的 100 分量化结果。
- 输出 P0/P1/P2 修复清单。
- 必须按当前阶段调度对应 sub agent 做专业校验，再由主流程聚合结论。

评分、阻塞条件、报告要求、跨轮收敛和 agent 评审边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/task-check-rubric.md`

## 事实优先级（强制）
证据优先级和争议处理统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/task-check-rubric.md`

## 使用方式
```bash
/t-task-check [feature] [--phase <backend|frontend|miniapp|demo>]
```

| 参数 | 说明 |
|---|---|
| `[feature]` | 功能名（必填） |
| `--phase <phase>` | 指定阶段检查；未指定时检查 `.state.json` 当前阶段 |

## 输入范围
- 设计文档：`.ai/design/[feature].md`
- 需求来源：`.ai/user-stories/**/*.md`、`docs/user-stories/**/*.md`、`.ai/prd/**/*.md`、`docs/prd/**/*.md`、`.ai/tech-research/**/*.md`（按设计文档引用读取）
- 状态文件：`.ai/task/[feature]/.state.json`
- 阶段目录：`.ai/task/[feature]/[phase]/`
- 阶段索引：`index.md`
- slot manifest：
  - backend/frontend/miniapp: `dev.md`、`test.md`、`accept.md`
  - demo: `dev.md`、`accept.md`
- item 文件：
  - backend/frontend/miniapp: `dev/*.md`、`test/*.md`、`accept/*.md`
  - demo: `dev/*.md`、`accept/*.md`
- backend 额外文件：`finalize.md`

## Schema 校验
`.state.json` 的 schema 要求统一参考：

- `${CLAUDE_PLUGIN_ROOT}/protocols/task-state-contract.md`
- `${CLAUDE_PLUGIN_ROOT}/protocols/task-check-rubric.md`

任一项缺失或非法即返回 `TASK_SCHEMA_INVALID`

## 执行流程
- 校验设计文档是否存在。
- 读取 `.state.json` 并验证 schema。
- 若指定 `--phase`，仅检查该阶段；否则检查当前阶段。指定阶段必须存在于 `.state.json.phases` 的 active phases 中。
- 校验阶段依赖正确性。
- 读取阶段目录下的 `index.md`、slot manifest，并建立 item 文件清单。
- 校验 item 时按以下顺序读取：
   - 从 `.state.json`、slot manifest 和 item 文件头/关键字段抽取 `id/title/agent/scope/expected_files/validation/depends_on/test_item_type/uses_skill/handoff_summary/completion_criteria`。
   - 用抽取结果完成 item 存在性、路径一致性、manifest 覆盖、DAG、agent/slot 匹配和 backend test authoring/集中 runner 覆盖校验。
   - 发现字段缺失、DAG/manifest 不一致、拆分阈值可疑、设计一致性可疑或需要为 P0/P1 补证时，读取对应 item 全文。
   - 大型 phase 先用 `Grep`、路径清单或 manifest 定位目标 item，再读取命中的 item 文件。
- 按 `${CLAUDE_PLUGIN_ROOT}/protocols/task-check-rubric.md` 校验 item DAG 与 manifest 覆盖关系。
- 验证 item 文件结构与内容：
   - 必须包含 `id/title/agent/scope/inputs/steps/expected_files/validation/depends_on/handoff_summary/completion_criteria`
   - backend/test item 必须声明 `test_item_type: authoring|runner`
   - backend/test runner item 必须声明 `uses_skill: skills/t-backend-test-run/SKILL.md`
   - backend/test 必须有 runner item 覆盖全部相关 authoring item，且 runner 依赖这些 authoring item
   - backend/accept item 必须依赖 runner item，不得只依赖 authoring item
   - frontend/test、miniapp/test 和 demo/dev 涉及测试代码 authoring 时，必须有集中定向执行 item 依赖全部相关测试 authoring item
   - 集中测试执行 item 必须包含 `Expected Test Manifest`，逐项列出测试文件、测试函数/用例标题、来源 authoring item 和 runner 命令
   - 测试执行 item 必须从覆盖来源推导定向命令；如升级全量，必须说明定向范围不足或门禁要求
   - 对 backend/frontend/miniapp/demo 的集中测试执行 item，优先运行 `uv run scripts/check-test-runner-coverage.py [feature] --layer [layer]` 做覆盖校验；backend 动态校验失败应记 P1 或 P0（取决于是否导致新增测试无法执行），frontend/miniapp/demo 静态校验失败至少记 P1
   - 后端测试命令必须使用目标项目内脚本入口 `uv run scripts/backend-test.py -- [filter]`；即使没有 filter，也必须写为 `uv run scripts/backend-test.py --`。不得写成 `${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py` 或省略 `--`。若测试 item 使用 `cargo run`、裸 `cargo test`、插件根路径或省略 `--` 的后端测试命令，记 P1，并改为统一入口。
   - 不得把完整 slot 内容塞进一个 item
   - 超过拆分阈值，或职责、验证、恢复边界可疑时，必须有合理说明，否则记 P1
   - scope 中包含两个可独立交付、独立验证的主交付物时，必须拆分，否则记 P1
   - 单个 HTTP/API item 覆盖超过 7 个 endpoint，或混合不同资源域、读写操作、状态操作、配置类接口时，必须拆分，否则记 P1
   - 单个 demo item 同时创建复用 helper 并覆盖多个完整用户故事或多个业务状态流时，必须拆分，否则记 P1
- 核对设计文档与任务文档的一致性；纯技术方案任务可只追溯设计文档中的技术预研来源，不得因缺少 PRD/用户故事扣 P0。
- 若任务或设计引用 `.ai/user-stories`，确认其为 draft 候选来源且路径存在；不得要求先发布到 `docs/user-stories` 才能进入 `/t-run`。
- 通过 `Agent` tool 调度当前阶段对应 subagent 做专业校验。每个 subagent 独立启动，传入 prompt 包含：该 agent/slot 相关 item 的文件路径、关键字段摘要、必要 item 全文或片段、设计文档相关节、验证范围、`${CLAUDE_PLUGIN_ROOT}/protocols/task-check-rubric.md` 中的 agent 评审边界、输出格式要求（score/findings/fixes/summary）。可并行调度同阶段多个 subagent。
   - 不得默认把当前 phase 的全部 item 全文传给每个 subagent。
   - dev agent 默认只接收 dev item 与直接影响实现的跨 slot 摘要。
   - test agent 默认只接收 test item、相关 dev handoff/expected_files 摘要和集中定向测试执行闭环约束。
   - accept agent 默认只接收 accept item、直接依赖 runner/dev handoff 摘要和验收闭环约束。
   - demo 阶段按 dev/accept slot 同样做最小分发。
   - backend: subagent_type="backend-dev", "backend-test", "backend-accept"
   - frontend: subagent_type="frontend-dev", "frontend-test", "frontend-accept"
   - miniapp: subagent_type="miniapp-dev", "miniapp-test", "miniapp-accept"
   - demo: subagent_type="demo-dev", "demo-accept"
- 聚合 agent 结果并进行主流程复核：同类问题合并，P0/P1 必须补齐任务文档证据和真源证据。
- 按评分体系生成评分与问题清单。
- 执行报告一致性自检。
- 写入报告：`.ai/quality/task-check-[feature]-[YYYYMMDD-HHMMSS].md`。

## Agent Review Contract
调度方式：通过 `Agent(subagent_type="<agent-name>")` 启动。主流程收集所有 subagent 返回后进行交叉验证（证据优先级：仓库证据 > subagent 发现 > 假设）。

当前阶段 agent 输出字段和主流程补证要求统一参考：

- `${CLAUDE_PLUGIN_ROOT}/protocols/task-check-rubric.md`

agent finding 不直接作为最终裁决；主流程必须按 rubric 完成证据复核和同类合并。

## 评分与问题分级
评分体系、P0/P1/P2 定义和报告结构统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/task-check-rubric.md`

## 错误处理
| 错误码 | 触发条件 | 用户可见提示 | 恢复动作 |
|---|---|---|---|
| `DESIGN_DOC_MISSING` | 设计文档不存在 | 未找到设计文档 | 先运行 `/t-design [feature]` |
| `STATE_FILE_MISSING` | 任务目录或 `.state.json` 缺失 | 状态文件不存在 | 运行 `/t-task [feature] --phase backend` 重建 |
| `STATE_JSON_INVALID` | `.state.json` 格式错误 | 状态文件解析失败 | 修复 JSON 后重试；或重建任务目录 |
| `TASK_SCHEMA_INVALID` | 缺少 `phase/phases/tasks/status/manifest/items` 字段 | 任务状态结构不完整 | 运行 `/t-task [feature] --phase [phase]` 重建 |
| `PHASE_INVALID` | `--phase` 不是 `backend|frontend|miniapp|demo` | 非法阶段，仅支持 backend/frontend/miniapp/demo | 使用合法参数后重试 |
| `PHASE_NOT_ACTIVE` | `--phase` 不在当前任务 active phases 中 | 当前项目未启用该阶段 | 使用 `.state.json.phases` 中存在的阶段，或重新运行 `/t-task` 生成该阶段 |
| `PHASE_DIR_MISSING` | 阶段目录不存在 | 找不到阶段目录 | 运行 `/t-task [feature] --phase [phase]` 生成 |
| `ITEM_DAG_INVALID` | item 依赖缺失或成环 | 子任务依赖非法 | 修复或重新生成该阶段 |
| `REPORT_INCONSISTENT` | 报告中的严重度、总分、准入结论或问题数量互相冲突 | 报告自检失败 | 重新聚合证据并重生成报告 |

信息提示（不阻断）：
- `PHASE_NOT_CURRENT`：指定 `--phase` 非当前阶段时提示"当前阶段为 [state.phase]，继续检查指定阶段"。
- `PHASE_CHECK_AGENT_SET`：展示本次实际调用的 phase agent 集合，便于复查。

## 示例
```bash
/t-task-check sample-feature --phase backend
```

输出：
```text
总分: 92/100 (优秀，可进入实施)

状态文件验证: 通过
Item DAG 验证: 通过

状态文件结构: 15/15
文档完整性: 14/15
Item 可执行性: 18/20
内容一致性: 19/20
依赖与恢复: 15/15
文档规范: 8/10
代码示例质量: 3/5

Agent 集合: backend-dev, backend-test, backend-accept
问题分类摘要: confirmed=2, disputed=0, assumption=0

P1 问题:
- BE-D03 超过拆分阈值，建议拆为 repository trait 与 repository implementation 两个 item

下一步: /t-run sample-feature --phase backend
```

## 质量门禁
硬性门禁统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/task-check-rubric.md`
