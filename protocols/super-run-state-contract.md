# Super Run State And Execution Contract

`t-super-run` 是唯一调度者与状态写入者。planner 产出候选计划，角色 worker 串行执行，accept 独立验收。本文定义 super-run 的状态与调度；不读取、迁移或覆盖 `.ai/task/` 状态。

## Runtime Artifacts

```text
.ai/super-run/<feature>/
├── .state.json
├── .state.next.json
└── <phase>/r<revision>/
    ├── index.md
    ├── coverage.json
    ├── proposal.json
    ├── dev.md
    ├── dev/<ITEM-ID>-<name>.md
    ├── test.md                    # 需要独立测试资产时才生成
    ├── test/<ITEM-ID>-<name>.md
    ├── accept.md
    └── accept/<ITEM-ID>-<name>.md
```

- `.state.json` 是执行状态唯一真源；只有它指向的 revision 才生效。`.state.next.json` 是主会话准备的下一快照，不是恢复入口。
- revision 从 1 递增；重规划写新目录，校验通过后切换指针，保留旧目录供核查。未引用的候选目录不代表已规划或已执行。
- `index.md` 是该 revision 唯一阶段计划：范围与完成条件、Source Trace、Decision Trace、验证责任表、测试选择、共享文件/接口冲突表、Rulings 和恢复说明。无需再写 `<phase>.md`。
- slot manifest 包含 `## Items` 表：`id | title | agent | file`，行序是执行顺序唯一真源；file 使用目标项目根相对路径。state 不维护第二份 order。
- item 的稳定 ID、五章节、责任闭环与拆分上限引用 `${CLAUDE_PLUGIN_ROOT}/protocols/task-phase-execution.md` 的 Item Contract、Splitting Heuristics 和测试规则。头部使用 `id: ...`、`title: ...`、`agent: ...`；相关文档列在 Work，不能把 item 当成高于 PRD/设计/Active Decision 的事实源。
- 生效后 worker 只可追加当前 item 的 Handoff，不修改计划目标、Validation、manifest 或 state。计划变化交回主会话重规划。

## State Shape

```json
{
  "schema_version": 2,
  "sequence": 1,
  "feature": "sample-feature",
  "current_phase": "backend",
  "active_phases": ["backend", "frontend"],
  "phases": {
    "backend": {
      "status": "pending",
      "revision": 1,
      "index": ".ai/super-run/sample-feature/backend/r1/index.md",
      "design_fingerprint": "sha256:...",
      "slots": {
        "dev": {
          "status": "pending",
          "manifest": ".ai/super-run/sample-feature/backend/r1/dev.md",
          "items": {
            "BE-D01": {
              "status": "pending",
              "file": ".ai/super-run/sample-feature/backend/r1/dev/BE-D01-implement.md",
              "agent": "backend-dev",
              "attempt": 0,
              "failures_without_progress": 0,
              "evidence": []
            }
          }
        },
        "accept": {
          "status": "pending",
          "manifest": ".ai/super-run/sample-feature/backend/r1/accept.md",
          "items": {
            "BE-A01": {
              "status": "pending",
              "file": ".ai/super-run/sample-feature/backend/r1/accept/BE-A01-review.md",
              "agent": "backend-accept",
              "attempt": 0,
              "failures_without_progress": 0,
              "evidence": []
            }
          }
        }
      }
    }
  }
}
```

- `active_phases` 按 task-phase-execution 的 Phases 判定；`phases` 只包含已规划阶段，不为其他阶段自动建计划。支持八个 phase，slot 顺序与角色映射沿用 task-phase-execution；通常为 `<phase>-<slot>`。backend/test authoring 用 `backend-test`，runner 用 `general-purpose` 并保留 `test_item_type`。
- `sequence` 每次 checkpoint 加 1；state 不记录时间元数据。`revision` 表示计划版本，`attempt` 表示 item 派发次数，不能用它们相互替代。
- checkpoint 自动写入 `plan_fingerprint`，覆盖 manifest、coverage 和 item 的执行正文；Handoff 和 index 的进度记录不参与。执行正文变更必须创建新 revision。重规划记录 `replan_reason`；移除旧 item 时用 `retired_items: {ID: 原因}` 说明责任承接或来源变化，不得用删除规避未完成目标。
- item 必含示例中的六字段。失败/阻塞记录 `last_error`；重开/跳过记录 `reason`；派发后可记录 `worker_id`。`evidence` 是已落盘 Handoff、日志或报告路径，不存大段输出。accept 完成还必含 `acceptance_result`、`blocking_findings: 0` 和 `report_path`。
- 完成后清除过期 last_error；清零无进展计数时记录 `progress_evidence`，说明新增证据或已完成修复，不以“换模型重试”作为进展。
- `current_phase` 指向请求阶段；该阶段完成或全部 skipped 后置 null，不切换到其他 phase。

