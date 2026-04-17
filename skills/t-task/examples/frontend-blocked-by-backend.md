# Example: Frontend Blocked by Backend

## User Input
```bash
/t-task sample-feature --phase frontend
```

## Expected Response
```text
阶段校验失败：frontend 依赖 backend=completed。
当前 backend 状态: running
阻塞项: backend-accept (pending)
下一步: /t-run sample-feature --phase backend
```

## State Unchanged
```json
{
  "phase": "backend",
  "phases": {
    "backend": {"status": "running"},
    "frontend": {"status": "pending", "generated_at": null}
  }
}
```
