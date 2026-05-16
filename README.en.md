# T-Tools

[中文](README.md)

A Claude Code plugin for Rust + React projects. It turns `PRD -> Design -> Task -> Development -> Acceptance -> Demo` into a reusable workflow, so teams do not need to repeatedly design prompts, switch context manually, or maintain stage boundaries by hand.

It is designed for teams and projects that:

- Already have a clear delivery chain across product documents, design, task breakdown, development, testing, and demo delivery
- Want to move Claude Code from ad hoc Q&A to an executable engineering workflow
- Need subagent collaboration, stage gates, and standardized artifacts instead of one-off freeform execution

## Why Use It

- Fast adoption: follow the `/t-tools:t-*` command sequence directly, without designing a full prompt and collaboration system yourself
- Stable delivery: key stages include check and acceptance commands to reduce document drift, missed task breakdowns, and non-runnable demos
- Clear collaboration: skills, agents, guides, and protocols are layered for reuse across teams and long-running projects

## Full Workflow

```text
/t-tools:t-init <project-name> (optional, initialize a full-stack project scaffold)
  /t-tools:t-tech-research (optional, evaluate technical feasibility before PRD)
  /t-tools:t-prd
  -> /t-tools:t-prd-check
  -> /t-tools:t-design
  -> /t-tools:t-design-check
  -> /t-tools:t-task
  -> /t-tools:t-task-check
  -> /t-tools:t-run
  -> /t-tools:t-backend-finalize
  -> /t-tools:t-demo-run
  -> /t-tools:t-demo-accept
  -> /t-tools:t-release [version]
```

Notes:

- `/t-tools:t-prd-check` is the quality gate for PRDs and user stories. It is not an optional helper command.
- `/t-tools:t-demo-accept` is the demo-stage acceptance gate. It verifies test coverage, runnability, and delivery quality.

Common helper commands:

- `/t-tools:t-init <project-name>`: initializes a full-stack project scaffold for Rust Axum + React TanStack, including backend, frontend, E2E tests, development scripts, and the complete directory structure
- `/t-tools:t-tech-research`: evaluates technical feasibility before writing the PRD, including dependency gap analysis, library research, impact analysis, and feasibility judgment
- `/t-tools:t-doc <project-or-module-name>`: scans the target project codebase and generates newcomer-oriented tutorial documentation under `docs/tutorials/<name>/` by default
- `/t-tools:t-consistency-check`: checks whether the backend PRD and implementation are consistent; it is not a global DDD inspection command
- `/t-tools:t-demo-run-all`: runs demo tests in batch
- `/t-tools:t-release [version]`: releases a version by updating project versions, creating a git commit and tag, and pushing to the remote. The version follows semantic versioning, such as `0.2.0`; the final tag never uses a `v` prefix. If omitted, the command recommends one based on the latest semver tag and strips any historical `v` prefix. It only runs on a clean `main` branch, updates `backend/Cargo.toml`, `frontend/package.json`, and `demo/package.json`, then commits and pushes after compilation checks pass.

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
- MCP Server `context7` is configured for third-party library documentation lookup

## 3-Minute Quick Start

Prerequisites:

- The t-tools plugin has been loaded by following the [Installation](#installation) steps
- The target project has runtime directories: `docs/` and `.ai/`
- `context7` is enabled

Minimal end-to-end example:

```bash
/t-tools:t-prd user-management
/t-tools:t-prd-check user-management
/t-tools:t-design user-management
/t-tools:t-task user-management
/t-tools:t-run user-management --phase backend
/t-tools:t-demo-run super-admin
/t-tools:t-demo-accept super-admin
```

Execution flow:

- `/t-tools:t-prd user-management`: creates the PRD if it does not exist, or completes and updates the existing PRD and user stories
- `/t-tools:t-prd-check user-management`: immediately runs the product-document quality gate, so upstream issues do not enter the design stage
- `/t-tools:t-design user-management`: produces the technical design from the PRD
- `/t-tools:t-task user-management`: converts the design into executable tasks
- `/t-tools:t-run user-management --phase backend`: drives implementation and testing by phase
- `/t-tools:t-demo-run super-admin`: runs the Demo/E2E tests for the role
- `/t-tools:t-demo-accept super-admin`: performs final acceptance and verifies story mapping, compilation, execution, and quality requirements

If you only remember one thing: do not skip check or accept stages. This plugin is not only for generating content. It is also designed to close each stage before problems flow downstream.

Additional notes:

- This README consistently uses `/t-tools:t-*` as the standard invocation format.
- `t-doc` is for project documentation, onboarding tutorials, API references, configuration, and deployment notes. It is not for PRDs, technical designs, or small document edits.
- `t-consistency-check` is a backend-specific consistency check and is not equivalent to the old repository's global DDD inspection.
- `t-backend-test-run` is an internal execution skill reused by flows such as `backend-test`; it is not recommended as a manual entry point.

## Common Entry Points

- Design overview: [human/structure.en.md](human/structure.en.md), recommended first reading to understand how skills, subagents, and protocols work together to drive AI programming
- Chinese design overview: [human/structure.md](human/structure.md)
- Product standards: [guides/product/index.md](guides/product/index.md)
- Backend development and gates: [guides/backend/index.md](guides/backend/index.md)
- Frontend development and gates: [guides/frontend/index.md](guides/frontend/index.md)
- Mini app development and gates: [guides/miniapp/index.md](guides/miniapp/index.md)
- Demo testing and diagnosis: [guides/demo/index.md](guides/demo/index.md)
- Cross-domain overview: [guides/core/index.md](guides/core/index.md)
- Protocol index: [protocols/index.md](protocols/index.md)

## Repository Boundary

This is the plugin source repository, not a target business repository.

- Plugin resources mainly live under `skills/`, `agents/`, `guides/`, `protocols/`, and `scripts/`
- The plugin manifest is `.claude-plugin/plugin.json`
- Target projects mainly depend on runtime directories such as `docs/` and `.ai/`

When referencing internal plugin files, use the `${CLAUDE_PLUGIN_ROOT}` semantic path. The root `README.md` only explains value, workflow, and quick start. Detailed rules live in the corresponding guide or protocol.

## Projects Using This Plugin

- [herald](https://github.com/timzaak/herald) — A multi-tenant authentication and authorization system (Rust Axum + SeaORM + PostgreSQL / React 19 + TanStack), providing auth services for both single-tenant and multi-tenant scenarios
- [rmqtt-things](https://github.com/timzaak/rmqtt-things) — An IoT thing-model management platform built on RMQTT (Rust Axum + SQLx + PostgreSQL / React 19 + TanStack), with device management, command delivery, OTA firmware updates, and TLS certificate issuance

## Dependencies

- `Context7`: used by `backend-dev`, `backend-test`, `frontend-dev`, and `frontend-test` to query third-party library documentation
- `/simplify`: optional, used by `t-backend-finalize` for final review