## Planning Contract

主会话在首次规划或设计指纹变化时先运行 `check-design.py --require-complete --json`。校验只在来源门禁执行，不在每个 item 之后重新验证设计中的 CREATE/MODIFY/DELETE 前置路径；这些路径可能已被本轮合法修改或删除。恢复时检查设计生成状态仍为 complete，重新计算文档指纹，并按证据协议复核相关输入。

planner 输入：feature、请求 phase、完整 `design_documents` 与指纹、相关需求/决策/预研入口、项目 AGENTS.md、现有有效 index/items/证据、重规划原因、候选 revision 目录。按 phase 读取分端设计：backend；frontend/web-demo；extension/extension-demo；flutter/flutter-demo；miniapp 读主文档相关章节。消费后端契约时补读 backend.md。按相关角色 Read Order 读取实际需要的规范和 guide，不能只凭角色名称推测。

planner 依次完成来源加载、active phases 判定、slot/item 规划、验证承接、冲突扫描；不调度其他 agent，不实现代码，不写 `.state.json`。读取 `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`，发现 `needs_user_answer` 时仅返回问题与已有诊断，不将未确认假设写入候选计划。超拆分上限沿用共享协议的用户授权门禁。

用以下只读命令取得覆盖清单：

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/check-super-run-plan.py" ".ai/super-run/<feature>/.state.next.json" --phase <phase> --inventory --json
```

inventory 不要求 state 文件存在；从该路径推导 feature。它复用设计解析器，列出主文档覆盖矩阵、跨端 Operation ID、全量文件影响行的 `source_id/kind/content`。`coverage.json` 是数组，每个 source_id 恰好一项：

```json
[
  {"source_id": "coverage:hash", "disposition": "implement", "items": ["BE-D01"], "reason": "本阶段实现此能力"},
  {"source_id": "impact:hash", "disposition": "other_phase", "items": [], "phase": "frontend", "reason": "客户端文件由 frontend 承接"}
]
```

`disposition` 为 `implement | consume | other_phase | not_applicable`。implement/consume 必须指向当前阶段实际 item；other_phase 必须指向另一个 active phase；not_applicable 必须给出依据。逐行分类用于检查当前阶段责任，不能为覆盖全量设计而生成其他阶段 item。脚本检查结构与完整性，主会话负责判断分类和 item 内容是否真正覆盖来源。

planner 将阶段状态对象写入候选目录的 `proposal.json`，新 item 为 pending；重规划沿用责任不变的稳定 ID，不自行继承 completed。返回：

```json
{
  "task_completion": {"status": "success", "summary": "阶段计划已写入候选目录"},
  "plan_result": {
    "phase": "backend", "revision": 1,
    "proposal_path": ".ai/super-run/sample-feature/backend/r1/proposal.json",
    "active_phases": ["backend", "frontend"],
    "needs_user_answer": [],
    "self_check": {"sources_classified": true, "conflicts_checked": true, "verification_assigned": true}
  }
}
```

`partial | failed`、问题非空或 self_check 未全通过均不得激活。主会话复核分类、共享文件/接口的生产消费关系、测试价值及真实命令；确认可保留的完成证据后合并 proposal 至 `.state.next.json`。对全部候选 Markdown 运行 `check-decision-closure.py`，按决策协议处理命中项。

## Checkpoint And Audit

主会话准备完整下一快照，再执行：

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/check-super-run-plan.py" ".ai/super-run/<feature>/.state.next.json" --phase <phase> --commit --expected-sequence <previous-sequence> --json
```

