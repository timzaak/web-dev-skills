# 原生产领域模板

保留从 main 0221a41 泛化时移除的资源：Rust 后端、React 前端、Chrome 扩展、小程序、Flutter、Shopify，以及相关角色、开发/测试/验收指南、脚本和初始化/设计模板。Web Demo/Figma 已在通用插件保留；导出的运行时使用来源版本配套实现。

来源分支：`main`；固定提交：`0221a413be1e1d41ac073e5b9bf1dfa077caa41e`。来源文件清单与版本在 [template.json](template.json)，原始内容在 files/。

从仓库根目录运行 `python scripts/export-template.py export classic-stack --output <仓库外的新目录>`；可先加 --dry-run。完整拉取、运行、兼容边界和重复执行规则见[模板入口](/templates/index.md)。

## 领域资源导航

### agents

- [agents/backend-accept.md](files/agents/backend-accept.md)
- [agents/backend-consistency.md](files/agents/backend-consistency.md)
- [agents/backend-design.md](files/agents/backend-design.md)
- [agents/backend-dev.md](files/agents/backend-dev.md)
- [agents/backend-test.md](files/agents/backend-test.md)
- [agents/extension-accept.md](files/agents/extension-accept.md)
- [agents/extension-demo-accept.md](files/agents/extension-demo-accept.md)
- [agents/extension-demo-dev.md](files/agents/extension-demo-dev.md)
- [agents/extension-demo-diagnose.md](files/agents/extension-demo-diagnose.md)
- [agents/extension-design.md](files/agents/extension-design.md)
- [agents/extension-dev.md](files/agents/extension-dev.md)
- [agents/extension-test.md](files/agents/extension-test.md)
- [agents/flutter-accept.md](files/agents/flutter-accept.md)
- [agents/flutter-demo-accept.md](files/agents/flutter-demo-accept.md)
- [agents/flutter-demo-dev.md](files/agents/flutter-demo-dev.md)
- [agents/flutter-demo-diagnose.md](files/agents/flutter-demo-diagnose.md)
- [agents/flutter-design.md](files/agents/flutter-design.md)
- [agents/flutter-dev.md](files/agents/flutter-dev.md)
- [agents/flutter-test.md](files/agents/flutter-test.md)
- [agents/frontend-accept.md](files/agents/frontend-accept.md)
- [agents/frontend-design.md](files/agents/frontend-design.md)
- [agents/frontend-dev.md](files/agents/frontend-dev.md)
- [agents/frontend-test.md](files/agents/frontend-test.md)
- [agents/miniapp-accept.md](files/agents/miniapp-accept.md)
- [agents/miniapp-dev.md](files/agents/miniapp-dev.md)
- [agents/miniapp-test.md](files/agents/miniapp-test.md)
- [agents/shopify-accept.md](files/agents/shopify-accept.md)
- [agents/shopify-design.md](files/agents/shopify-design.md)
- [agents/shopify-dev.md](files/agents/shopify-dev.md)
- [agents/shopify-test.md](files/agents/shopify-test.md)

### guides

