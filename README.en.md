# T-Tools

[中文](README.md)

A Claude Code plugin for Java Spring Boot, React, Chrome extension, miniapp, and Flutter projects. It turns AI programming into an executable, resumable, and acceptable engineering workflow:

```text
Decision -> PRD / Tech Research (choose by the main unknown; iterate if needed) -> Design -> Task -> Development -> Acceptance -> Demo -> Release
```

T-Tools is designed for projects that already have a delivery chain across product documents, design, task breakdown, development, testing, and demos. Its focus is not freeform model execution. It uses skills to orchestrate stages, subagents to split work, protocols to keep shared contracts stable, and check / accept stages to close quality when needed.

Recommended first reading: [human/structure.en.md](human/structure.en.md) to understand how skills, subagents, and protocols work together. Before shaping a requirement, use [human/speech-template.en.md](human/speech-template.en.md) to speak through the real intent first.

The development log of this project's iterations is kept on [linux.do](https://linux.do/t/topic/1988118/4) (in Chinese).

![T-Tools engineering workflow knowledge graph](knowledge-graph.en.webp)

## Quick Start

Not sure which command to start with? Run `t-how` — it explains the workflow for your goal and recommends the entry command.

Prerequisites:

- The plugin has been loaded by following [Installation](#installation)
- The target project has runtime directories: `docs/` and `.ai/`
- [`context7`](https://github.com/upstash/context7) is configured

Minimal end-to-end loop:

```bash
# Product decision gate; routes to tech research or PRD by the main unknown
t-decision user-management

# Run research first when feasibility, dependencies, or cost may affect scope;
# no fixed order with PRD — converge before design
t-tech-research user-management

# Generate .ai/prd and .ai/user-stories drafts
t-prd user-management

# Generate technical design (master + per-stack)
t-design user-management

# Generate tasks and implement per phase; repeat the loop for other phases
t-task user-management --phase backend
t-run user-management --phase backend

# Single-main-session path for GPT-5.6 Sol-class models, merging planning and execution
t-super-run user-management --phase backend

# Web Demo/E2E and final acceptance (Flutter: t-flutter-demo-run / t-flutter-demo-accept)
t-web-demo-run demo/e2e/<role>/<scenario>.e2e.ts
t-web-demo-accept <role>

# Publish formal PRD / user stories after implementation and acceptance
t-prd-publish user-management
```

`t-prd-check`, `t-design-check`, and `t-task-check` are optional quality checks; use them by risk.

## Phase Split

A typical web order is `backend -> frontend -> web-demo`; a typical Flutter order is `backend -> flutter -> flutter-demo`.

- `backend`: backend APIs, data models, permissions, business logic, backend tests, and read-only acceptance.
- `frontend`: React pages, components, state, frontend tests, and read-only acceptance.
- `extension`: WXT / Chrome MV3 entrypoints, messaging, storage, permissions, Vitest tests, and read-only acceptance; browser demos use `web-demo`.
- `miniapp`: miniapp pages, platform capabilities, build verification, and read-only acceptance.
- `flutter`: Flutter views, Riverpod state, data layers, unit/widget/integration tests, and read-only acceptance.
- `web-demo`: Playwright Demo/E2E based on user stories and browser user paths.
- `flutter-demo`: Android Patrol demos based on user stories, including real App actions and native system UI.

Each phase runs the loop `t-task -> [t-task-check] (optional, by risk) -> t-run`; the quick start shows backend as the example and other phases repeat it. `t-super-run` is the single-main-session path for GPT-5.6 Sol-class models: it merges planning and execution, requires `--phase`, executes exactly one phase per call, then stops. Every supported phase, including extension and miniapp, can use this path.

Prepare a WXT project using the [extension initialization guide](guides/extension/initialization.md) (skip for existing projects; `t-init` has no extension template yet). Once requirement sources are ready, run `t-design <feature>`, `t-task <feature> --phase extension`, and `t-run <feature> --phase extension`. Design produces a separate `extension.md`. See the [extension testing guide](guides/extension/testing.md) for standalone fixtures and `--no-auto-env`.

## Usage Rules

When extension development needs the user's current Chrome tabs, login state, or installed extensions, use **Chrome DevTools MCP with `--autoConnect`**. Follow the [live Chrome debugging guide](guides/extension/live-browser.md) to configure Claude Code, Codex, or ZCode and allow the connection in Chrome. This is a conditional dependency for live-browser tasks, not a globally required MCP server; live evidence and isolated Playwright regression results are assessed separately.

- Every `t-*` command is manually invoked; the model must not trigger them automatically.
- Not sure which command to use, or how a stage runs? Run `t-how`: it routes by goal and explains preconditions, outputs, and next steps.
- PRD, tech research, and design need explicit human calibration: speak through the real intent with [Do Not Shortcut the Intent](human/speech-template.en.md) first, and never deliver with unconfirmed questions left open.

## Installation

```bash
# 1. Clone this repository
git clone <repo-url>

# 2. Start Claude Code in the target project and load the plugin
cd /your-project
claude --plugin-dir /path/to/skills
```

Prerequisites:

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI is installed and logged in
- MCP Server [`context7`](https://github.com/upstash/context7) is configured
- The official [Figma MCP Server](https://developers.figma.com/docs/figma-mcp-server/) and Chrome DevTools MCP are configured when using the Figma workflow (the latter is used for visual acceptance comparison)
- `ffmpeg` and `ffprobe` are installed and available on PATH when converting Figma media assets; SVG optimization additionally requires `svgo` (`npm install -g svgo`)
- `t-figma-impl` / `t-figma-ux` require a user-provided accessible preview URL; the dev server is the user's responsibility to start

For tools that do not support `claude --plugin-dir` (Codex, ZCode, etc.), see [Using t-tools in Other AI Coding Tools](human/use-in-other-agents.en.md): place a dispatcher skill under `~/.agents/skills/` that routes `/t-tool <skill>` to the cloned repository directory.

## Projects Using This Plugin

- [Herald](https://github.com/timzaak/herald) — A multi-tenant authentication and authorization system
- [RMQTT-Things](https://github.com/timzaak/rmqtt-things) — An IoT thing-model management platform built on RMQTT
- [RWiki](https://github.com/timzaak/rwiki) — RAG-powered knowledge base Q&A in a single binary, zero external databases

> The current `java` branch provides Java Spring Boot backend support.
