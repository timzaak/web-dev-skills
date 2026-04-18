# T-Tools

面向 Rust + React 项目的 Claude Code plugin。它把 `PRD -> 设计 -> 任务 -> 开发 -> 验收 -> Demo` 串成一套可复用工作流，让你不用反复设计 prompt、切换上下文或手工维护阶段边界。

适合这类团队和项目：

- 已经有明确的产品文档、设计、任务拆解、开发、测试、Demo 交付链路
- 希望把 Claude Code 从“临时问答”升级成“可执行的工程工作流”
- 需要 sub-agent 分工、阶段门禁、标准化产物，而不是一次性自由发挥

## 为什么用它

- 上手快：直接按 `/t-*` 命令顺序推进，不需要自己设计整套提示词和协作流程
- 交付稳：关键阶段自带检查和验收命令，减少文档跑偏、任务漏拆、Demo 不可执行
- 协作清：skill、agent、guide、protocol 已分层，适合多人或长期项目持续复用

## 完整工作流

```text
/t-prd
  -> /t-prd-check
  -> /t-design
  -> /t-design-check
  -> /t-task
  -> /t-task-check
  -> /t-run
  -> /t-backend-finalize
  -> /t-demo-run
  -> /t-demo-accept
```

其中：

- `/t-prd-check` 是 PRD 与 user story 质量门禁，不是可有可无的补充命令
- `/t-demo-accept` 是 Demo 阶段验收门禁，用来确认测试覆盖、可运行性和交付质量

常见辅助命令：

- `/t-consistency-check`：复核 PRD 与实现是否一致
- `/t-demo-run-all`：批量执行 Demo 测试

## 3 分钟快速上手

前置条件：

- 已安装 `t-tools` plugin
- 目标项目具备运行时目录：`docs/`、`.ai/`
- 已启用 `context7`

最短闭环示例：

```bash
/t-tools:t-prd create user-management
/t-tools:t-prd-check user-management
/t-tools:t-design user-management
/t-tools:t-task user-management
/t-tools:t-run user-management --phase backend
/t-tools:t-demo-run super-admin
/t-tools:t-demo-accept super-admin
```

执行顺序可以这样理解：

- `/t-tools:t-prd create user-management`：先创建或补齐该功能的 PRD 与相关 user story
- `/t-tools:t-prd-check user-management`：马上做产品文档质量门禁，避免把问题带入设计阶段
- `/t-tools:t-design user-management`：基于 PRD 产出技术设计
- `/t-tools:t-task user-management`：把设计转换成可执行任务
- `/t-tools:t-run user-management --phase backend`：按阶段驱动实现与测试
- `/t-tools:t-demo-run super-admin`：运行该角色的 Demo/E2E 测试
- `/t-tools:t-demo-accept super-admin`：做最终验收，确认故事映射、编译、执行和质量要求都通过

如果你只想记住一件事：不要跳过 check / accept 阶段。这个 plugin 的价值不只是“帮你生成内容”，而是“帮你在每个阶段收口”。

## 常用入口

- 产品规范入口：[guides/product/index.md](/guides/product/index.md)
- 后端开发与门禁：[guides/backend/index.md](/guides/backend/index.md)
- 前端开发与门禁：[guides/frontend/index.md](/guides/frontend/index.md)
- Demo 测试与诊断：[guides/demo/index.md](/guides/demo/index.md)
- 跨领域总纲：[guides/core/index.md](/guides/core/index.md)
- 协议索引：[protocols/index.md](/protocols/index.md)

## 仓库边界

这是 plugin 源码仓库，不是目标业务仓库。

- 插件资源主要在 `skills/`、`agents/`、`guides/`、`protocols/`、`scripts/`
- 插件清单位于 `.claude-plugin/plugin.json`
- 目标项目运行时主要依赖 `docs/`、`.ai/`

引用插件内部文件时统一使用 `${CLAUDE_PLUGIN_ROOT}` 语义路径。根级 `README.md` 只负责说明优势、工作流和快速上手；更细的规则请进入对应 guide / protocol。

## 依赖

- `Context7`：供 `backend-dev`、`backend-test`、`frontend-dev`、`frontend-test` 查询第三方库文档
- `/simplify`：可选，用于 `t-backend-finalize` 收口审查
