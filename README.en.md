# T-Tools

[中文](README.md)

A general Claude Code engineering workflow plugin for real projects: executable, resumable, and independently accepted. The plugin supplies orchestration, decision continuity, quality gates and recovery. Production stacks, architecture and testing practices come from the target project. Web Demo and Figma remain available.

```text
Decision -> PRD / Tech Research -> Design -> Implementation / Testing -> Independent Acceptance -> Publish
```

Read the [structure overview](human/structure.en.md), [intent template](human/speech-template.en.md), [generalization rationale](human/generalization.en.md), and [proposed project knowledge workflow](human/generalization-plan.en.md). The knowledge proposal has not been implemented as a new command.

## Quick start

Users explicitly invoke commands. Use `/t-tools:t-how` for routing. From an existing project root:

```text
/t-tools:t-init
/t-tools:t-decision sample-feature
/t-tools:t-prd sample-feature
/t-tools:t-design sample-feature
/t-tools:t-super-run sample-feature --phase implementation
/t-tools:t-prd-publish sample-feature
```

Use t-tech-research first when feasibility, dependencies or costs are the main unknown, and converge with PRD before design. Only purely technical changes that do not alter business behavior, product rules, user flows or acceptance goals may proceed directly from research to design.

`t-prd-check`, `t-design-check` and `t-task-check` remain optional, risk-based checks. They do not replace post-implementation acceptance.

## Phases and project constraints

The current phases are generic `implementation` and optional `web-demo`. The [phase contract](protocols/task-phase-execution.md) alone defines activation, ordering, design inputs and roles. Modules follow actual project boundaries rather than preset languages or directories.

`t-super-run <feature> --phase <phase>` executes only the requested phase: the main session performs dev/test work and an independent read-only accept agent closes it. Resume the same command from persisted state. Use `t-task -> t-run` when a separate item plan needs review; its state is independent.

Project AGENTS.md, code, configuration and confirmed documentation define engineering rules. t-init connects an existing project and documents actual entrypoints; it does not scaffold an application. Project CI lives in scripts/ci.py and invokes real checks. Missing or failing CI blocks push.

Previous domain commands and phases have been removed. They are not silently mapped and old state is not automatically migrated. Preserve old artifacts, replan from the current design and verify existing evidence before execution.

## Web Demo

```text
/t-tools:t-init --web-demo
/t-tools:t-super-run sample-feature --phase web-demo
/t-tools:t-web-demo-run demo/e2e/<role>/<scenario>.e2e.ts
/t-tools:t-web-demo-run-all
/t-tools:t-web-demo-run-all continue
/t-tools:t-web-demo-accept <role>
```

Initialization establishes Playwright and logging infrastructure; smoke success does not accept real stories. The project defines URLs, identities, isolation and cleanup. Automatic environment management requires local scripts/demo-start.py, demo-health.py and demo-stop.py, with exit code 0 indicating success. Fixture/external management uses --no-auto-env. No application environment falls back to the plugin. See [Web Demo guides](guides/web-demo/index.md) and the [repair contract](protocols/web-demo-run-repair-contract.md).

## Figma

`t-figma-assets`, `t-figma-impl` and `t-figma-ux` retain asset processing, block-based reconstruction and motion refinement in existing project files, without selecting a production framework. Assets may be prepared later but must be bound before delivery; developers perform page acceptance. See [Figma guides](guides/figma/index.md) and the [shared contract](protocols/figma-workflow-contract.md).

## Quality chain and supporting commands

Close changes with `t-review --fix -> t-simplify -> t-push`. Repairs invalidating evidence require regression checks and independent acceptance. Review reports by default; unresolved correctness findings block push. Push uses project CI and preserves recovery after remote failures; see the [push contract](protocols/push-execution-contract.md). scripts/release.py and t-release govern publishing: semantic versions omit v, Git tags include v.

| Goal | Entry |
| --- | --- |
| Workflow guidance | [t-how](skills/t-how/SKILL.md) |
| Decisions and research | [t-decision](skills/t-decision/SKILL.md), [t-tech-research](skills/t-tech-research/SKILL.md) |
| Requirements and publishing | [t-prd](skills/t-prd/SKILL.md), [t-prd-publish](skills/t-prd-publish/SKILL.md) |
| Design and optional checks | [t-design](skills/t-design/SKILL.md), [t-design-check](skills/t-design-check/SKILL.md), [t-prd-check](skills/t-prd-check/SKILL.md) |
| Planning and execution | [t-super-run](skills/t-super-run/SKILL.md), [t-task](skills/t-task/SKILL.md), [t-run](skills/t-run/SKILL.md), [t-task-check](skills/t-task-check/SKILL.md) |
| Review, cleanup and push | [t-review](skills/t-review/SKILL.md), [t-simplify](skills/t-simplify/SKILL.md), [t-push](skills/t-push/SKILL.md) |
| Context and consistency | [t-dream](skills/t-dream/SKILL.md) |
| Skill authoring | [t-skill](skills/t-skill/SKILL.md), --project for target-project skills |
| Documents and previews | [t-doc](skills/t-doc/SKILL.md), [t-html-show](skills/t-html-show/SKILL.md) |
| Icon prompts | [t-icon-prompt](skills/t-icon-prompt/SKILL.md) |
| Onboarding and release | [t-init](skills/t-init/SKILL.md), [t-release](skills/t-release/SKILL.md) |

## Optional domain templates

Migrated assets remain in [templates/](templates/index.md). [classic-stack](templates/project-profiles/classic-stack/index.md) preserves Rust/React, extension, miniapp, Flutter and Shopify roles, practices, scripts and scaffolds. [java-backend](templates/project-profiles/java-backend/index.md) preserves Java/Spring Boot/Maven backend content from java.

```powershell
python scripts/export-template.py list
python scripts/export-template.py export classic-stack --output C:/code/ai/t-tools-classic
python scripts/export-template.py export java-backend --output C:/code/ai/t-tools-java
```

Output must be outside this repository. --dry-run previews; repeated exports preserve user edits. Export combines domain sources with the template's pinned shared runtime, producing a standalone plugin loadable with claude --plugin-dir. Select the generic plugin or one template per session; do not mix phase/state versions. Templates are inactive by default. Fetch origin main or origin java first if pinned history is unavailable.

## Ongoing maintenance

Before integrating main, read the [merge guide](human/merge-main.en.md): classify generic updates and domain migrations, resolve modify/delete conflicts, advance template baselines independently, and validate both runtimes.

## Installation

```bash
git clone <repo-url>
cd /your-project
claude --plugin-dir /path/to/web-dev-skills
```

Configure Context7 MCP for entrypoints needing dependency documentation. Figma requires the official Figma MCP; asset conversion needs ffmpeg/ffprobe, svgo and kyz as described in the [asset guide](guides/figma/assets.md). Web Demo needs Python/uv, Node and Playwright browsers. Workflows create .ai/ and docs/ as needed; empty state files are not required.

Other AI tools can use the [thin dispatcher](human/use-in-other-agents.en.md). Shared contracts are indexed in [protocols/index.md](protocols/index.md).

## Projects using T-Tools

- [Herald](https://github.com/timzaak/herald) — multi-tenant authentication and authorization
- [RMQTT-Things](https://github.com/timzaak/rmqtt-things) — IoT thing-model management
- [RWiki](https://github.com/timzaak/rwiki) — RAG knowledge-base Q&A
- [OnceWise](https://github.com/timzaak/OnceWise) — intelligent form automation

The iteration log is on [linux.do](https://linux.do/t/topic/1988118/4) (Chinese).
