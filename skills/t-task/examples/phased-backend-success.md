# Example: Phased Backend Success

## User Input
```bash
/t-task sample-feature --phase backend
```

## Expected Response
```text
已生成 backend 阶段任务：
- backend/index.md
- backend/dev.md + backend/dev/*.md
- backend/test.md + backend/test/*.md
- backend/accept.md + backend/accept/*.md
- backend/finalize.md
生成方式: 按 `dev -> test -> accept` 串行生成 slot，通过写入前硬校验后再写盘，并向下一个 slot 传递上一个 slot 的路径与摘要。
状态更新: phase=backend, phases.backend.generated_at=<timestamp>
下一步: /t-task-check sample-feature --phase backend
```

## State Delta
```json
{
  "phase": "backend",
  "phases": {
    "backend": {"status": "pending", "generated_at": "2026-03-04T10:00:00Z"}
  },
  "tasks": {
    "backend": {
      "dev": {"status": "pending"},
      "test": {"status": "pending"},
      "accept": {"status": "pending"}
    }
  }
}
```
