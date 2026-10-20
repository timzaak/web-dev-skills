# Extension Demo Acceptance Contract

验收前读取 `${CLAUDE_PLUGIN_ROOT}/protocols/acceptance-contract.md`，公共输入、报告、结构化返回、分级、结论与只读边界以其为准。本协议补充扩展故事门禁。

## 输入与范围

输入为目标 `demo/e2e/extension/**/*.e2e.ts` 文件或 `all`、设计与用户故事来源、构建命令和产物、环境模式、执行日志。只验收当前扩展演示范围，不扫描普通 Web Demo。

`demo/e2e/extension/verification/` 保留给初始化基础设施验证，不属于用户故事演示。故事验收的 `all` 扫描排除此目录，显式传入时提示使用初始化验证入口；不将其判为故事 ACCEPTED 或为其编造故事映射。排除后没有故事用例时报告“无可验收用户故事”，不报告验收通过。批次发现复用 runner 已有的 verification 目录排除规则，初始化流程直接定向执行其中的 smoke。

报告额外记录故事/场景映射、实际加载产物/manifest、fixture 环境模式及隔离/清理证据。故事追溯按 `${CLAUDE_PLUGIN_ROOT}/protocols/requirement-source-contract.md` 的 Story Traceability。

## 专项门禁

- MANDATORY：用户故事来源存在且角色、动作、关键断言与验收目标一致；构建成功并确认 fixture 加载本次产物；整文件浏览器执行通过；profile、宿主/stub、数据清理可复核；必要现场证据完整。
- 不使用 skip、弱化断言或只检查 toast/测试 mock 来获得通过。权限、消息、存储与生命周期只要求覆盖设计和本次变更实际涉及的路径，不凭空增加全量要求。

## 恢复与交接

失败交回 extension-demo-dev 或归因到的实现角色修复，重新构建并验证当前加载产物，运行受影响用例和必要整文件终验后重新验收。必要现场证据按 `${CLAUDE_PLUGIN_ROOT}/protocols/extension-acceptance-contract.md`；公共证据复用、报告保留及状态消费不在此重复定义。
