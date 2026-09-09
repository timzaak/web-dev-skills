# Extension 完成前验证

先从实际 package.json 确认目录、包管理器和 scripts；WXT 类型检查常为 `compile`，也可能为 `type-check`。不得假设脚本存在或用成功的构建替代类型检查。

| 检查 | 何时执行 | 成功证据 |
|---|---|---|
| 类型检查 | 实现或类型变更 | 项目等价命令退出码为 0 |
| 生产构建 | 实现、配置或权限变更 | build 成功，入口与 manifest 生成 |
| manifest 核对 | 构建后 | 实际输出（默认 `.output/chrome-mv3/manifest.json`）的权限、注入范围、入口、CSP 与设计及源码意图一致；披露增量 |
| 定向测试 | 受影响行为有测试、补测或任务要求 | 相关测试通过；缺失必要测试不能视为通过 |
| lint | 项目已有该门禁 | 使用不改写源码的检查模式 |

在扩展实际目录分别运行，例如 `npm run compile`、`npm run build`、`npm run test:run -- <相关文件>`。仅文档变更可跳过编译并说明原因。

实现 agent 修复失败项后重跑受影响检查；仍失败时返回失败原因、证据和可恢复动作，不标记完成。accept 不修代码，按 [验收协议](${CLAUDE_PLUGIN_ROOT}/protocols/extension-acceptance-contract.md) 返回判定，由编排层停止并交回对应实现/测试 item。

验收允许构建派生物和写质量报告，但不改源码、依赖声明或 lockfile，不运行 autofix。缺少必需脚本时报告门禁未完成，不临时安装工具或静默略过。
