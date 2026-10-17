# Demo Result Contract

Web Demo runner以最后一行 `Result: {json}` 交付机器可解析结果。

必填字段：`success`, `fixed`, `logs`, `exitCode`, `testFile`, `runId`, `duration`, `error`。`success` 与 `fixed` 使用字符串 `"true" | "false"` 保持现有调用兼容；编排层统一映射 `exitCode/testFile/runId` 为 `exit_code/test_file/run_id`。

可追加 `grep/mode`。日志路径始终使用目标仓库相对路径。
