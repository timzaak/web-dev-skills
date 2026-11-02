# pi 验收检查依据

按 [开发规范](${CLAUDE_PLUGIN_ROOT}/guides/pi/development.md) 检查受影响边界，命令按 [验证指南](${CLAUDE_PLUGIN_ROOT}/guides/pi/validation.md) 执行；公共输出、阻断条件和状态只由 [公共验收协议](${CLAUDE_PLUGIN_ROOT}/protocols/acceptance-contract.md) 定义。

| 检查对象 | 可复核证据 |
|---|---|
| 设计一致性 | 设计中的工具契约、命令、事件钩子、状态模型到变更文件与冒烟结果的映射；技术任务豁免遵循 core quality |
| 类型与加载 | 类型检查退出码；加载诊断无错误与告警；清单资源全部被发现 |
| 工具契约 | schema 与设计一致；`promptGuidelines` 点名工具；无界输出已用 `truncateHead` / `truncateTail` 截断并告知位置；错误用抛错或 `isError`；嵌套模型调用上报 `usage` |
| 并发与文件 | 改文件工具的整个读改写窗口在 `withFileMutationQueue` 内；共享内存态工具为 `sequential` |
| 生命周期 | 工厂内无进程、socket、watcher、定时器；`session_shutdown` 幂等清理；`withSession` 未复用旧 ctx |
| 事件钩子 | `continue: true` 有守卫；安全门 fail closed；系统提示修改走 `systemPromptOptions`，整体替换有设计依据；`context_with_system` 保留索引 0 的 system message |
| 状态 | 状态存 `details` 并从 `getBranch()` 重建；非模型数据用 `appendEntry` |
| UI 与模式 | 对话 UI 前核对 `ctx.hasUI`；`custom()` 与组件工厂限 `tui`；print / json 下逻辑不依赖 UI 返回值 |
| 权限与安全 | 设计要求的权限门存在且阻断路径有证据；未静默放宽 project trust；无远程代码加载 |
| 清单与依赖 | host 包只在 `peerDependencies`；运行时依赖精确版本；`keywords` 与清单路径与设计一致 |
| Skills | frontmatter 符合 Agent Skills 规范；仅手动触发的 skill 设 `disable-model-invocation`；行为验证证据按 [skill-testing](${CLAUDE_PLUGIN_ROOT}/guides/core/skill-testing.md) |
| 回归 | 受影响 Vitest 与约定的运行时冒烟；fake 结果不能证明事件顺序、并行调度或 TUI 行为 |

架构审查关注行为后果；不要把集中封装内部合法使用 pi API 判为违规。重复代码检查的触发、范围和证据遵循公共验收协议。

设计前置边界读取 [core quality](${CLAUDE_PLUGIN_ROOT}/guides/core/quality.md)。缺少插件规范时报告输入缺失，不另立降级验收清单。
