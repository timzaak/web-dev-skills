# Design Agent Output Contract

`backend-design`、`frontend-design`、`flutter-design` 严格返回下述结构。实现、测试和验收类 agent 改用 `${CLAUDE_PLUGIN_ROOT}/protocols/agent-task-output-contract.md`。

## Envelope

返回：

```json
{
  "task_completion": {
    "status": "success|partial|failed",
    "summary": "本端设计摘要与关键取舍",
    "files_created": [".ai/design/[feature]/backend.md"],
    "files_modified": [],
    "change_scope": {
      "backend": true,
      "frontend": false,
      "miniapp": false,
      "flutter": false,
      "web_demo": false,
      "flutter_demo": false
    }
  },
  "design_result": {
    "doc_path": ".ai/design/[feature]/backend.md",
    "decisions_applied": ["DEC-[feature]-001"],
    "needs_user_answer": [],
    "contract_summary": [],
    "contract_dependencies": [],
    "self_check": {
      "template_complete": true,
      "paths_verified": true,
      "unresolved_placeholders": 0
    }
  }
}
```

## Status Rules

- `task_completion.status=success`：文档已完整写入，`needs_user_answer` 为空，`self_check` 全部通过。
- `task_completion.status=partial`：只保留可诊断的中间文档；修复后重新调度或终止本轮。
- `task_completion.status=failed`：返回 `task_completion.error` 并终止本端。

`partial` 和 `failed` 不得进入合并。需要用户回答时返回 `task_completion.status=partial`。

## User Decision Gap

`needs_user_answer` 的每项结构固定为：

```json
{
  "question": "问题",
  "evidence": "证据",
  "decision_point": "需要用户决定什么",
  "blocked_action": "阻塞的后续动作"
}
```

## Backend Contract Summary

后端适用时，为每个接口返回：

```json
{
  "operation_id": "createExport",
  "method": "POST",
  "path": "/api/exports",
  "request_fields": ["format", "filters"],
  "response_fields": ["id", "status"],
  "error_codes": [400, 403, 409],
  "callers": ["frontend"]
}
```

- `operation_id` 在当前方案内唯一，并与 `backend.md` 接口清单一致。
- 不适用请求体或响应体时使用空数组，不省略字段。
- `error_codes` 使用整数数组。

## Client Contract Dependencies

前端和 Flutter 只声明消费关系：

```json
{
  "operation_id": "createExport",
  "method": "POST",
  "path": "/api/exports",
  "request_fields_used": ["format", "filters"],
  "response_fields_used": ["id", "status"]
}
```

主会话逐项校验：

- `operation_id` 存在且唯一。
- method/path 与后端摘要一致。
- `request_fields_used`、`response_fields_used` 分别是后端字段集合的子集。
- 客户端依赖的接口调用方包含对应端。

任一校验失败都必须重新调度客户端设计；涉及产品语义时再升级为用户裁决。

## Self Check

`self_check` 必须存在。只要任一布尔值为 false 或 `unresolved_placeholders > 0`，主会话就把结果视为 `partial`，不得进入合并。
