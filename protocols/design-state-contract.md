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

- 适用端取值为 backend / frontend / extension / flutter / shopify；各端使用独立完成/失败记录，extension 与 frontend 不能合并状态。shopify 端由 `shopify.md` 分端文档承载（shopify-app 与 shopify-extension 两个 phase 共用同一分端设计，不拆两份状态）。
- 调度前写 `in_progress`。
- 每个端成功后更新 `completed_stacks`。
- 无法恢复时写 `failed` 和 `failed_stack`。
- 主文档、分端文档、决策闭合扫描和结构校验全部通过后写 `complete`。
- `/t-super-run` 和 `/t-design-check` 遇到非 `complete` 状态时停止。
- 状态文件缺失时停止，提示运行 `/t-design <feature>` 生成完整设计状态。
