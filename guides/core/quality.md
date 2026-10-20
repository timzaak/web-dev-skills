# 质量总规范（Core）

## 目标

本文件定义跨领域质量检查原则；accept 的结论、分级、报告与只读边界只由 `${CLAUDE_PLUGIN_ROOT}/protocols/acceptance-contract.md` 定义，验收前读取。本页不定义第二套验收判定。

## 1. 设计与追踪

默认要求：

- 需求来源可追溯到 `docs/`、任务说明或明确的设计输入。
- 重要实现应能说明与设计或需求的对应关系。
- 主链入口已经要求设计/任务时沿用其门禁，检查主文档及当前分端设计。独立验收既有项目可使用明确的需求、任务说明和已有设计，不强制补插件工作流文件。
- 不按 `bugfix-`、`refactor-` 等命名前缀自动豁免；按实际影响判断所需设计。缺失影响业务规则、公共契约或验收目标的决策时交回调用方，不能以“修复/重构”名称跳过。

验收前读取 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`，统一判断业务验证责任、阶段放行、最终交付及证据复用；下文和领域指南中的执行命令按该协议取得或复核证据。

## 2. 验收与证据

公共验收协议统一处理必要门禁未完成、问题分级、阶段放行与拒绝恢复。每条问题须有来源、实际影响和可执行建议；维护性建议不代替缺陷证据。报告放 `.ai/quality/`，路径和字段不在各领域重复定义。

## 3. 领域细则入口

- 后端验收细则：`${CLAUDE_PLUGIN_ROOT}/guides/backend/quality.md`
- 前端验收细则：`${CLAUDE_PLUGIN_ROOT}/guides/frontend/quality.md`
- 小程序验收细则：`${CLAUDE_PLUGIN_ROOT}/guides/miniapp/quality.md`
- 扩展验收细则：`${CLAUDE_PLUGIN_ROOT}/guides/extension/quality.md`
- Shopify 验收细则：`${CLAUDE_PLUGIN_ROOT}/guides/shopify/quality.md`
- Web Demo 验收细则：`${CLAUDE_PLUGIN_ROOT}/guides/web-demo/quality.md`
- 扩展 Demo 验收细则：`${CLAUDE_PLUGIN_ROOT}/protocols/extension-demo-acceptance-contract.md`
- Flutter Demo 验收细则：`${CLAUDE_PLUGIN_ROOT}/guides/flutter/demo-testing.md`

## 4. 执行约束

- 需求语义冲突按 `${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md` 裁决草稿与正式来源关系；无法确认时交回调用方，不静默以已发布基线覆盖本轮候选变更
- 共享执行/输出契约以 `protocols/` 为准；工程实践以适用的领域 guide 和项目约束为准
- 未经授权不得修改与当前任务无关的文件
