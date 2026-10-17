# 项目运行说明模板

接入或更新项目运行入口时读取；按真实项目填写 scripts/index.md，不保留示例命令。

| 用途 | 命令 | cwd | 前置条件 | 结果位置 | 清理边界 |
| --- | --- | --- | --- | --- | --- |

涵盖已存在的构建、静态检查、测试和必要环境入口；标出没有配置或尚未验证的部分。测试选取与执行记录按 `${CLAUDE_PLUGIN_ROOT}/protocols/tests-to-run-contract.md` 和 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`。

包含 Web Demo 时，额外写明 URL、身份/数据 fixture、环境管理方式、真实启停/健康检查、日志、run ID 和整文件回归命令；从 `${CLAUDE_PLUGIN_ROOT}/protocols/web-demo-run-repair-contract.md` 读取运行契约。

测试命令只在此处维护；AGENTS.md 提供读取入口，不复制命令表。重复执行保留用户说明，仅更新受影响行。
