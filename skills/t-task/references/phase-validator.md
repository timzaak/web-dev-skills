---
name: phase-validator
description: >
  校验阶段转换条件，确保分阶段顺序按 active phases 依赖执行。
tools:
  - Read
---

# 阶段验证器（低冗余版）

## Purpose
- 在 `/t-task --phase` 或 `/t-run --phase` 前验证是否可进入目标阶段。

## Inputs
| 参数 | 必需 | 说明 |
|---|---|---|
| `feature` | 是 | 功能名 |
| `target_phase` | 是 | backend / frontend / miniapp / demo |
| `state_json_path` | 是 | `.ai/task/[feature]/.state.json` |

## Output Contract
```json
{
  "valid": true,
  "message": "验证通过，可以进入 frontend 阶段",
  "pre_phase": null,
  "pre_phase_status": null,
  "blocking_items": []
}
```

## Rules
1. supported phases 固定为：
   - `backend`
   - `frontend`
   - `miniapp`
   - `demo`
2. active phases 来自 `.state.json.phases` 的键集合；未启用 miniapp 的项目不要求存在 `miniapp`。
3. 默认阶段依赖为：
   - `backend` 无前置
   - `frontend` 依赖 `backend`
   - `miniapp` 依赖 `frontend`
   - `demo` 依赖 active phases 中排在它之前的最后一个交付阶段
4. `target_phase` 不在 supported phases 中时非法。
5. `target_phase` 不在 active phases 中时返回 `valid=false`，提示当前项目未启用该阶段。
6. 只读取当前 `.state.json` 的 `phase/phases/tasks` 结构，不兼容旧 `state.agents`。
7. 校验失败时必须返回阻塞阶段与阻塞 items/slots，而不是虚构 agent 状态。

## Blocking Rule
- 阻塞项定义：目标前置阶段中尚未 `completed` 的 slot 或 item。
- 优先返回更具体的阻塞 item；若没有 item 级状态，则返回 slot 状态。
- backend 阶段常见阻塞项：
  - `tasks.backend.dev`
  - `tasks.backend.test`
  - `tasks.backend.accept`
- frontend 阶段常见阻塞项：
  - `tasks.frontend.dev`
  - `tasks.frontend.test`
  - `tasks.frontend.accept`
- miniapp 阶段常见阻塞项：
  - `tasks.miniapp.dev`
  - `tasks.miniapp.test`
  - `tasks.miniapp.accept`
- demo 阶段的直接前置看 active phases 中 demo 的上一阶段；有 miniapp 时为 `miniapp`，无 miniapp 时为 `frontend`。

## Errors
| 错误 | 处理 |
|---|---|
| `target_phase` 非法 | 返回 `valid=false` + 允许值列表 |
| `target_phase` 未启用 | 返回 `valid=false` + 当前 active phases 列表 |
| 状态文件不存在 | 返回 `valid=false` + 提示先运行 `/t-task` |
| 状态文件格式损坏 | 返回 `valid=false` + 提示重建任务目录 |
| 发现旧结构字段 | 返回 `valid=false` + 提示删除旧任务目录后重建 |

## Minimal Example
```json
{
  "valid": false,
  "message": "前置阶段 'backend' 尚未完成（running）",
  "pre_phase": "backend",
  "pre_phase_status": "running",
  "blocking_items": ["tasks.backend.accept (pending)"]
}
```
