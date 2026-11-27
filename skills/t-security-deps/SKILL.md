---
name: t-security-deps
description: Scan the target project's dependency manifests for known CVEs with containerized Trivy (Node/npm, Rust/cargo, Java/Maven/Gradle and other Trivy ecosystems), then write an evidence-backed report with a per-ecosystem upgrade plan. Use when the user asks about dependency vulnerabilities, CVEs, safe versions, or supply-chain risk of the current project, even without naming this command. Read-only scan plus plan; code-level security review belongs to t-review.
argument-hint: "[<target>（可选：项目路径，默认当前项目）]"
allowed-tools:
  - Read
  - Glob
  - Bash
  - Write
---

# 依赖 CVE 扫描与修复方案

`前置校验 → security-deps-scan.py 容器化 Trivy 扫描 → 修复方案报告（全程只读）`

运行时边界：`${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md`（脚本入口或项目事实与插件默认冲突时读）

## 目标与边界

- 确认依赖中已知 CVE（Trivy 支持的 npm/yarn/pnpm/bun、cargo、Maven/Gradle、go、pip 等），按严重度与生态归类，证据取自扫描 JSON。
- 报告写入 `.ai/quality/security-deps-[YYYYMMDD-HHMMSS].md`；不修改依赖清单、锁文件或任何项目文件。升级由用户确认方案后另行执行，升级后重跑本命令复核。

## 扫描执行

1. 按运行时边界 Script Entry Rules 选择入口：目标项目存在 `scripts/security-deps-scan.py` 时用项目脚本，否则 `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/security-deps-scan.py`；项目脚本失败时报告原因，不得用插件脚本绕过。
2. 命令形态（文件名、参数、JSON 输出、退出码是稳定契约；镜像与缓存目录可被项目覆盖）：

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/security-deps-scan.py scan <target> --json \
  [--severity HIGH,CRITICAL] [--image aquasec/trivy:0.68.1] [--cache-dir <dir>]
```

3. JSON 关键字段：`status`（passed/failed/error）、`manifests[].{path,ecosystem}`、`vulnerabilities[].{id,severity,package,installed,fixed,ecosystem,manifest,url}`、`by_severity`、`findings[].{code,message}`。`fixed` 为 null 表示上游暂无修复版本。
4. 退出码：`0` 通过；`2` 有漏洞（正常产出，继续写报告）；`1` 执行失败（看 findings）。目标目录只读挂载，脚本不执行项目内代码；首跑下载漏洞库较慢，缓存后秒级。

## 修复方案规则

1. 有 `fixed`：给最小安全版本和该生态升级命令（npm 系 `npm|pnpm|yarn install <pkg>@<fixed>`；cargo `cargo update -p <pkg> --precise <fixed>`；Maven/Gradle 改版本属性或 BOM）；传递依赖无法直接指定时给 lockfile override 并标注是兜底。多分支 `fixed`（如 `2.8.11, 2.9.4`）取当前线最小安全版本，禁止降级；当前线无修复时推荐最近有修复的线并按跨 major 处理；约束式（如 `>=4.17.19`）给最小满足的具体版本。
2. `fixed` 为 null：标记"暂无修复版本"，只给缓解建议（评估暴露面、关注公告、必要时替换依赖），不得编造升级目标。
3. 跨 major 标注破坏性变更风险；lockstep 对等依赖（如 `react`/`react-dom`、同一 BOM 内组件）成组升级。
4. CRITICAL 优先于 HIGH，再按生态分组；低于阈值的不逐条展开，报告注明阈值。

## 报告

必须使用以下模板，raw JSON 同目录留存 `security-deps-[同时间戳].json` 供复核；重复执行生成新报告：

```markdown
# 依赖 CVE 扫描报告
## 摘要
（target、镜像、severity 阈值、漏洞总数、各严重度计数、涉及生态）
## 风险概览
（严重度 × 生态 汇总表）
## 发现明细
（每条：CVE / severity / 包 / 当前版本 → 修复版本 / 生态 / 清单 / 公告链接）
## 修复方案
（按生态分组：升级命令、成组升级项、major 风险、暂无修复版本项的缓解建议）
## 复核
（重跑本命令验证清零；raw JSON 位置）
```

## 错误处理

| 错误码 | 触发条件 | 用户可见提示 | 恢复动作 |
|---|---|---|---|
| `NO_DOCKER` | Docker 不可用 | 无法运行容器化扫描 | 启动 Docker 后重跑 |
| `NO_MANIFEST` | 目标内无可扫描的依赖清单/锁文件 | 没有可扫描的依赖清单 | 确认路径或先生成锁文件 |
| `SCAN_FAILED` | Trivy 非零退出或输出不可解析 | 扫描执行失败（附 stderr 摘要） | 按 stderr 修复环境后重跑；不得换镜像版本静默重试 |
| `REPORT_WRITE_FAILED` | 报告写入失败 | 报告写入失败 | 保留扫描 JSON，恢复可写后从报告写入重试 |

## Forbidden

- 修改依赖清单、锁文件或任何项目文件；在容器内执行目标项目代码或包管理器。
- 把 `fixed` 为 null 的漏洞写成"升级即可解决"，或补写扫描结果中不存在的 CVE。
- 略过 JSON 中任何超阈值发现。
