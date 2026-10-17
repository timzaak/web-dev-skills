# Agent Task Output Contract

实现、修复、测试和验收角色统一返回 `task_completion`；设计角色使用 `${CLAUDE_PLUGIN_ROOT}/protocols/design-agent-output-contract.md`。

```json
{
  "task_completion": {
    "status": "success|partial|failed",
    "summary": "当前责任闭环的结果",
    "files_modified": [],
    "files_created": [],
    "change_scope": {"implementation": true, "web_demo": false},
    "tests_to_run": [],
    "next_steps": []
  }
}
```

`status` 与 `change_scope` 必填。change_scope 两个布尔字段必须出现，仅将实际受影响范围标为 true；文件列表说明具体模块。不再携带固定技术领域字段。

修复或补测调用必须返回 tests_to_run，其条目按 `${CLAUDE_PLUGIN_ROOT}/protocols/tests-to-run-contract.md`；无法给出可靠补测时明确原因。可选添加 validation_results、tests_written 等证据索引，不复制日志全文。

失败仍使用相同 envelope，status=failed，并增加 error：severity（P0/P1/P2/P3）、type、message、location、details、suggested_fix、blocked_by。部分完成使用 partial，不能作为下游成功依据。

执行与验收证据遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`，在 Handoff/报告中落盘并引用；存在后续承接时在 next_steps 列出待验证场景与承接位置，当前任务 success 不等于整个 feature 验收完成。

## Decision Gaps

需要用户裁决时返回 task_completion.needs_user_answer，并将 status 标为 partial；条目结构和处理规则见 `${CLAUDE_PLUGIN_ROOT}/protocols/decision-continuity-contract.md` 的 Agent Decision Gap。skill 解决前不得把依赖该答案的工作视为完成。slot 规划输出遵循调用方规划契约，其 needs_user_answer 条目使用同一结构。
