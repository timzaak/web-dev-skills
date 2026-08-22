# Design State Contract

写入 `.ai/design/<feature>/.state.json`：

```json
{
  "status": "in_progress|complete|failed",
  "applicable_stacks": ["backend", "frontend"],
  "completed_stacks": ["backend"],
  "failed_stack": null
}
```

- 调度前写 `in_progress`。
- 每个端成功后更新 `completed_stacks`。
- 无法恢复时写 `failed` 和 `failed_stack`。
- 主文档、分端文档、决策闭合扫描和结构校验全部通过后写 `complete`。
- `/t-task` 和 `/t-design-check` 遇到非 `complete` 状态时停止。
- 状态文件缺失时兼容旧设计产物。
