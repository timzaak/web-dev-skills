# Agent Task Output Contract

实现、修复、测试和验收类 agent 按下述结构返回。设计类 agent 改用 `${CLAUDE_PLUGIN_ROOT}/protocols/design-agent-output-contract.md`；不得混用。

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
      "extension": false,
      "miniapp": false,
      "flutter": false,
      "web_demo": false,
      "extension_demo": false,
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

执行验证或验收时，按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md` 在现有 Handoff/报告保存证据，并通过 `validation_results` 或 `summary` 引用；有后续承接时在 `next_steps` 列出待验证场景与承接位置。不得用当前 item 的 `success` 表示整个 feature 已验收。

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
  "extension": false,
  "miniapp": false,
  "flutter": false,
  "web_demo": false,
  "extension_demo": false,
  "flutter_demo": false
}
```

规则：

- 八个字段都必须出现
- 只将实际受影响层标记为 `true`
- 未启用 extension/miniapp/Flutter 的项目仍返回对应字段为 `false`，以保持修复闭环契约稳定

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
      "extension": false,
      "miniapp": false,
      "flutter": false,
      "web_demo": false,
      "extension_demo": false,
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
- `change_scope` 必须按已产生或可能影响的层填写；字段为 `backend/frontend/extension/miniapp/flutter/web_demo/extension_demo/flutter_demo`。无法判断时八项都保留并在 `error.details` 说明不确定性。
- 若失败发生在修复或验证闭环中，`tests_to_run` 可以为空数组，但必须在 `error.details` 或 `suggested_fix` 中说明无法给出补测命令的原因。

## Controller Dispatch

调用方明确传入 `dispatch_owner: controller` 时，worker 不自行委派；保留本协议的 `task_completion.status`、`change_scope`、`tests_to_run`，在 `task_completion` 内补充以下字段。其他调用方继续使用原有 envelope，不要求新增字段。

- `dispatch`: 原样返回输入的 `phase/revision/item_id/attempt`，用于拒绝过期结果。
- `evidence_refs`: 已写入当前 item Handoff 或现有报告的路径；验证内容按 verification-evidence-contract，不在短返回中复制日志。
- `concerns`: `{message, blocking, evidence}` 数组；没有则为空。必要验证未完成不能返回 success。
- `context_requests`: `{question, evidence, decision_point, blocked_action, needs_user_answer}` 数组；需要补上下文返回 partial，用户决策由控制器处理。
- `blocked_by`: 当前无法自行解决的外部条件数组；与可修复的实现失败区分。
- `repair_request`: 需要其他责任角色时返回 `{agent, reason, evidence_refs, tests_to_run}`；原 item 返回 failed，等待控制器派发修复后重测。不授予 worker 修改其他角色文件的权限。

`success` 必须没有 blocking concerns、context_requests、blocked_by 或 repair_request。不能同时提出修复请求又宣称已完成。accept 仍返回其角色规定的验收结论与独立报告路径，不能用通用 success 替代 verdict。

## Role-Specific Extensions

- `frontend-dev` 可补充 `validation_results`、`components_added`、`components_modified`
- `extension-dev` 可补充 `entrypoints_changed`、`permissions_changed`、`validation_results`
- `miniapp-dev` 可补充 `validation_results`、`components_added`、`components_modified`
- `flutter-dev` 可补充 `validation_results`、`widgets_added`、`widgets_modified`
- `web-demo-dev` / `extension-demo-dev` / `flutter-demo-dev` 可只保留最小成功字段，不需要 `validation_results`
- 其他实现类 agent 可在不破坏上述字段语义的前提下扩展
