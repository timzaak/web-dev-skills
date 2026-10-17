# Web Demo 失败诊断

诊断前读取 `${CLAUDE_PLUGIN_ROOT}/protocols/diagnostic-report-contract.md`，分类与报告结构只在该协议维护。

从真实失败 run 的 playwright-output.log 开始，关联截图/trace、统一日志、失败用例和目标项目实现；项目服务日志位置从 scripts/index.md 取得。缺少运行证据时降低置信度，不能凭历史经验判生产缺陷。

区分测试资产、项目实现、身份/数据与环境失败。报告明确失败事实、根因证据、最小修复入口和定向回归；不修改任何代码，也不自行推进流程或调用修复角色。

报告落 `.ai/diagnose/`，骨架见 `${CLAUDE_PLUGIN_ROOT}/guides/web-demo/templates/diagnose-report-template.md`。编排层按 `${CLAUDE_PLUGIN_ROOT}/protocols/web-demo-run-repair-contract.md` 分发修复与补测。
