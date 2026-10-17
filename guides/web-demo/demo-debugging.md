# Web Demo 调试

适用 project-dev、web-demo-dev 与诊断角色。先读取 `${CLAUDE_PLUGIN_ROOT}/protocols/web-demo-run-repair-contract.md` 与目标项目 scripts/index.md，确认实际 URL、环境、日志和测试命令。

用失败 run 的 playwright-output.log、截图、trace 与统一日志复原操作；接口相关问题关联请求与项目真实服务日志。测试资产问题由 web-demo-dev 修复，生产实现交 project-dev；分类与推荐角色来自 `${CLAUDE_PLUGIN_ROOT}/protocols/diagnostic-report-contract.md`。

不通过忽略失败、放宽权限或弱化断言修复。修复后先运行受影响项目的定向验证，确认应用加载新实现，再执行失败用例及整文件终验。隔离和清理按项目入口，不预设数据库、目录或启动命令。
