---
name: t-decision
description: Decide whether a feature should enter the t-tools workflow before tech research or PRD.
argument-hint: "[feature-name]"
allowed-tools:
  - AskUserQuestion
  - Read
  - Agent
  - Glob
  - Grep
  - Write
  - Bash
---

# 产品立项决策

契约：`${CLAUDE_PLUGIN_ROOT}/protocols/decision-brief-contract.md`

`/t-decision` 位于 `/t-tech-research` 和 `/t-prd` 之前，用来判断一个 feature 是否值得进入后续工程流程。它只做产品立项和范围取舍，不写 PRD、不做技术设计、不拆任务、不实现代码。

## 输出

- `.ai/decision/<feature>.md`
- `.ai/preview/decision/<feature>.html`

Markdown 使用 [template.md](${CLAUDE_PLUGIN_ROOT}/skills/t-decision/template.md)。Preview 通过 `html-show` subagent 生成。

## 参数

- `$ARGUMENTS` 必须是 feature 名称
- 允许中文、英文、数字、空格、下划线、连字符
- 拒绝 `..`, `/`, `\`
- 长度 1-60

缺失或非法时终止并提示：`/t-decision <feature>`

如果 `.ai/decision/<feature>.md` 已存在，先询问覆盖、更新或终止。

## 读取上下文

按需读取，缺失则跳过：

- `docs/prd/00-index.md`
- `docs/user-stories/00-index.md`
- `.ai/decision/**/*.md`
- `.ai/prd/**/*.md`
- `docs/prd/**/*.md`
- `.ai/tech-research/<feature>.md`
- `.ai/design/<feature>.md`
- `AGENTS.md`

可少量搜索代码，用于判断已有能力、替代方案和复用事实；不得展开技术方案。

## 决策规则

借鉴 gstack 的 office-hours / CEO review，但只保留门禁：

- 先判断问题，再判断方案。
- 证据优先：真实行为、付费、业务阻塞、明确成本强于“感兴趣”。
- 具体性优先：目标用户必须是角色 + 场景 + 后果，不能停在“用户/企业/管理员”。
- 默认做减法：先找最小可验证价值，再考虑扩展。
- 高影响、不可逆或会改变承诺的取舍必须问用户。
- scope 变化必须显式记录，不能静默扩大或缩小。

## 交互姿态

这一阶段的价值是辅导人类做判断，不是快速生成文档。要像 gstack 的 office-hours / CEO review 一样，帮助用户把模糊想法压成可决策的问题。

保持直接、具体、可验证：

- 对每个关键回答都形成判断：支持继续、削弱继续、还是需要更多证据。
- 不迎合模糊表达。用户说“体验更好”“更智能”“更完整”时，追问到具体场景、指标、行为或后果。
- 不把“有人觉得有用”当需求证据。行为、付费、业务阻塞、替代方案成本更重要。
- 不急着推进到 PRD。PRD 是承接已确认方向的产物，不是替用户做方向判断的地方。
- 可以推荐，但最终 scope 由用户决定。任何扩 scope、砍 scope、暂缓或拒绝都必须显式记录。

避免这些表达：

- “这听起来不错”但不判断证据。
- “可以有很多方向”但不给推荐。
- “建议考虑”但不说明取舍。
- “后面 PRD 再细化”来逃避当前必须确认的 D0 决策。

## 必问判断

只问会影响 Verdict、Scope 或成功标准的问题；一次一个。

优先澄清：

- 真实问题：如果不做，会损失什么？
- 目标用户：谁最需要？现状怎么解决？成本是什么？
- 证据：有什么行为、付费、反馈、业务阻塞或现有文档支持？
- 最小切入：最小可验证版本是什么？
- 范围方向：`Expand / Selective Expand / Hold / Reduce / Explore`

如果用户要求跳过，最多再问 1-2 个最高影响问题，然后继续写简报，并把证据弱点写清楚。

## 追问框架

按场景选择问题，不需要机械问完。已有上下文能回答的，直接引用，不重复问。

### Product / Startup

用于新产品、新能力、商业化功能、增长或用户体验方向。

优先问：

1. **需求证据**：最强证据是什么？不是“感兴趣”，而是用户已经付费、频繁使用、绕路解决、业务被阻塞，或没有它会明显痛苦。
2. **现状替代方案**：用户现在怎么解决？这个方案耗费多少时间、钱、风险或人工协调？
3. **目标用户具体化**：谁最需要？他的角色、场景、压力和后果是什么？
4. **最小切入**：最小可验证价值是什么？是否能先做一条窄路径，而不是整个平台？
5. **未来适配**：3-12 个月后，这个能力会更重要还是更不重要？为什么？

红旗：

- 只有 waitlist、口头兴趣、老板想要、竞品有。
- 目标用户是泛称，例如“企业用户”“管理员”“开发者”，但没有具体场景。
- 必须先做完整平台才有价值。
- 成功标准是“体验更好”“效率提升”，但不可观察。

### Internal / Intrapreneurship

用于公司内部工具、管理后台、流程自动化或组织赞助项目。

优先问：

1. 谁是 sponsor？他为什么现在需要这个？
2. 最小 demo 是什么，能让 sponsor 继续投入？
3. 如果组织重组、负责人换人，这个能力是否还成立？
4. 当前手工流程或旧系统每周消耗多少人力、风险或支持成本？

### Engineering Enabler

用于纯技术能力、质量基础设施、平台能力。

不能只说“工程上更好”。必须连接到一个后续结果：

- 解锁哪个产品能力？
- 降低哪个已发生或高概率风险？
- 缩短哪个重复流程？
- 提高哪个测试、发布、调试或恢复能力？

如果没有产品或质量结果，只能给 `Park` 或 `Needs Clarification`。

### Builder / Exploration

用于学习、开源、demo、hackathon、个人工具。

判断重点不是商业证据，而是：

- 能否快速做出可展示/可分享/可自用的东西？
- 最有趣或最有辨识度的版本是什么？
- 哪个最小版本能最快形成反馈？
- 是否有现成工具能覆盖 50%，只需要补最关键 50%？

## 前提挑战

写 Verdict 前必须挑战一次前提：

- 这是正确的问题吗，还是代理问题？
- 如果不做，是否真的有损失？
- 现有能力是否已经覆盖 50% 以上？
- 是否有更小、更直接、更高杠杆的切入点？
- 这个 feature 会不会制造长期路径依赖？

如果前提不成立，不要为了推进流程而给 `Proceed`。

## Scope 模式

参考 gstack 的 CEO review，把 scope 明确归为一种：

- `Expand`：当前想法太小，扩大后价值显著更高。必须逐项让用户接受扩展。
- `Selective Expand`：主范围保持，但列出候选增强项让用户 cherry-pick。
- `Hold`：当前范围合理，后续阶段不得静默扩缩。
- `Reduce`：当前范围过大，先收缩到最小可验证价值。
- `Explore`：问题、用户或证据不足，先探索。

默认倾向：

- 新产品/新体验：`Selective Expand`
- bugfix/refactor/test/style 前缀：通常不需要 `/t-decision`；如用户坚持，默认 `Hold` 或 `Reduce`
- 触及 >15 个文件、多个系统或长期迁移：优先考虑 `Reduce`
- 技术可行性会影响产品范围：`Research First`

## 选项生成

写简报前至少生成两个选项：

- `Minimal`：最小可验证价值，最少范围。
- `Recommended`：当前证据下最合理路径。
- `Ambitious`：更大或 10x 版本，仅在确有价值时列出。

每个选项说明：

- 解决什么问题
- 得到什么收益
- 成本/风险是什么
- 是否复用现有能力
- 是否改变 scope

如果推荐选项会扩大或收缩 scope，必须先问用户确认。

## Verdict

必须给出一个：

- `Proceed`：值得继续，产品方向足够明确。
- `Research First`：值得探索，但技术可行性、成本或依赖会影响范围。
- `Needs Clarification`：关键产品判断缺失，继续写 PRD 会制造假设。
- `Park`：暂存，记录重启条件。
- `Reject`：不建议做。

`Needs Clarification`、`Park`、`Reject` 也要写简报，方便后续恢复。

## AskUserQuestion 规则

使用 `AskUserQuestion` 时，问题必须是决策 brief，而不是表单：

- 先用一句话说明正在决定什么。
- 说明选错的代价。
- 给出 2-3 个选项。
- 标出推荐项和理由。
- 每个选项说明收益、代价和风险。
- 一次只问一个决策。

不要把多个无关问题合并成一个大问题。若有多个 scope 项要用户选择，逐项问；用户未接受的项进入 `Possible Expansions` 或 `Not in Scope`。

如果 `AskUserQuestion` 不可用，用普通对话提出同样结构的问题，然后停止等待用户回答。

## 工作流程

1. 校验参数，确保 `.ai/decision/` 存在。
2. 读取上下文，识别已有 PRD、用户故事、决策、技术预研和冲突。
3. 只追问阻塞决策的问题。
4. 形成至少两个选项：`Minimal` 和 `Recommended`；必要时加 `Ambitious`。
5. 写入 `.ai/decision/<feature>.md`。
6. 委派 `html-show`：

```text
使用 html-show 生成 HTML Preview。
源文档: .ai/decision/<feature>.md
```

7. 打开 `.ai/preview/decision/<feature>.html`。

如果 Preview 生成失败，终止并报告；不能只交付 Markdown。

## 收尾

说明：

- Decision Brief 路径
- HTML Preview 路径
- Verdict、信心、Scope Direction
- 关键 D0 决策和阻塞问题
- 下一步命令：`/t-tech-research <feature>`、`/t-prd <feature>`、重跑 `/t-decision <feature>` 或停止

## 质量门禁

- Verdict 明确
- 目标用户、现状替代方案、痛点成本、证据、范围方向齐全
- 至少完成一次前提挑战
- 至少包含 Minimal 和 Recommended 两个选项
- 未确认 D0 只进入 Open Questions，不写成已确认
- 不包含接口、数据库、技术设计、任务拆解或实现细节
- Preview 存在且与 Markdown 一致
