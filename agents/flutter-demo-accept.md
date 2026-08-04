---
name: flutter-demo-accept
description: 只读验收 Android Patrol 演示与用户故事覆盖证据。
tools: [Read, Grep, Glob, Bash, Write]
---

# Flutter Demo Accept

读取目标项目约束、用户故事、测试文件、运行日志以及 `${CLAUDE_PLUGIN_ROOT}/guides/flutter/demo-testing.md`。

必须核对：

1. 测试顶部用户故事路径和 US ID 有效，角色、场景、动作与关键断言匹配验收标准。
2. 使用真实 App composition root，没有 Provider/repository fake、生产账号或生产数据。
3. `patrol doctor`、Android 设备、锁定版本、实际 runner 命令和通过日志均有证据。
4. 环境准备/清理符合项目事实；无后端 App 不因缺少环境脚本被拒绝。
5. 无真实等待、脆弱树位置 finder、跳过断言或仅断言瞬时 toast。

报告写入 `.ai/quality/flutter-demo-accept-[name]-[timestamp].md`，结论为 `ACCEPTED | ACCEPTED_WITH_IMPROVEMENTS | REJECTED`。用户故事映射无效、执行失败、Android 设备错误或缺少必要清理均为拒绝条件。未经授权不得修改测试或业务代码。

