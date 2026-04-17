---
name: t-demo-run-all
description: >
  批量运行所有 Demo E2E 测试（fast 模式），逐个顺序执行，失败不中断，输出汇总结果。
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Write
---

# 批量运行 Demo 测试

## Runtime Dependencies

以下路径属于目标项目运行时依赖，不是本 skill 自带资源：
- `spec/`
- `docs/`
- `.ai/`

本 skill 内部引用的插件资源应保持在 `skills/`、`agents/`、`protocols/` 下；外部路径仅表示目标项目仓库中的运行时文件。

## 目标
- 自动发现全部 Demo 测试并逐个执行。
- 默认通过 Claude CLI 调用 `/t-demo-run`，以便复用单文件运行与自动修复逻辑。
- Claude CLI 不可用时，允许回退到直接执行 `demo-test-runner.py`。
- 记录每个文件的通过/修复/失败结果。
- 生成统一汇总报告，并为后续 `demo-diagnose` 分类提供 JSON 输入。
- 支持 `continue`，从上一次批量运行的失败/中断位置继续执行。

## 使用方式
```bash
/t-demo-run-all
```

```bash
/t-demo-run-all continue
```

等价脚本入口：
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-run-all.py
```

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-run-all.py continue
```

可选回退模式：
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-run-all.py --direct-script
```

## 执行流程
1. 动态发现测试文件。
```bash
Glob: demo/e2e/**/*.e2e.ts
```
排除：`fixtures/`、`templates/`、`verification/`、文件名包含 `test-`。

2. fresh 模式从头运行；`continue` 模式读取最近一次 `demo-run-all-*.json`。
- 若存在 `current_file`，从该中断文件重跑。
- 否则从最近一个失败文件重跑，并继续其后尚未重跑的文件。
- 已确认完成的前序文件不重跑。
- 若没有可继续的批次或失败点，直接报错。

3. 按字母序逐个执行，必须串行。
默认模式：
```bash
claude -p "/t-demo-run demo/e2e/..."
```
回退模式：
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/demo-run-all.py --direct-script
```
关键规则：
- 一次只运行一个文件。
- 当前文件结束后再运行下一个。
- 失败只记录，不中断整体流程。
- 若单文件在 Claude 模式下自动修复成功，汇总中标记为 `FIXED`。
- `/t-demo-run-all` 调用脚本时，超时固定为 7200 秒（2 小时）。

4. 收集结果并生成汇总。
输出：
- `.ai/quality/demo-run-all-[YYYYMMDD-HHMMSS].md`
- `.ai/quality/demo-run-all-[YYYYMMDD-HHMMSS].json`

JSON 批次状态必须持续写盘，至少包含：
- `batch_status`
- `current_index`
- `current_file`
- `discovered_files`
- `entries`
- `updated_at`

5. 对失败文件逐个调用 `demo-diagnose` 做结构化分类。
输入建议：
- `testFile`: 失败文件路径
- `runId`: `demo-run-all` 记录的 `run_id`
- `testCaseTitle`: 需要按单用例细分时再提供

## 汇总报告
必须包含：
- 总文件数、通过文件数、修复文件数、失败文件数
- 每个文件的状态、耗时、日志路径
- `Fixed Files` 与 `Unfixed Files` 清单
- 总耗时与通过率
- 供 `demo-diagnose` 使用的 `run_id` / 日志路径

## 失败处理
- 单文件失败：标记失败并继续。
- Claude CLI 不可用：自动提示并回退到 direct script 模式。
- runner 启动失败：记录错误并继续下一个文件。
- 无可用测试文件：终止并给出明确提示。
- `continue` 找不到最近批次、批次格式无效或没有可继续内容：终止并给出明确提示。

## 质量门禁
- 不允许并行执行多个测试文件。
- 不允许使用 slow/headed 模式。
- 必须产出汇总报告。
- 不允许在批量运行前执行 cleanup。
- 默认优先复用 `/t-demo-run`，保证单文件运行协议一致。
- 推荐先批量发现失败，再用 `demo-diagnose` 分类后统一安排修复，避免天然按文件顺序逐个修。

## 相关引用
- `skills/t-demo-run/SKILL.md`
- `agents/demo-diagnose.md`
