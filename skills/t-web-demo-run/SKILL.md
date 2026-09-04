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
单文件运行与修复闭环（整文件 → 拆用例 → 诊断 → 分发修复 → 补测 → 整文件终验，含环境重建、run ID 和结果字段规则）统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/web-demo-run-repair-contract.md`

## 使用方式

```bash
/t-tools:t-web-demo-run demo/e2e/<role>/<scenario>.e2e.ts
```

## 执行流程

- 校验参数：测试文件必须存在且扩展名为 `.e2e.ts`；单次执行只处理一个测试文件。
- 按 `web-demo-run-repair-contract.md` 的单文件执行顺序处理整文件运行、失败用例修复、补测和整文件终验。
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
