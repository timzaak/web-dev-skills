# Java 后端模板

从 origin/java 82546bf 提取 Java/Spring Boot/Maven 后端角色、最佳实践与测试/验收规范，包含 Java 后端启动/构建/测试适配、初始化/设计模板，以及该分支为 Java 修改的调用方。导出时带上 java 固定版本的完整配套运行时；其旧版阶段/状态行为以导出后的说明为准，不回写 general 主链路。

来源分支：`java`；固定提交：`82546bff68e50acd3f8b3eaf7b2959d8993a2565`。来源文件清单与版本在 [template.json](template.json)，原始内容在 files/。

从仓库根目录运行 `python scripts/export-template.py export java-backend --output <仓库外的新目录>`；可先加 --dry-run。完整拉取、运行、兼容边界和重复执行规则见[模板入口](/templates/index.md)。

## 领域资源导航

### agents

- [agents/backend-accept.md](files/agents/backend-accept.md)
- [agents/backend-consistency.md](files/agents/backend-consistency.md)
- [agents/backend-design.md](files/agents/backend-design.md)
- [agents/backend-dev.md](files/agents/backend-dev.md)
- [agents/backend-test.md](files/agents/backend-test.md)

### guides

- [guides/backend/calibration-mode.md](files/guides/backend/calibration-mode.md)
- [guides/backend/development.md](files/guides/backend/development.md)
- [guides/backend/index.md](files/guides/backend/index.md)
- [guides/backend/quality.md](files/guides/backend/quality.md)
- [guides/backend/tdd-workflow.md](files/guides/backend/tdd-workflow.md)
- [guides/backend/testing.md](files/guides/backend/testing.md)
- [guides/backend/validation.md](files/guides/backend/validation.md)
- [guides/core/environment-and-testing-guide.md](files/guides/core/environment-and-testing-guide.md)
- [guides/product/prd.md](files/guides/product/prd.md)
- [guides/web-demo/demo-debugging.md](files/guides/web-demo/demo-debugging.md)

### protocols

- [protocols/backend-test-execution.md](files/protocols/backend-test-execution.md)
- [protocols/dream-report-contract.md](files/protocols/dream-report-contract.md)
- [protocols/task-phase-execution.md](files/protocols/task-phase-execution.md)
- [protocols/tests-to-run-contract.md](files/protocols/tests-to-run-contract.md)

### skills

- [skills/t-design/template-backend.md](files/skills/t-design/template-backend.md)
- [skills/t-doc/SKILL.md](files/skills/t-doc/SKILL.md)
- [skills/t-doc/references/doc-templates.md](files/skills/t-doc/references/doc-templates.md)
- [skills/t-init/SKILL.md](files/skills/t-init/SKILL.md)
- [skills/t-init/references/backend-template.md](files/skills/t-init/references/backend-template.md)
- [skills/t-init/references/demo-template.md](files/skills/t-init/references/demo-template.md)
- [skills/t-init/references/frontend-template.md](files/skills/t-init/references/frontend-template.md)
- [skills/t-init/references/output-checklist.md](files/skills/t-init/references/output-checklist.md)
- [skills/t-init/references/scripts-template.md](files/skills/t-init/references/scripts-template.md)
- [skills/t-init/references/subagent-prompts.md](files/skills/t-init/references/subagent-prompts.md)
- [skills/t-prd/SKILL.md](files/skills/t-prd/SKILL.md)
- [skills/t-push/SKILL.md](files/skills/t-push/SKILL.md)
- [skills/t-task-check/SKILL.md](files/skills/t-task-check/SKILL.md)
- [skills/t-tech-research/SKILL.md](files/skills/t-tech-research/SKILL.md)
- [skills/t-tech-research/template.md](files/skills/t-tech-research/template.md)

## 脚本与其他资产

完整名单以 template.json 的 source_paths 为准；脚本原文件位于 files/scripts/，导出后在独立插件的 scripts/ 使用。原有测试随对应模板保留，新增修改须在导出运行时验证。
