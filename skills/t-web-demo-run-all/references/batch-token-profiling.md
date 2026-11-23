# 批次 Token 去向诊断指南

> `/t-tools:t-web-demo-run-all` 跑完一轮后，用它定位 token 花在了哪、是否值得改造，再决定走哪条优化路径。本文是诊断方法，不构成跨 skill 契约。

## 为什么要先测再改

`t-web-demo-run-all` 的 token 大头不在 Playwright 输出（已重定向到文件，主会话只看一行 `Result:`），而在三处：

1. **每失败用例的 subagent dispatch 重复注入 agent 规范**。每次 `Agent` 调用（每文件最多 6 轮 × (诊断 + 修复)）都要求主会话先 Read 完整 agent 规范全文再注入子 prompt 首段，这份文本每次重发。
2. **共享根因被重复诊断**。多个文件挂在同一个失效 selector / 同一个后端接口变更上时，各自独立诊断、独立修复、独立终验，同一套证据被反复读。
3. **主会话上下文随批次时长线性增长**，文件数一多会触发上下文压缩，压缩本身也耗 token。

这三处的影响随"失败画像"不同而差异巨大。先测一次真实批次的画像，再决定是否改造，能避免过度工程。

## 怎么测：三步

### 第 1 步：从批次 JSON 读失败分布

批次产物在 `.ai/quality/web-demo-run-all-<ts>.json`。读 `entries[]`，统计：

- 总文件数（`total_files`）
- 失败文件数（`failed_files`，含修复后仍失败的）
- 修复成功数（`entries` 中 `fixed == true` 的条目数）
- 平均每文件耗时（`total_duration / total_files`）

修复成功的文件越多，说明 dispatch 注入的重复开销越大——每个 `fixed` 文件都至少经历了一次诊断 + 一次修复 dispatch。

### 第 2 步：聚合失败用例标题，判断共享根因

对每个失败或修复过的文件，读它 `run_id` 指向的失败日志：

```
demo/test-results/runs/<run_id>/playwright-output.log
```

从日志中提取失败用例标题（`✗` / `×` / `Error:` 行后面的用例名）和错误消息头。把所有文件的失败标题去重，得到：

- `failure_cases`：所有失败用例（含重复）
- `unique_failure_titles`：去重后的失败用例标题
- `unique_error_fingerprints`：按错误关键字归一化后的指纹（如 `selector not found: [data-testid="x"]`、`GET /api/foo → 404`、`timeout 30000ms exceeded`）

> 如果只想快速聚类而不手写正则，跑 `uv run scripts/web-demo-run-all.py cluster --json <json_report>`（见下文"第三档联动"）即可自动产出 `unique_clusters`。

### 第 3 步：算三个比值，对照决策树

| 指标 | 计算 | 含义 |
| --- | --- | --- |
| 根因分散度 | `unique_error_fingerprints / failure_cases` | 越接近 1 → 每个失败都是独立根因；越接近 0 → 共享根因严重 |
| 修复 dispatch 密度 | `(诊断次数 + 修复次数) / unique_error_fingerprints` | 越大 → 同一根因被重复诊断修复的次数越多，注入重复开销越重 |
| 主会话压力 | `total_files × 平均每文件 dispatch 数` | 粗估主会话累积的 Agent 调用数，超过平台上下文压缩阈值时要警惕 |

## 决策树

```
读完三步指标后：

失败文件占比低（< 20%）且 unique_error_fingerprints ≈ failure_cases
  → 孤立失败为主，token 大头在少数文件的多轮修复
  → 走第二档：优化 dispatch 注入（同批次同角色读一次、注入多次）

unique_error_fingerprints << failure_cases（如 3 个指纹对应 15 个失败用例）
  → 共享根因明显，目前各自独立诊断修复造成大量重复
  → 走第三档：预跑全量 → 批量修唯一失败（/t-tools:t-web-demo-run-all scan）

两者都不显著，或 total_files 本身就少（< 5）
  → 保持现状，当前架构已足够，改造的边际收益低于维护成本
```

## 第三档联动

当决策树指向第三档时，直接用 `/t-tools:t-web-demo-run-all scan`：它内置了预扫描 + 聚类 + 按 cluster 修复的完整流程。底层调用 `scripts/web-demo-run-all.py` 的两个无 subagent 子命令：

```bash
# 纯 Bash 逐文件跑 fast 模式，只收集 success/fail + run_id，不进修复闭环
uv run scripts/web-demo-run-all.py scan --json <json_report>

# 读取 scan 结果里的失败日志，按错误指纹聚类，输出 clusters[]
uv run scripts/web-demo-run-all.py cluster --json <json_report>
```

`cluster` 打印单行 JSON：`total_files`、`passed`、`failed`、`unique_clusters`、`clusters[]`（每项含 `fingerprint`、`representative_error`、`affected_files[]`、`affected_cases[]`）。`/t-tools:t-web-demo-run-all scan` 拿到后对每个 unique cluster 只跑一次诊断 + 修复链，再回扫所有受影响文件。

## 常见误区

- **只看失败文件数就下结论**。10 个文件全挂在同一个 selector 上（1 个根因）和 10 个文件各挂各的（10 个根因），token 量级差一个数量级，必须看指纹去重数。
- **把 `total_duration` 当 token 代理指标**。耗时长主要卡在环境重建和 Playwright 执行，这些是机器时间不花 token；真正花 token 的是 Agent dispatch 次数和重复注入的规范体积。
- **为小批次改造**。文件数 < 5 时，现有架构的编排开销可忽略，第二、三档的工程成本不划算。
