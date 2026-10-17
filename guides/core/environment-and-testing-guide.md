# 环境与验证入口

执行前读取目标项目 AGENTS.md、scripts/index.md（存在时）、构建/测试配置和 CI，取得真实命令、工作目录、依赖、输出位置与清理边界。项目已有入口失败时报告并修复，不用插件默认技术栈绕过。

按受影响行为选择最小可靠验证范围；只有范围不足或明确门禁要求才升级全量并说明原因。静态检查与运行验证分开记录；零用例和未运行均不算通过。跨阶段承接按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md`。

Web Demo 的资产、选择器与运行细则按 `${CLAUDE_PLUGIN_ROOT}/guides/web-demo/index.md`。环境由目标项目本地 scripts/demo-start.py、demo-health.py、demo-stop.py（健康/启停退出码 0 为成功）或 fixture 管理；fixture 或外部环境使用 --no-auto-env。插件不提供数据库、服务端或应用启动默认方案。
