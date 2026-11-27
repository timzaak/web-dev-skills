# Extension 验证与验收规范

按 [开发规范](${CLAUDE_PLUGIN_ROOT}/guides/extension/development.md) 检查受影响边界；公共输出、阻断条件和状态只由 [公共验收协议](${CLAUDE_PLUGIN_ROOT}/protocols/acceptance-contract.md) 定义，现场与扩展故事专项规则按 [扩展验收协议](${CLAUDE_PLUGIN_ROOT}/protocols/extension-acceptance-contract.md) 定义。设计前置边界读取 [core quality](${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md)。

## 1. 完成前验证

先从实际 package.json 确认目录、包管理器和 scripts；WXT 类型检查常为 `compile`，也可能为 `type-check`。不得假设脚本存在或用成功的构建替代类型检查。

| 检查 | 何时执行 | 成功证据 |
|---|---|---|
| 类型检查 | 实现或类型变更 | 项目等价命令退出码为 0 |
| 生产构建 | 实现、配置或权限变更 | build 成功，入口与 manifest 生成 |
| manifest 核对 | 构建后 | 实际输出（默认 `.output/chrome-mv3/manifest.json`）的权限、注入范围、入口、CSP 与设计及源码意图一致；披露增量 |
| 定向测试 | 受影响行为有测试、补测或任务要求 | 相关测试通过；缺失必要测试不能视为通过 |
| 用户浏览器现场 | 按 [验收协议](${CLAUDE_PLUGIN_ROOT}/protocols/extension-acceptance-contract.md) 判断适用性 | 协议要求的本次现场证据完整，修复后已核对实际加载产物及行为 |
| lint | 项目已有该门禁 | 使用不改写源码的检查模式 |

在扩展实际目录分别运行，例如 `npm run compile`、`npm run build`、`npm run test:run -- <相关文件>`。仅文档变更可跳过编译并说明原因。

实现 agent 修复失败项后重跑受影响检查；仍失败时返回失败原因、证据和可恢复动作，不标记完成。accept 不修代码，按 [验收协议](${CLAUDE_PLUGIN_ROOT}/protocols/extension-acceptance-contract.md) 返回判定，由编排层停止并交回对应实现/测试 item。

验收允许构建派生物和写质量报告，但不改源码、依赖声明或 lockfile，不运行 autofix。缺少必需脚本时报告门禁未完成，不临时安装工具或静默略过。

## 2. 验收检查依据（extension-accept）

| 检查对象 | 可复核证据 |
|---|---|
| 设计一致性 | 需求/设计中的验收目标到变更文件、测试结果的映射；技术任务豁免遵循 core quality |
| 构建与权限 | 类型/构建退出码、生产 manifest、权限与注入范围差异及确认依据 |
| 消息 | 定义和全部消费者、接收端 schema、sender/操作范围检查、错误/超时路径 |
| worker | 监听注册位置、状态恢复和幂等路径；涉及生命周期时提供重启后行为证据 |
| 存储 | key/区域、迁移与失败处理、敏感数据访问范围、watch 清理和并发写入策略 |
| content UI | 挂载和卸载、样式/portal 隔离、权限拒绝及宿主导航后行为 |
| 回归 | 受影响单测和约定的真实浏览器路径；fakeBrowser 结果不能证明 MV3 生命周期或权限行为 |

架构审查关注行为后果；不要把集中封装内部合法使用 chrome API 判为违规。重复代码检查的触发、范围和证据遵循公共验收协议。缺少插件规范时报告输入缺失，不另立降级验收清单。