- [guides/backend/calibration-mode.md](files/guides/backend/calibration-mode.md)
- [guides/backend/development.md](files/guides/backend/development.md)
- [guides/backend/index.md](files/guides/backend/index.md)
- [guides/backend/quality.md](files/guides/backend/quality.md)
- [guides/backend/tdd-workflow.md](files/guides/backend/tdd-workflow.md)
- [guides/backend/testing.md](files/guides/backend/testing.md)
- [guides/backend/validation.md](files/guides/backend/validation.md)
- [guides/extension/demo-testing.md](files/guides/extension/demo-testing.md)
- [guides/extension/development.md](files/guides/extension/development.md)
- [guides/extension/index.md](files/guides/extension/index.md)
- [guides/extension/initialization.md](files/guides/extension/initialization.md)
- [guides/extension/live-browser.md](files/guides/extension/live-browser.md)
- [guides/extension/quality.md](files/guides/extension/quality.md)
- [guides/extension/testing.md](files/guides/extension/testing.md)
- [guides/extension/validation.md](files/guides/extension/validation.md)
- [guides/flutter/constitution.md](files/guides/flutter/constitution.md)
- [guides/flutter/demo-testing.md](files/guides/flutter/demo-testing.md)
- [guides/flutter/development.md](files/guides/flutter/development.md)
- [guides/flutter/index.md](files/guides/flutter/index.md)
- [guides/flutter/integration-testing.md](files/guides/flutter/integration-testing.md)
- [guides/flutter/patrol-initialization.md](files/guides/flutter/patrol-initialization.md)
- [guides/flutter/patterns.md](files/guides/flutter/patterns.md)
- [guides/flutter/quality.md](files/guides/flutter/quality.md)
- [guides/flutter/testing.md](files/guides/flutter/testing.md)
- [guides/flutter/validation.md](files/guides/flutter/validation.md)
- [guides/frontend/development.md](files/guides/frontend/development.md)
- [guides/frontend/index.md](files/guides/frontend/index.md)
- [guides/frontend/patterns.md](files/guides/frontend/patterns.md)
- [guides/frontend/quality.md](files/guides/frontend/quality.md)
- [guides/frontend/testid-standards.md](files/guides/frontend/testid-standards.md)
- [guides/frontend/testing.md](files/guides/frontend/testing.md)
- [guides/frontend/ui-decisions.md](files/guides/frontend/ui-decisions.md)
- [guides/frontend/validation.md](files/guides/frontend/validation.md)
- [guides/miniapp/ai-rules.md](files/guides/miniapp/ai-rules.md)
- [guides/miniapp/constitution.md](files/guides/miniapp/constitution.md)
- [guides/miniapp/development.md](files/guides/miniapp/development.md)
- [guides/miniapp/index.md](files/guides/miniapp/index.md)
- [guides/miniapp/quality.md](files/guides/miniapp/quality.md)
- [guides/miniapp/testing.md](files/guides/miniapp/testing.md)
- [guides/miniapp/validation.md](files/guides/miniapp/validation.md)
- [guides/shopify/development.md](files/guides/shopify/development.md)
- [guides/shopify/environment.md](files/guides/shopify/environment.md)
- [guides/shopify/index.md](files/guides/shopify/index.md)
- [guides/shopify/quality.md](files/guides/shopify/quality.md)
- [guides/shopify/testing.md](files/guides/shopify/testing.md)
- [guides/shopify/validation.md](files/guides/shopify/validation.md)
- [guides/web-demo/shopify-embedded-app.md](files/guides/web-demo/shopify-embedded-app.md)

### protocols

- [protocols/backend-test-execution.md](files/protocols/backend-test-execution.md)
- [protocols/code-comment-contract.md](files/protocols/code-comment-contract.md)
- [protocols/extension-acceptance-contract.md](files/protocols/extension-acceptance-contract.md)
- [protocols/extension-demo-acceptance-contract.md](files/protocols/extension-demo-acceptance-contract.md)
- [protocols/flutter-demo-run-repair-contract.md](files/protocols/flutter-demo-run-repair-contract.md)

### skills

- [skills/t-design/template-backend.md](files/skills/t-design/template-backend.md)
- [skills/t-design/template-extension.md](files/skills/t-design/template-extension.md)
- [skills/t-design/template-flutter.md](files/skills/t-design/template-flutter.md)
- [skills/t-design/template-frontend.md](files/skills/t-design/template-frontend.md)
- [skills/t-design/template-shopify.md](files/skills/t-design/template-shopify.md)
- [skills/t-extension-demo-accept/SKILL.md](files/skills/t-extension-demo-accept/SKILL.md)
- [skills/t-extension-demo-run-all/SKILL.md](files/skills/t-extension-demo-run-all/SKILL.md)
- [skills/t-extension-demo-run/SKILL.md](files/skills/t-extension-demo-run/SKILL.md)
- [skills/t-flutter-demo-accept/SKILL.md](files/skills/t-flutter-demo-accept/SKILL.md)
- [skills/t-flutter-demo-run-all/SKILL.md](files/skills/t-flutter-demo-run-all/SKILL.md)
- [skills/t-flutter-demo-run/SKILL.md](files/skills/t-flutter-demo-run/SKILL.md)
- [skills/t-init/references/agents-template.md](files/skills/t-init/references/agents-template.md)
- [skills/t-init/references/backend-template.md](files/skills/t-init/references/backend-template.md)
- [skills/t-init/references/extension-demo-init.md](files/skills/t-init/references/extension-demo-init.md)
- [skills/t-init/references/extension-demo-template.md](files/skills/t-init/references/extension-demo-template.md)
- [skills/t-init/references/frontend-template.md](files/skills/t-init/references/frontend-template.md)
- [skills/t-init/references/output-checklist.md](files/skills/t-init/references/output-checklist.md)
- [skills/t-init/references/shopify-init.md](files/skills/t-init/references/shopify-init.md)
- [skills/t-init/references/subagent-prompts.md](files/skills/t-init/references/subagent-prompts.md)

## 脚本与其他资产

完整名单以 template.json 的 source_paths 为准；脚本原文件位于 files/scripts/，导出后在独立插件的 scripts/ 使用。原有测试随对应模板保留，新增修改须在导出运行时验证。
