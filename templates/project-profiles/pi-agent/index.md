# pi coding agent 模板

从 `pi` 分支固定提交 `4951ba13e05033e6a5b89506121e848fa9d8fa65` 提取 extension、skill、prompt/theme 与 package 开发/测试/验收、`t-init --pi` 初始化和对应调用方。来源清单见 [template.json](template.json)。

导出包含该提交的完整配套运行时，沿用来源分支的 phase/state 和依赖约定；不能与 general 的 implementation 状态混用，也不自动启用到通用主链路。SDK 嵌入应用与 fork pi 内核不在此模板初始化范围。

从仓库根目录执行 `python scripts/export-template.py export pi-agent --output <仓库外的新目录>`，可加 `--dry-run`。随后在项目中使用 `claude --plugin-dir <导出目录>`，再显式调用 `/t-tools:t-init --pi <project-name>` 或 `--pi .`。兼容和恢复规则见[模板入口](/templates/index.md)。

固定提交缺失时先 `git fetch origin pi`；导出不访问网络，不修改目标业务项目，也不把来源解析到浮动分支。

## 资源导航

- [README.en.md](files/README.en.md)
- [README.md](files/README.md)
- [agents/pi-accept.md](files/agents/pi-accept.md)
- [agents/pi-design.md](files/agents/pi-design.md)
- [agents/pi-dev.md](files/agents/pi-dev.md)
- [agents/pi-test.md](files/agents/pi-test.md)
- [guides/core/quality.md](files/guides/core/quality.md)
- [guides/pi/development.md](files/guides/pi/development.md)
- [guides/pi/index.md](files/guides/pi/index.md)
- [guides/pi/quality.md](files/guides/pi/quality.md)
- [guides/pi/testing.md](files/guides/pi/testing.md)
- [guides/pi/validation.md](files/guides/pi/validation.md)
- [human/structure.en.md](files/human/structure.en.md)
- [human/structure.md](files/human/structure.md)
- [protocols/acceptance-contract.md](files/protocols/acceptance-contract.md)
- [protocols/agent-task-output-contract.md](files/protocols/agent-task-output-contract.md)
- [protocols/design-agent-output-contract.md](files/protocols/design-agent-output-contract.md)
- [protocols/design-check-rubric.md](files/protocols/design-check-rubric.md)
- [protocols/design-state-contract.md](files/protocols/design-state-contract.md)
- [protocols/pi-project-contract.md](files/protocols/pi-project-contract.md)
- [protocols/review-correctness-contract.md](files/protocols/review-correctness-contract.md)
- [protocols/runtime-boundaries.md](files/protocols/runtime-boundaries.md)
- [protocols/super-run-state-contract.md](files/protocols/super-run-state-contract.md)
- [protocols/task-check-rubric.md](files/protocols/task-check-rubric.md)
- [protocols/task-phase-execution.md](files/protocols/task-phase-execution.md)
- [protocols/tests-to-run-contract.md](files/protocols/tests-to-run-contract.md)
- [skills/t-design-check/SKILL.md](files/skills/t-design-check/SKILL.md)
- [skills/t-design/SKILL.md](files/skills/t-design/SKILL.md)
- [skills/t-design/template-pi.md](files/skills/t-design/template-pi.md)
- [skills/t-design/template.md](files/skills/t-design/template.md)
- [skills/t-dream/SKILL.md](files/skills/t-dream/SKILL.md)
- [skills/t-how/SKILL.md](files/skills/t-how/SKILL.md)
- [skills/t-init/SKILL.md](files/skills/t-init/SKILL.md)
- [skills/t-init/references/pi-init.md](files/skills/t-init/references/pi-init.md)
- [skills/t-init/references/pi-template.md](files/skills/t-init/references/pi-template.md)
- [skills/t-init/references/script-adaptation.md](files/skills/t-init/references/script-adaptation.md)
- [skills/t-push/SKILL.md](files/skills/t-push/SKILL.md)
- [skills/t-release/SKILL.md](files/skills/t-release/SKILL.md)
- [skills/t-skill/SKILL.md](files/skills/t-skill/SKILL.md)
- [skills/t-task-check/SKILL.md](files/skills/t-task-check/SKILL.md)
- [skills/t-task/SKILL.md](files/skills/t-task/SKILL.md)

脚本、初始化资产和其他文件以 template.json 的 source_paths 为准；本轮维护须在导出运行时执行相应检查。
