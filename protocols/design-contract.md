# Design Contract

`project-design` 返回：

```json
{
  "task_completion": {
    "status": "success|partial|failed",
    "summary": "模块设计摘要",
    "files_created": [],
    "files_modified": [],
    "change_scope": {"implementation": true, "web_demo": false}
  },
  "design_result": {
    "doc_path": ".ai/design/<feature>/<module>.md",
    "decisions_applied": [],
    "needs_user_answer": [],
    "contract_summary": [],
    "contract_dependencies": [],
    "self_check": {"template_complete": true, "paths_verified": true, "unresolved_placeholders": 0}
  }
}
```

success 要求文档落盘、无 needs_user_answer 且 self_check 全通过；partial/failed 不进入合并。failed 增加 task_completion.error。change_scope 语义见 `${CLAUDE_PLUGIN_ROOT}/protocols/agent-task-output-contract.md`。

needs_user_answer 条目与处理规则遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md` 的 Agent Decision Gap。

contract_summary / contract_dependencies 每项含 id、source（项目内唯一契约路径与章节）、description。生产者声明契约，消费者引用相同 id 和 source；接口、消息、文件格式等具体结构由项目规范确定，不预设 HTTP。skill 汇总时核对唯一来源与消费一致性；无跨模块契约时两数组为空并写明不适用原因。

## Design State（`.ai/design/<feature>/.state.json`）

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
