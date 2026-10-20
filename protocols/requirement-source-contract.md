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

`.ai/decision-log/**/*.md` 是当前 feature 跨阶段决策连续性的结构化来源。其记录规则、稳定 ID 和用户决策暴露门禁统一参考 `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md`。已发布 feature 的账本随 `/t-prd-publish` 内化进正式 PRD 后移除；后续轮次从已发布产物重建，不得因账本缺失停止。

## Read Rules

- `/t-prd` 先按 feature 查找并读取 `.ai/decision/<feature>.md`、`.ai/decision-log/<feature>.md` 和 `.ai/tech-research/<feature>.md`（存在时）；随后检查 `docs/prd/` 和 `.ai/prd/`，必须读取同名 PRD 及与当前 feature 的领域、流程或业务规则相关的已有 PRD，即使没有独立的“需求文档”或 user story。已有 PRD 用于确定已发布基线、现有能力边界和候选变更关系；缺少 PRD 或 user story 时不得因此要求用户提供文档或停止。
- Pre-publish 阶段必须同时读取相关 published sources 和 draft sources。
- Pre-publish 阶段在提问或作出新决策前必须读取相关 `.ai/decision-log/<feature>.md`；已解决问题不得重复询问。
- 同一 feature 存在 `.ai/prd` 或 `.ai/user-stories` 时，它们表达本轮候选变更意图；`docs/prd` 和 `docs/user-stories` 表达已发布基线。
- `/t-tech-research` 在 PRD 草稿后运行时必须读取相关 `.ai/prd`、`.ai/user-stories` 与 published baseline，将其作为产品边界输入；技术结论不得静默改写产品语义。
- 设计、任务、实现、测试、Demo 和检查阶段可以引用 draft user story，但必须保留来源路径，不能把它改写成已发布事实。
- 纯技术方案可以只引用 `.ai/tech-research/**/*.md`，但必须声明不涉及业务逻辑、产品规则、用户可见流程或验收目标变动。
- Draft source 与 published source 在目标、范围、角色、权限、业务状态或验收目标上冲突时，停止并报告冲突；不要自动合并或平均折中。
- 技术预研结论会改变范围、业务规则、用户流程或验收目标时，必须通过 `/t-prd` 更新候选 PRD / user story；进入 `/t-design` 前不得保留未解释冲突。

### 同一 feature 草稿与正式来源并存的裁决

消费需求来源的阶段（`/t-design`、`/t-super-run`、检查类 skill）按以下规则处理：

- 草稿与正式来源一致，或草稿明确声明为增量/替换 → 继续工作，在产物中同时引用两者并给出差异摘要。
- 在核心业务边界、角色、权限、业务状态或验收目标上冲突且无法确认覆盖关系 → 停止，提示先修正草稿；必要时运行 `/t-prd-check [feature]` 定位冲突。
- 草稿不存在但正式来源存在 → 可基于正式来源继续，并在产物中标记"未发现草稿"。
- 默认基于草稿继续设计或检查，不得要求先把草稿发布到 `docs/`；产物中保留 `.ai/...` 来源路径。

## Write Rules

- `/t-prd` 只写 `.ai/prd/**/*.md` 和 `.ai/user-stories/**/*.md`。
- `/t-prd-check` 只写质量报告，不写 `docs/prd` 或 `docs/user-stories`。
- `/t-design`、`/t-super-run` 和 Demo 阶段可以读取 draft sources，不得把 draft user story 发布到 `docs/user-stories`。
- `/t-prd-publish` 是把仍然成立的 PRD 草稿和 draft user stories 合并进 `docs/` 的标准入口。
- `t-dream` 只读审计 PRD 和用户故事；治理建议只写入质量报告，它必须区分 draft sources 与 published sources，不执行任何写入。

## Reference Rules

代码注释只保留稳定追溯信息，工作流文档保存本轮真实来源；具体规则统一见下节。其他临时路径注释约束按 `${CLAUDE_PLUGIN_ROOT}/protocols/code-comment-contract.md`。

## Story Traceability

实现、测试、Demo、accept 及发布在处理故事映射时读取：

- 测试追溯使用稳定 US ID；已发布来源存在时可同时写 `docs/user-stories/...` 路径，路径必须真实且指向该 ID。只有草稿的新故事，测试注释只写 US ID，不虚构尚未存在的正式路径，也不写 `.ai/` 路径。
- 设计、任务、Handoff 或验收报告中记录“测试文件/US ID → 真实故事来源路径、必要场景及关键断言”。发布前来源可以是 `.ai/user-stories/...`；目标仅给测试文件且没有映射时，可从当前 feature 的相关来源解析 US ID，必须唯一且匹配本轮意图。缺失或多义时交回调用方补齐，不凭名称猜测。
- 草稿与正式来源并存时按 Read Rules 判断本轮候选变更及已发布基线；声明增量/替换关系可继续，不把旧正式故事内容冒充本轮验收目标。
- 发布前验收检查真实 draft/published 来源、稳定 ID 和实际行为，不以正式路径尚未生成拒绝，也不要求先发布。无 US ID 的已有测试可通过其有效正式故事路径定位 ID；不为格式要求重写无关历史测试。
- `/t-prd-publish` 在行为验收后发布，保留或明确映射测试引用的 US ID，验证本轮测试可从正式故事唯一定位；有代码中的正式路径引用时同时验证路径与 ID。完成此项前不删除草稿；仅有 US ID 的测试无需为了发布改源码。
- 来源发布迁移但验收语义和代码未变化时，不要求重跑行为验证；故事的角色、权限、动作、预期结果或必要场景变化时，先按验证证据协议重新验收，再发布。

`.ai/` 工作流文档可保留真实草稿路径和 ID，不能把草稿表述为已发布事实；交付代码注释不引用将被清理的临时路径。

