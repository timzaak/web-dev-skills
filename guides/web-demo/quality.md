# Web Demo 验收依据

验收前读取 `${CLAUDE_PLUGIN_ROOT}/protocols/acceptance-contract.md`；公共分级、结论、报告和结构化返回以该协议为准。本页只定义 Web 页面 Demo 的检查对象，扩展故事使用 extension-demo 协议。

## 故事与必要场景

按 `${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md` 的 Story Traceability 确认故事真实来源和 US ID，核对角色、动作及关键验收目标；发布前允许 draft，交付代码注释不写临时路径或虚构正式路径。

从本轮故事验收目标、改动风险和上游验证责任表列出必要场景，逐项映射测试及关键断言、实际结果与证据。批量时汇总场景，不因单文件只覆盖故事的一部分误算整故事覆盖率；文件范围外的必要场景必须有有效证据或按验证证据协议明确承接。最终收口不能留有未验证必要场景，不用平均覆盖率或主观总分放行。

## 编译与整文件运行

从目标项目 `demo/package.json` 和 `scripts/index.md` 确认真正入口；优先类型检查，只有存在 build 脚本且适用时才使用 build。Shopify 初始化的 Demo 使用 `cd demo && npm run type-check`。

缺失或失效证据时，使用项目 runner 补跑相关整文件，例如：

```bash
uv run scripts/web-demo-test-runner.py "<test-file>" --mode fast --log-level mini
```

Shopify 执行/恢复前读 `${CLAUDE_PLUGIN_ROOT}/protocols/web-demo-run-repair-contract.md` 的 Shopify 模式；命令追加 `--no-auto-env` 并核查该模式的隔离和清理。普通项目按真实环境模式执行，不能照抄不适用的启停命令。

核对退出码、实际用例、失败/超时/跳过、日志与加载产物；必要场景跳过或零用例不能算通过。定向 grep 通过不能替代整文件终验。有效整文件证据可复用，不重复启动环境。

## 隔离、数据与断言

- 核查 `verifyTestEnvironment()` 和清理函数或项目等价封装的实际效果；清理覆盖本轮创建的数据和环境。
- 使用统一 `demoLogger` fixture，测试不绕过 fixture 手工初始化或 finalize logger；不靠文件中出现特定 logger 字符串证明接入。
- 业务数据使用 Demo Seed 或用户端 UI；不使用 `api-test-data.helpers.ts`、`db-test-data.helpers.ts`、`subscription-creation.helpers.ts` 绕过业务路径。非 admin 故事不绕到管理端 UI 准备数据；设计声明的 Shopify admin 故事可操作管理端 UI，隔离按 Shopify 模式。
- 主断言验证持久业务/页面状态、URL、列表/详情数据或稳定错误区域。toast、Snackbar 等瞬时提示只能作辅助，不能作为唯一或主要结果。
- 等待条件必须对应可观察状态，检查固定延迟及超时是否掩盖竞态；网络等待先注册 Promise 再触发。
- 选择器和 POM 变更分别按 `${CLAUDE_PLUGIN_ROOT}/guides/web-demo/selector-strategy.md`、`${CLAUDE_PLUGIN_ROOT}/guides/web-demo/pom-guide.md` 检查；重复代码按公共协议限定范围。

必要故事映射、类型检查、整文件执行、隔离/清理、日志和关键断言均为门禁，缺失或失败不能以代码质量分数抵消。
