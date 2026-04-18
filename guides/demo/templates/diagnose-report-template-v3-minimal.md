# 诊断报告: {{TEST_NAME}} - {{TIMESTAMP}}

- `problem_code`: `{{PROBLEM_CODE}}`
- `severity`: `{{SEVERITY}}`
- `recommended_agent`: `{{RECOMMENDED_AGENT}}`
- `confidence`: `{{CONFIDENCE}}`

## 失败上下文

**错误信息**:
```
{{ERROR_MESSAGE}}
```

**发生位置**:
- **文件**: `{{FILE_PATH}}`
- **行号**: `{{LINE_NUMBER}}`
- **测试**: `{{TEST_SUITE}} > {{TEST_CASE}}`

**关键日志**:
```log
{{MOST_RELEVANT_LOG_LINE}}
```

**失败请求摘要**（如适用）:
```http
{{FAILED_API_REQUEST}}
```

---

## 问题分类

- **主分类**: `{{PROBLEM_CODE}}`
- **严重级别**: `{{SEVERITY}}`
- **推荐处理方**: `{{RECOMMENDED_AGENT}}`
- **结论强度**: `{{CONFIDENCE}}`
- **分类说明**: {{CLASSIFICATION_SUMMARY}}

---

## 根本原因分析

**直接原因**: {{THE_IMMEDIATE_CAUSE}}

**间接原因**: {{THE_UNDERLYING_ISSUE}}

**证据**:
```text
{{EVIDENCE_SUMMARY}}
```

**代码或日志片段**:
```text
{{CODE_OR_LOG_SNIPPET}}
```

---

## 修复建议

**推荐方案**: {{RECOMMENDED_FIX}}

**最小修改点**:
1. {{FIX_STEP_1}}
2. {{FIX_STEP_2}}

**次要观察**（可选）:
- {{SECONDARY_NOTE_1}}
- {{SECONDARY_NOTE_2}}

---

## 相关文件

| 类型 | 文件路径 | 行号 | 角色 |
|---|---|---|---|
| 测试 | `{{TEST_FILE}}` | `{{TEST_LINE}}` | 失败入口 |
| 证据 | `{{EVIDENCE_FILE}}` | `{{EVIDENCE_LINE}}` | 关键证据 |
| 候选修复 | `{{TARGET_FILE}}` | `{{TARGET_LINE}}` | 建议修改 |

---

## API复现命令（来自 network.json）

仅在 API 类问题时保留本节；否则删除整节。

### 请求 1

- requestId: `{{REQUEST_ID_1_OR_NA}}`
- status/error: `{{STATUS_OR_ERROR_1}}`
- original_url: `{{ORIGINAL_URL_1}}`
- normalized_url: `{{NORMALIZED_URL_1}}`

```bash
{{REPLAY_CURL_1}}
```

### 请求 2（可选）

- requestId: `{{REQUEST_ID_2_OR_NA}}`
- status/error: `{{STATUS_OR_ERROR_2}}`
- original_url: `{{ORIGINAL_URL_2}}`
- normalized_url: `{{NORMALIZED_URL_2}}`

```bash
{{REPLAY_CURL_2}}
```

---

## 快速验证命令

```bash
# 重跑当前失败测试
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-test-runner.py "{{TEST_FILE}}" --grep "{{TEST_CASE}}"

# 环境健康检查（如适用）
curl http://localhost:8080/health
curl http://localhost:3000
```
