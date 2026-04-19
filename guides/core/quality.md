# 质量总规范（Core）

## 目标

本文件定义跨领域质量总原则与门禁框架。

具体验收细则已下沉到：
- `${CLAUDE_PLUGIN_ROOT}/guides/backend/quality.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/frontend/quality.md`
- `${CLAUDE_PLUGIN_ROOT}/guides/demo/quality.md`

## 1. 设计与追踪

默认要求：

- 需求来源可追溯到 `docs/`、任务说明或明确的设计输入。
- 重要实现应能说明与设计或需求的对应关系。
- `.ai/design/`、`.ai/task/`、`/t-tools:t-*` 工作流产物可作为辅助治理材料，但不是所有任务的强制前置条件。

## 2. 通用质量门禁

### P0（阻塞）
- 编译/类型检查失败
- 核心测试失败
- 关键验收流程缺失

### P1（重要）
- 关键一致性偏差（接口/文档/用户故事）
- 明显质量风险（高复杂度、关键重复逻辑）

### P2（一般）
- 可维护性优化项

### P3（优化）
- 体验或表达层改进

## 3. 证据与报告要求

质量结论必须：
- 给出文件来源（必要时附行号）
- 给出可执行修复建议
- 按 P0/P1/P2/P3 分类

报告目录：`.ai/quality/`

## 4. 领域细则入口

- 后端验收细则：`${CLAUDE_PLUGIN_ROOT}/guides/backend/quality.md`
- 前端验收细则：`${CLAUDE_PLUGIN_ROOT}/guides/frontend/quality.md`
- Demo 验收细则：`${CLAUDE_PLUGIN_ROOT}/guides/demo/quality.md`

## 5. 执行约束

- 需求语义冲突时，以 `docs/`（PRD + User Stories）为准
- 执行流程与测试约束，以 `${CLAUDE_PLUGIN_ROOT}/guides/` 与 `AGENTS.md` 为准
- 未经授权不得修改与当前任务无关的文件
