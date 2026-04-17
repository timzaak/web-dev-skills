# Example: Phased Backend Success

## User Input
```bash
/t-task sample-feature --phase backend
```

## Expected Response
```text
已生成 backend 阶段任务（4 个文件：index.md + dev.md + test.md + accept.md）。
生成方式: 按 `dev -> test -> accept` 串行写盘，并向下一个 slot 传递上一个文件的路径与摘要。
状态更新: phase=backend, phases.backend.generated_at=<timestamp>
下一步: /t-run sample-feature --phase backend
```

## State Delta
```json
{
  "phase": "backend",
  "agents": {
    "backend": ["backend-dev", "backend-test", "backend-accept"]
  },
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
