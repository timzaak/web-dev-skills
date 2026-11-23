# Demo E2E 测试指南

用于 Demo 开发与功能验证的主入口。

## 适用范围

- 新增或修改 `demo/e2e/**/*.e2e.ts`
- 修复 Demo 测试代码问题
- 运行单文件或最小回归验证

## 核心规则

- 完整用户故事主路径优先用 Demo / E2E 覆盖。
- 业务数据优先通过 UI 创建或通过 Demo seed 预置，不在测试文件里走业务旁路。
- 路由和身份以目标项目设计与实现为准；Shopify 页面从 `shopify.md` 与 [Shopify 验证与验收规范](${CLAUDE_PLUGIN_ROOT}/guides/shopify/quality.md) 获取交付面，不套用默认 Web 登录路径。
- 选择器优先 `data-testid`、语义 role、稳定文本，不依赖脆弱 CSS。
- `sonner`、toast、Snackbar 等自动消失提示只能作为辅助反馈断言，不得作为主判断条件或唯一验收依据。
- 关键验收断言必须落在可稳定观察的结果上，例如持久业务状态、列表/详情数据、页面状态、URL、禁用态或不会自动消失的错误区域。
- 运行和清理优先使用项目脚本与统一 fixture。

## 当前目录事实

```text
demo/e2e/
├── fixtures/
├── helpers/
├── pages/
├── selectors.ts
└── *.e2e.ts
```

角色目录和文件组织以当前 `demo/e2e/` 实际结构为准，不再把旧项目目录命名当默认模板。

## 标准命令

下列示例用于默认 Web 环境。Shopify 的单文件、批量、重试与恢复读取 `${CLAUDE_PLUGIN_ROOT}/protocols/demo-run-repair-contract.md` 的 Shopify Demo 运行模式，runner 保留 `--no-auto-env`，不执行默认 Web 启停脚本。

```powershell
uv run scripts/web-demo-test-runner.py demo/e2e/[test-file].e2e.ts
uv run scripts/web-demo-test-runner.py demo/e2e/[test-file].e2e.ts --log-level verbose
uv run scripts/web-demo-run-all.py discover   # 批量入口由 /t-tools:t-web-demo-run-all 主会话驱动；脚本只辅助发现、进度写盘和汇总
uv run scripts/demo-stop.py
```

## 自检

- [ ] 测试覆盖真实用户路径
- [ ] 未使用历史模板中的旧路由示例
- [ ] 选择器可维护
- [ ] 关键验收断言不依赖自动消失的 toast/sonner 提示
- [ ] 已完成最小验证运行

## 参考

- 选择器与 POM：[`authoring.md`](${CLAUDE_PLUGIN_ROOT}/guides/web-demo/authoring.md)
- 维护与修复：[`maintenance.md`](${CLAUDE_PLUGIN_ROOT}/guides/web-demo/maintenance.md)
- 失败诊断：[`diagnose-guide.md`](${CLAUDE_PLUGIN_ROOT}/guides/web-demo/diagnose-guide.md)
- 验收门禁：[`quality.md`](${CLAUDE_PLUGIN_ROOT}/guides/web-demo/quality.md)
