# Error Response Template

```json
{
  "error_code": "{{ERROR_CODE}}",
  "message": "{{USER_FACING_MESSAGE}}",
  "recover_action": "{{RECOVER_ACTION}}",
  "retryable": true,
  "details": {
    "feature": "{{FEATURE}}",
    "phase": "{{PHASE}}",
    "blocking_agents": ["{{AGENT_1}}"]
  }
}
```
