# Agent Task Output Contract

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
      "miniapp": false,
      "flutter": false,
      "web_demo": false,
      "flutter_demo": false
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
  "miniapp": false,
  "flutter": false,
  "web_demo": false,
  "flutter_demo": false
}
```

规则：

- 六个字段都必须出现
- 只将实际受影响层标记为 `true`
- 未启用 miniapp/Flutter 的项目仍返回对应字段为 `false`，以保持修复闭环契约稳定

## `tests_to_run`

字段结构和允许命令统一参考：`${CLAUDE_PLUGIN_ROOT}/protocols/tests-to-run-contract.md`

规则：

- 当上游编排依赖补测指令时，不能省略
- 若无法给出可靠补测，必须在 `reason` 或 `summary` 中说明原因，而不是静默留空

## Error Envelope

默认失败返回：

```json
{
  "task_completion": {
    "status": "failed",
    "change_scope": {
      "backend": false,
      "frontend": true,
      "miniapp": false,
      "flutter": false,
      "web_demo": false,
      "flutter_demo": false
    },
    "tests_to_run": [],
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
}
```

失败返回规则：

- 失败也必须使用 `task_completion` envelope，便于调用方统一读取 `task_completion.status`。
- `task_completion.status` 必须为 `failed`。
- `change_scope` 必须按已产生或可能影响的层填写；字段为 `backend/frontend/miniapp/flutter/web_demo/flutter_demo`。无法判断时六项都保留并在 `error.details` 说明不确定性。
- 若失败发生在修复或验证闭环中，`tests_to_run` 可以为空数组，但必须在 `error.details` 或 `suggested_fix` 中说明无法给出补测命令的原因。

## Role-Specific Extensions

- `frontend-dev` 可补充 `validation_results`、`components_added`、`components_modified`
- `miniapp-dev` 可补充 `validation_results`、`components_added`、`components_modified`
- `flutter-dev` 可补充 `validation_results`、`widgets_added`、`widgets_modified`
- `web-demo-dev` / `flutter-demo-dev` 可只保留最小成功字段，不需要 `validation_results`
- 其他实现类 agent 可在不破坏上述字段语义的前提下扩展
