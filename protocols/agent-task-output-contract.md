# Agent Task Output Contract

定义实现类 agent 在完成或失败时返回的通用结构化结果。

## Success Envelope

默认返回：

```json
{
  "task_completion": {
    "status": "success|partial|failed",
    "summary": "任务完成摘要",
    "files_modified": ["path/a.tsx"],
    "files_created": ["path/b.test.tsx"],
    "change_scope": {
      "backend": false,
      "frontend": true,
      "demo": false
    },
    "tests_to_run": [
      {
        "layer": "frontend",
        "command": "cd frontend && npm run test:run -- src/example.test.tsx",
        "reason": "最小相关回归",
        "required": true
      }
    ],
    "next_steps": ["后续建议"]
  }
}
```

## Required Fields

- `task_completion.status`
- `task_completion.change_scope`
- `task_completion.tests_to_run` when the agent is used in a repair or verification loop that expects retest instructions

## Optional Fields

按角色扩展：

- `summary`
- `files_modified`
- `files_created`
- `components_added`
- `components_modified`
- `validation_results`
- `tests_written`
- `next_steps`

## `change_scope`

```json
{
  "backend": false,
  "frontend": false,
  "demo": false
}
```

规则：

- 三个字段都必须出现
- 只将实际受影响层标记为 `true`

## `tests_to_run`

字段结构和允许命令统一参考：`protocols/tests-to-run-contract.md`

规则：

- 当上游编排依赖补测指令时，不能省略
- 若无法给出可靠补测，必须在 `reason` 或 `summary` 中说明原因，而不是静默留空

## Error Envelope

默认失败返回：

```json
{
  "error": {
    "severity": "P0|P1|P2|P3",
    "type": "type_check_error|build_error|runtime_error|logic_error",
    "message": "错误描述",
    "location": "文件路径:行号",
    "details": "详细错误信息",
    "suggested_fix": "建议的修复方案",
    "blocked_by": ["阻塞原因"]
  }
}
```

## Role-Specific Extensions

- `frontend-dev` 可补充 `validation_results`、`components_added`、`components_modified`
- `demo-dev` 可只保留最小成功字段，不需要 `validation_results`
- 其他实现类 agent 可在不破坏上述字段语义的前提下扩展
