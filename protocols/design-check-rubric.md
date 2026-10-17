# Design Check Rubric

## Scoring

| 维度 | 分值 |
| --- | ---: |
| 需求追溯与覆盖 | 20 |
| 现有实现依据 | 15 |
| 模块方案与边界 | 25 |
| 公共契约与兼容性 | 15 |
| 测试与验收策略 | 15 |
| 决策闭合与汇总一致性 | 10 |

总分 100；仅按目标项目实际约束评分，不以审查者偏好的技术方案扣分。评分、门禁与输出只在本协议定义。

## Clarification Gate

影响范围、业务规则、权限、公共契约、数据、兼容、验收或测试策略的缺口，先按 `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md` 查账本；仍需用户回答时由 skill 提问，回答前不把问题写为假设或风险继续。needs_user_answer 不计入缺陷分，未清空不允许进入执行。

## Detailed Checks

- 按 `${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md` 核对草稿与发布基线；纯技术方案只能在不改变业务/产品/流程/验收目标时仅引用技术预研。
- 主文档与实际模块设计完整；模块来自真实项目，§4.2 路径明确。
- 当前入口与 MODIFY/DELETE 路径真实存在，CREATE 有合法父目录和命名依据；新 skill 目录按结构检查例外处理。
- 关键模块有责任边界、实现入口、异常路径和兼容策略；公共契约唯一，生产者与消费者一致。
- 决策追踪覆盖全部 Active Decision；主文档覆盖矩阵关联需求、设计、测试与全量文件影响。
- 实际命令与验收场景按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`，静态检查不代替必要行为验证。
- 全部实际文档通过 check-decision-closure.py 与 check-design.py，状态符合 `${CLAUDE_PLUGIN_ROOT}/protocols/design-state-contract.md`。

## Severity Rules

P0：关键需求冲突、必需文档缺失、公共契约相互矛盾、范围无法实施、覆盖矩阵或必要行为验证缺失。存在 P0 不通过。

P1：关键实现/失败/兼容路径不清、项目规则严重冲突、文件影响未汇总、验证命令不真实或决策追踪不完整。进入执行前修正会影响实施的 P1。

P2：可压缩重复、非关键表述或导航改进，不阻塞。

## Report Requirements

输出总分与分项得分、参与范围、P0/P1/P2、每项文件证据与修复建议、needs_user_answer、结构/决策扫描结果及是否可进入执行。缺少证据不宣称通过；检查可选，不替代实现后的 accept。

## Pass Gate

- PASS：总分至少 90，无 P0/P1，needs_user_answer=0，确定性扫描通过。
- CONDITIONAL PASS：总分至少 75，无 P0 与阻塞实施的 P1，needs_user_answer=0，扫描通过；列出已知非阻塞改进。
- 其余情况 FAIL；不得只凭总分越过硬门禁。该结论属于可选检查，不代替后续 accept。
