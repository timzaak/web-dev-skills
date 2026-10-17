# Design State Contract

`.ai/design/<feature>/.state.json`：

```json
{
  "status": "in_progress|complete|failed",
  "applicable_stacks": ["processor", "adapter"],
  "completed_stacks": ["processor"],
  "failed_stack": null
}
```

保留 stacks 字段名作为结构契约，值改为目标项目真实模块 ID，与主文档 §4.2 完全一致；ID 为稳定 kebab-case，拒绝路径分隔符、点路径和重复值。分模块路径在 §4.2 显式声明，允许同一主文档覆盖小型项目（路径写 `main`）。独立模块文档位于 `.ai/design/<feature>/<module>.md`。

开始生成前写 in_progress；每个模块成功后更新 completed_stacks；无法恢复时写 failed 与 failed_stack。只有全部适用模块、主文档、决策闭合和结构校验通过才写 complete；complete 要求 completed_stacks 与 applicable_stacks 集合相等、failed_stack=null。

下游遇到缺失、损坏、非 complete 或集合不一致的状态必须停止并提示恢复 `/t-design <feature>`。重复执行复用有效产物，只重做受影响模块；旧领域状态不自动迁移，保留后重新规划。
