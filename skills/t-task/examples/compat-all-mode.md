# Example: Auto Select First Incomplete Phase

## User Input
```bash
/t-task sample-feature
```

## Expected Response
```text
已生成 backend 阶段任务：
- backend/index.md
- backend/dev.md + backend/dev/*.md
- backend/test.md + backend/test/*.md
- backend/accept.md + backend/accept/*.md
- backend/finalize.md

下一步: /t-run sample-feature --phase backend
```

## State Delta
```json
{
  "feature": "sample-feature",
  "phase": "backend",
  "phases": {
    "backend": {"status": "pending", "generated_at": "<timestamp>"},
    "frontend": {"status": "pending", "generated_at": null},
    "demo": {"status": "pending", "generated_at": null}
  }
}
```
