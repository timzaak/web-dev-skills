# Backend 规范入口

backend 规范入口，按“先看架构事实，再进入测试/验证/验收细页”使用。

| 你要确认的问题 | 对应规范 |
| --- | --- |
| 当前 backend 架构事实、crate 边界、依赖方向与默认实现约束 | [development.md](/guides/backend/development.md) |
| TDD 节奏、单元/模块测试补法与实现期测试边界 | [tdd-workflow.md](/guides/backend/tdd-workflow.md) |
| 场景测试、集成测试和测试命令入口 | [testing.md](/guides/backend/testing.md) |
| 完成前最小验证命令与升级顺序 | [validation.md](/guides/backend/validation.md) |
| 只读验收门禁、拒绝条件与报告要求 | [quality.md](/guides/backend/quality.md) |
| Calibration 模式输出与代码示例校准规则 | [calibration-mode.md](/guides/backend/calibration-mode.md) |

## 使用规则

- `development.md` 是 backend 的事实型主规范，其他页面不应重复定义第二套架构真相。
- `tdd-workflow.md` 和 `testing.md` 负责测试 how-to；不要在 agent 文档里再抄一遍测试教程。
- `validation.md` 只定义验证顺序与升级策略，不替代验收结论。
- `quality.md` 只定义验收门禁和报告要求，不重新发明实现规范。
