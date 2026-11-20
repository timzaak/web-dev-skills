# Doc Anchor 契约

`t-anchor` 锚点是已发布需求文档声明与目标代码区域之间的机械可验证链接：文档记录代码位置和内容哈希，脚本用确定性校验替代 LLM 复核，检出漂移时零误报。

## 锚点语法

单行 HTML 注释，放在被锚定声明的紧邻位置：

```
<!-- t-anchor: id=<slug> | <repo相对路径>:<起行>-<止行> | sha256=<64位hex> -->
```

- `id` 在单文档内唯一，kebab-case。
- 目标路径必须是项目根内的相对路径，使用 `/` 分隔；拒绝绝对路径、反斜杠和 `..` 越界路径。
- 起止行为 1 起始的闭区间，止行不小于起行。
- 锚点是机器验证元数据，不参与正文渲染，不计入"PRD 禁止代码文件路径"的分层规则。

## 哈希规范化

为保证跨平台确定性，哈希输入按以下规则规范化：

1. 取目标文件起..止行（含）。
2. CRLF 和孤立 CR 统一为 LF。
3. 去除每行行尾空格和制表符。
4. 以 `\n` 连接各行后按 UTF-8 编码，取 SHA-256 hexdigest（64 位小写）。

哈希一律由脚本 `print` 子命令计算生成，不得手写或由 LLM 心算。

## 校验状态

| 状态 | 含义 | 处理 |
| --- | --- | --- |
| `ok` | 范围内内容哈希匹配 | 证据链成立，声明有实现支撑 |
| `moved` | 内容在目标文件其他位置找到，行号漂移 | 观察项；提示锚点行号待更新，不是漂移结论 |
| `drifted` | 文件存在但锚定内容已不存在 | 强漂移信号；修正文档、修正实现或产品确认由调用方裁决 |
| `missing-file` | 目标文件不存在 | 强漂移信号；同上 |
| `invalid` | 语法、id 重复、路径越界或范围非法 | 修正锚点本身 |

无锚点的文档不构成任何问题；锚点缺失只作为治理建议中的回填推荐。

## 宿主与写入责任

- 长期宿主是已发布需求文档：`docs/prd/**/*.md`、`docs/user-stories/**/*.md`。
- `.ai/**` 是实现后可删除的工作流产物，不承诺锚点存活；任何调用方不对 `.ai/` 锚点下治理结论。
- PRD 草稿（`.ai/prd`）默认不带锚点：写作时代码可能尚不存在。锚点回填属于发布后治理动作，依据实现事实生成。
- `t-dream` 只读审计：可在报告中输出建议锚点行（由脚本算好哈希），写入由用户确认后另行执行。

## 脚本契约

`${CLAUDE_PLUGIN_ROOT}/scripts/check-doc-anchors.py`，按 `${CLAUDE_PLUGIN_ROOT}/protocols/runtime-boundaries.md` 的脚本入口规则调用（目标项目 `scripts/check-doc-anchors.py` 优先，插件脚本回退）。

- `verify <docs...> --project-root <根> [--json]`：校验文档内全部锚点。JSON 输出 `{status, anchor_count, moved_count, anchors:[{id, source, line, target, start, end, status}], finding_count, findings:[{code, source, message, line}]}`；`status` 为 `failed` 当且仅当存在 findings。退出码：有 findings 为 1，否则为 0。
- findings 只包含 `INVALID_ANCHOR_SYNTAX`、`DUPLICATE_ANCHOR_ID`、`INVALID_TARGET_PATH`、`INVALID_ANCHOR_RANGE`、`MISSING_TARGET_FILE`、`ANCHOR_DRIFTED`、`DOC_NOT_FOUND`；`moved` 只计入 `anchors` 与 `moved_count`，不影响退出码。
- `print <path> <start> <end> --id <slug> --project-root <根>`：输出可直接粘贴的锚点行；路径、范围非法时退出码 1 并写 `ERROR:` 到 stderr。

## 调用方

- `t-dream`：对检查范围内的已发布文档运行 `verify`，结果注入共享上下文包；`drifted` / `missing-file` 按已验证证据进入候选问题（验证方式: 脚本），消费规则见 `${CLAUDE_PLUGIN_ROOT}/protocols/dream-report-contract.md`。
- PRD 分层例外：锚点注释不受 `guides/product/prd.md` 禁止项"具体代码文件路径列表"约束，见该规范与 `protocols/prd-check-rubric.md` 的对应条目。
