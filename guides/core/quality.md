# 质量总规范（Core）

本文件定义跨领域质量原则；验收前读取 `${CLAUDE_PLUGIN_ROOT}/protocols/acceptance-contract.md`，公共分级、结论、报告、只读边界和结果消费仅由该协议维护。

## 设计与追踪

- 需求来源、草稿与正式基线关系按 `${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md`，不以已发布事实静默覆盖本轮候选变更。
- 主链入口已要求设计/任务时沿用门禁；独立验收既有实现可使用明确需求、任务说明和已有设计，不强制补插件工作流文件。
- 不按 bugfix/refactor 命名前缀豁免。缺失影响业务规则、公共契约或验收目标的决策时交回调用方。

## 门禁与证据

工程门禁来自目标项目已确认规则与真实配置；Web Demo 细则见 `${CLAUDE_PLUGIN_ROOT}/guides/web-demo/quality.md`，不引入默认生产技术栈。

行为验证责任、后续承接、最终交付和证据复用按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`。必要门禁未完成时不能用评分或维护性建议代替证据；accept 独立收口，不自行修复实现或降低标准。

## 执行边界

共享执行/输出契约以 protocols 为准，工程实践以项目约束和已确认适用规则为准。未经授权不得修改与当前任务无关的文件。
