# Extension 验收检查依据

按 [开发规范](${CLAUDE_PLUGIN_ROOT}/guides/extension/development.md) 检查受影响边界，命令按 [验证指南](${CLAUDE_PLUGIN_ROOT}/guides/extension/validation.md) 执行；输出、阻断条件和状态只由 [验收协议](${CLAUDE_PLUGIN_ROOT}/protocols/extension-acceptance-contract.md) 定义。

| 检查对象 | 可复核证据 |
|---|---|
| 设计一致性 | 需求/设计中的验收目标到变更文件、测试结果的映射；技术任务豁免遵循 core quality |
| 构建与权限 | 类型/构建退出码、生产 manifest、权限与注入范围差异及确认依据 |
| 消息 | 定义和全部消费者、接收端 schema、sender/操作范围检查、错误/超时路径 |
| worker | 监听注册位置、状态恢复和幂等路径；涉及生命周期时提供重启后行为证据 |
| 存储 | key/区域、迁移与失败处理、敏感数据访问范围、watch 清理和并发写入策略 |
| content UI | 挂载和卸载、样式/portal 隔离、权限拒绝及宿主导航后行为 |
| 回归 | 受影响单测和约定的真实浏览器路径；fakeBrowser 结果不能证明 MV3 生命周期或权限行为 |

架构审查关注行为后果；不要把集中封装内部合法使用 chrome API 判为违规。重复代码检查只在项目已有工具或变更存在明显复制时执行，限定源码并排除生成目录；报告具体重复风险，不以固定百分比代替判断。

设计前置边界读取 [core quality](${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md)。缺少插件规范时报告输入缺失，不另立降级验收清单。
