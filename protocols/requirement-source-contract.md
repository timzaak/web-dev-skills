# Requirement Source Contract

本协议定义 PRD、用户故事和技术预研在各阶段的读取、引用和写入边界。所有 pre-publish 阶段必须同时理解正式来源与候选来源，避免把未发布草稿误写成长期权威事实。

## Source Classes

### Published Sources

长期权威来源，位于目标项目 `docs/`：

- `docs/prd/**/*.md`
- `docs/user-stories/**/*.md`

这些文件表达已发布、需要长期维护的产品事实。只有明确负责发布或治理的阶段可以写入。

### Draft Sources

候选需求来源，位于目标项目 `.ai/`：

- `.ai/prd/**/*.md`
- `.ai/user-stories/**/*.md`
- `.ai/tech-research/**/*.md`
- `.ai/decision/**/*.md`
- `.ai/decision-log/**/*.md`

这些文件表达当前工作流中的候选需求、决策和技术事实。它们可供设计、任务、实现、测试和 Demo 阶段追溯，但不是长期权威源。

`.ai/decision-log/**/*.md` 是当前 feature 跨阶段决策连续性的结构化来源。其记录规则、稳定 ID 和用户决策暴露门禁统一参考 `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`。

## Read Rules

- Pre-publish 阶段必须同时读取相关 published sources 和 draft sources。
- Pre-publish 阶段在提问或作出新决策前必须读取相关 `.ai/decision-log/<feature>.md`；已解决问题不得重复询问。
- 同一 feature 存在 `.ai/prd` 或 `.ai/user-stories` 时，它们表达本轮候选变更意图；`docs/prd` 和 `docs/user-stories` 表达已发布基线。
- `/t-tech-research` 在 PRD 草稿后运行时必须读取相关 `.ai/prd`、`.ai/user-stories` 与 published baseline，将其作为产品边界输入；技术结论不得静默改写产品语义。
- 设计、任务、实现、测试、Demo 和检查阶段可以引用 draft user story，但必须保留来源路径，不能把它改写成已发布事实。
- 纯技术方案可以只引用 `.ai/tech-research/**/*.md`，但必须声明不涉及业务逻辑、产品规则、用户可见流程或验收目标变动。
- Draft source 与 published source 在目标、范围、角色、权限、业务状态或验收目标上冲突时，停止并报告冲突；不要自动合并或平均折中。
- 技术预研结论会改变范围、业务规则、用户流程或验收目标时，必须通过 `/t-prd` 更新候选 PRD / user story；进入 `/t-design` 前不得保留未解释冲突。

## Write Rules

- `/t-prd` 只写 `.ai/prd/**/*.md` 和 `.ai/user-stories/**/*.md`。
- `/t-prd-check` 只写质量报告，不写 `docs/prd` 或 `docs/user-stories`。
- `/t-design`、`/t-task`、`/t-run` 和 Demo 阶段可以读取 draft sources，不得把 draft user story 发布到 `docs/user-stories`。
- `/t-prd-publish` 是把仍然成立的 PRD 草稿和 draft user stories 合并进 `docs/` 的标准入口。
- `t-dream --govern-prd` 可以治理已发布 PRD 和用户故事，但必须先区分 draft sources 与 published sources，并说明写入范围。

## Reference Rules

- PRD、设计、任务和测试注释引用用户故事时必须写明具体来源路径，可以是 `docs/user-stories/...` 或 `.ai/user-stories/...`。
- 面向人类长期文档的引用应优先指向 `docs/user-stories/...`；pre-publish 阶段允许临时指向 `.ai/user-stories/...`。
- Draft user story 发布后，相关 PRD、设计、任务或 Demo 注释中仍有价值的长期引用应在发布或治理阶段改为 `docs/user-stories/...`。

