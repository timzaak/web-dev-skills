---
name: t-web-demo-run
description: Run a single demo E2E test file, diagnose failures, dispatch fixes to agents, and re-run until pass.
argument-hint: "[测试文件路径]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Task
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
  - Agent
---

# 单文件 Demo 测试运行与修复

运行时边界统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`
单文件运行与修复闭环统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/web-demo-run-repair-contract.md`

## 目标
- 先对一个测试文件整体执行。
- 整体失败时，再按用例粒度顺序执行。
- 单个用例失败时先诊断，再分发到对应 agent 修复。
- 修复后必须执行相关后端/前端补测，不能只跑 Demo。
- 输出可恢复的任务状态与机器可解析结果。

## 使用方式
```bash
/t-tools:t-web-demo-run demo/e2e/<role>/<scenario>.e2e.ts
```

## 执行流程

- 校验参数：测试文件必须存在且扩展名为 `.e2e.ts`。
- 按 `web-demo-run-repair-contract.md` 执行整文件、失败用例修复、补测和整文件终验。
- 用 Task 记录当前失败用例和尝试轮次，供中断后继续。
- 最后一行仅输出该协议定义的 `Result: {...}`。

## 恢复机制
当流程中断时：
- 读取 `TaskList`。
- 按任务列表顺序找到第一个 `pending` 或 `failed` 任务继续执行。

## 失败处理
- 环境启动失败：停止并记录错误。
- 无可用修复方案：标记该用例失败，继续下一个。
- 达到最大重试次数：标记失败并继续。
- 补测失败：记录失败与风险，不阻断本用例修复循环，继续 Demo 重跑与后续尝试。

## 质量门禁
- 单次执行只处理一个测试文件。
- 必须先整体运行测试文件；只有整体失败时才拆分用例。
- 拆分后的用例执行必须串行。
- 每个失败用例必须有诊断记录。
- 每次修复后必须先执行相关层补测，再执行 Demo 验证。
- 当次修复实际产生后端代码变动时，必须在 Demo 验证前重建环境；判定以修复前后文件变化为准，不以 agent 类型或 `change_scope` 代替。
- 定向失败用例全部通过后，必须以整文件终验收口。
- 必须输出最后一行 `Result: {...}`。