首次 previous-sequence 为 0。脚本在短时文件锁内读取旧 `.state.json`，校验 sequence、结构、计划文件、覆盖映射、状态迁移和聚合，随后原子替换正式 state；失败不覆盖旧状态。commit 总是检查 completed 的证据路径与验收字段。不带 `--commit` 为只读审计，可加 `--evidence` 检查证据；只读审计不验证历史迁移。

激活计划、新派发和新完成项必须通过当前设计指纹与覆盖校验。来源变动后，允许先以旧 revision 将未结束项转 failed/blocked/pending、重开失效证据；此类停止或失效 checkpoint 不要求新设计已经可用，但不能派发或完成工作。先持久化恢复现场，再校验新来源并重规划，避免旧 in_progress 与新设计门禁互相阻塞。

脚本只验证证据存在性，内容适用性按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md` 复核。state 写入失败重试一次，仍失败则停止。锁已存在时不得删除后强写；先确认没有并行控制器，确认遗留锁后才清除并从正式 state 恢复。同一 feature 只允许一个执行会话，短时写锁不隔离代码工作区。

旧 schema 或损坏 JSON：停止并保留文件，不按新结构猜测。用户选择升级时先备份旧 super-run 目录，再由 planner 按当前来源重建候选计划；逐项复核旧产物与证据后由主会话设置状态，不按旧 dev/test completed 批量推定所有新 item 完成。

## Status And Recovery

super-run 独立使用 `pending | in_progress | failed | blocked | completed | skipped`，不继承标准 task 的 generated 迁移。

| 原状态 | 允许后继 | 条件 |
| --- | --- | --- |
| pending | in_progress / blocked / skipped | 派发前 attempt 加 1；blocked 写 last_error；skipped 写不适用依据 |
| in_progress | completed / failed / blocked / pending | 证据通过才完成；恢复至 pending 必须记录核查与未完成动作 |
| failed | in_progress / blocked / pending | 重试 attempt 加 1；重新规划或修复归位可 pending 并写 reason |
| blocked | pending | 阻塞条件已解除并写 reason，不自动升级模型反复尝试 |
| completed / skipped | pending | 证据失效、accept 拒绝或来源变化，写 reason |

同状态 checkpoint 允许追加 evidence/worker_id，不产生新 attempt。聚合 slot，再聚合 phase：任一 blocked → blocked；否则任一 failed → failed；否则任一 in_progress → in_progress；否则任一 pending → pending；全部 skipped → skipped；其余全为 completed/skipped → completed。空 slot 非法。

恢复先检查顺序中的 `in_progress`：worker 仍运行则等待；可恢复则继续同一 attempt；worker 丢失时核对工作区、Handoff 和副作用，记录缺失动作后转 pending，再派新 attempt。已产出有效完成结果时可核查后完成，不能仅凭文件存在判成功。accept 中断重新派发，旧报告不能自动代表本轮验收。未经核对不得重复迁移、外部写入或其他有副作用动作。

按 manifest 找第一个非 completed/skipped item；in_progress/blocked 先恢复或停止，不能越过。新 dispatch 必须在上一 worker 已结束后进行；超时不等于进程已退出。返回结果必须匹配 phase/revision/item/attempt；过期结果只保留诊断，不推进状态。

设计指纹变化时停止派发，重读来源并重派 planner；对受影响 item、验收和已完成的下游验证重开，保留无关完成证据。不自动执行其他 phase。PRD/Decision/测试/配置/运行环境变化也按证据协议判断失效，设计指纹不是全部证据的替代品。

## Dispatch Contract

按 `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md` 注入角色规范。必要上下文：`feature/phase/slot/item_id/agent/revision/attempt`、item 全文与路径、阶段 index（含验证责任表）、slot manifest、相关来源、已完成上游的必要 Handoff、失败证据与本轮补测范围。每次 prompt 明确 `dispatch_owner: controller`，禁止 worker 调用 Agent/Task/Skill 再派发、通过 CLI 启动其他 agent，或写 state；内置 general-purpose runner 同样适用。运行时支持工具限制时移除调度工具，不能依赖角色正文注入来修改真实工具权限。

角色 worker 按 `${CLAUDE_PLUGIN_ROOT}/protocols/agent-task-output-contract.md` 返回 `task_completion` 和 Controller Dispatch 扩展。先在 Handoff/现有报告记录命令、cwd、范围、退出码、预期/实际结果、版本与环境、日志入口，再返回短摘要和 evidence_refs。主会话核对当前 Validation 和原始证据，不能要求 worker 只返回一行却由主会话补造执行记录。

| 返回信息 | 主会话动作 |
| --- | --- |
| success，无阻塞关注点 | 验证结果和证据后 completed |
| success，含 concerns | 正确性/范围/必要验证问题重新归类为未完成；非阻塞维护建议写 Rulings |
| partial，context_requests 非空 | 可查事实由主会话补充后重派；用户决策按 Decision Exposure Gate 阻塞 |
| failed，repair_request 非空 | 先 failed，主会话按责任派发修复，再重跑受影响验证 |
| partial/failed，blocked_by 非空 | 写 blocked、停止依赖该项的执行，报告解除条件 |
| 输出缺失/格式错误/无解释的 partial | failed 并附原始结果；要求补齐，不推断成功 |

用户决策门禁优先于自动修复。Rulings 只记录 D2 工程取舍、证据和影响；跨阶段或高反转成本的决定按 decision-continuity 的 Entry Gate 写账本，不能据此改变业务规则、风险接受或验收目标。

## Repair And Acceptance

- 测试 worker 不接管生产修复。backend/test runner 遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/backend-test-execution.md` 的 controller 模式，向主会话返回 repair_request；其他 test/Demo worker 同理。测试资产问题交测试拥有者，生产缺陷交相应 dev。
- 同阶段已有对应 dev item 时重开该 item 及受影响的已完成验证/accept，先持久化再派发；原测试 item 保留失败证据，修复后转 pending 重测。Demo 发现同一已授权功能的客户端/后端缺陷时，可重规划当前 phase，在 dev slot 增加由对应 dev 负责的修复 item，记录 `repair_for`（原失败 item ID）、`reason` 和 `repair_evidence`；manifest 将修复放在原失败 item 前。这类 item 的 agent 可为相关端 dev；只修有证据的缺陷，不顺带执行其他 phase 的计划。受影响的上游验收证据按规则失效重开，报告其恢复入口。新增业务范围或未授权行为变更仍先触发决策门禁。
- Demo 归因不明时串行派发对应 `web-demo-diagnose | extension-demo-diagnose | flutter-demo-diagnose`，读取 `${CLAUDE_PLUGIN_ROOT}/protocols/diagnostic-report-contract.md`。非 Demo 由当前角色提供最小复现与证据，不套用 Demo diagnose。
- backend runner 覆盖检查显式传当前 runner 的 `--runner-file` 给目标项目 `scripts/check-test-runner-coverage.py`，或用协议允许的 nextest list 等价核查，避免默认发现 `.ai/task/`。测试命令仍使用目标项目脚本。
- extension 现场观察读取 `${CLAUDE_PLUGIN_ROOT}/protocols/extension-acceptance-contract.md` 和 `${CLAUDE_PLUGIN_ROOT}/guides/extension/live-browser.md`；extension-demo 读取 `${CLAUDE_PLUGIN_ROOT}/guides/extension/demo-testing.md`。设备/环境选择写 index；Flutter Demo 必须记录实际 Android device，不能猜测。
- 每个 item 持久化 failures_without_progress 和 last_error；失败签名相同、没有新证据时累计，实质进展后才能清零，重派/换模型/会话恢复不清零。前两次可修复并重试；第三次仍无进展转 blocked。仅在上限内、有具体原因且运行时支持时调整模型或补诊断；planner 生成、上下文补充和 accept 无效返回同样不得无界重试，在 index 记录计数。
- accept 按原角色边界只读检查代码/测试，可写独立验收报告；读取全阶段范围、dev/test evidence、上游待验证场景和 verification-evidence-contract。只允许 `ACCEPTED` 或无 P0/P1 的 `ACCEPTED_WITH_IMPROVEMENTS` 完成；REJECTED 重开对应 dev/test 及受影响下游，accept 转 pending，修复重测后重新验收。主会话不得代出、改写或降级 verdict。
- accept 不能单独 skipped 来绕过门禁；只有整个 phase 有不适用依据且全部 item skipped 时允许。阶段完成与 feature 业务交付的区别按 verification-evidence-contract。
