# Design Agent Output Contract

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
