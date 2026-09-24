# Extension Demo Acceptance Contract

## 输入与输出

输入为目标 `demo/e2e/extension/**/*.e2e.ts` 文件或 `all`、设计与用户故事来源、构建命令和产物、环境模式、执行日志。只验收当前扩展演示范围，不扫描普通 Web Demo。

报告写入 `.ai/quality/extension-demo-accept-[name]-[YYYYMMDD-HHMMSS].md`；批量时另写 `extension-demo-accept-summary-[YYYYMMDD-HHMMSS].md`。报告记录结论、故事与场景映射、构建及运行命令和结果、加载产物/manifest、日志路径、隔离与清理证据、P0/P1/P2 问题及后续责任角色。结构化返回遵循 `${CLAUDE_PLUGIN_ROOT}/protocols/agent-task-output-contract.md`。

验收前按 `${CLAUDE_PLUGIN_ROOT}/protocols/verification-evidence-contract.md` 核查业务验证责任与证据复用；每次独立输出本轮验收结论，必要现场证据仍须符合本协议。

## 门禁与判定

- MANDATORY：用户故事来源存在且角色、动作、关键断言与验收目标一致；构建成功并确认 fixture 加载本次产物；整文件浏览器执行通过；profile、宿主/stub、数据清理可复核；必要现场证据完整。
- 不使用 skip、弱化断言或只检查 toast/测试 mock 来获得通过。权限、消息、存储与生命周期只要求覆盖设计和本次变更实际涉及的路径，不凭空增加全量要求。
- `REJECTED`：任一必要门禁失败或未验证，或存在影响故事结果、权限/安全边界的 P0/P1；`task_completion.status=failed`。
- `ACCEPTED_WITH_IMPROVEMENTS`：全部必要门禁通过，仅有非阻断维护性 P2；`status=success`。
- `ACCEPTED`：全部必要门禁通过且无未解决问题；`status=success`。

accept 不修改测试或业务源码；允许按目标项目现有命令生成构建/测试派生物与报告。失败后由 `extension-demo-dev` 或归因到的实现角色修复，重新构建、运行受影响用例并再次验收；每次验收保留新报告，按验证证据协议引用仍有效的运行证据或补跑结果，不沿用旧通过结论。
