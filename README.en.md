# T-Tools

[中文](README.md)

A Claude Code plugin for Rust, React, miniapp, and Flutter projects. It turns AI programming into an executable, resumable, and acceptable engineering workflow:

```text
Decision -> PRD / Tech Research (choose by the main unknown; iterate if needed) -> Design -> Task -> Development -> Acceptance -> Demo -> Release
```

T-Tools is designed for projects that already have a delivery chain across product documents, design, task breakdown, development, testing, and demos. Its focus is not freeform model execution. It uses skills to orchestrate stages, subagents to split work, protocols to keep shared contracts stable, and check / accept stages to close quality when needed.

Recommended first reading: [human/structure.en.md](human/structure.en.md) to understand how skills, subagents, and protocols work together. Before shaping a requirement, use [human/speech-template.en.md](human/speech-template.en.md) to speak through the real intent first.

![T-Tools knowledge graph](knowledge-graph.png)

## Quick Start

Prerequisites:

- The plugin has been loaded by following [Installation](#installation)
- The target project has runtime directories: `docs/` and `.ai/`
- [`context7`](https://github.com/upstash/context7) is configured

Minimal end-to-end loop:

```bash
# Product decision gate
/t-tools:t-decision user-management

# Start with research when feasibility, dependency, or cost risks affect product scope
/t-tools:t-tech-research user-management

# Generate .ai/prd and .ai/user-stories drafts when product boundaries are ready;
# this may also run before research, then run again afterward to converge the drafts
/t-tools:t-prd user-management

# PRD quality check (optional; recommended for high-risk requirements)
/t-tools:t-prd-check user-management

# Generate technical design
/t-tools:t-design user-management

# Design quality check (optional; recommended for complex designs)
/t-tools:t-design-check user-management

# Generate executable backend tasks
/t-tools:t-task user-management --phase backend

# Check task breakdown, execution order, and executability (optional; recommended for complex plans)
/t-tools:t-task-check user-management --phase backend

# Implement and test by phase
/t-tools:t-run user-management --phase backend

# GPT-5.6 Sol-class path: let one main session plan, execute, and remain in
# Goal mode through implementation, validation, repair, and acceptance
/t-tools:t-super-run user-management --phase backend

# Run Demo/E2E tests
/t-demo-run demo/e2e/<role>/<scenario>.e2e.ts

# Run all non-live Demo/E2E files sequentially with checkpoint resume
/t-demo-run-all

# Final acceptance
/t-tools:t-demo-accept <role>

# Publish formal PRD / user stories after implementation and acceptance
/t-tools:t-prd-publish user-management
```

`t-prd-check`, `t-design-check`, and `t-task-check` are optional quality checks. Run them for high-risk requirements, complex designs, multi-person work, long-lived changes, or unstable AI output; simple changes may continue directly to the next stage. `accept` remains the implementation acceptance closure and is not part of this optional-check change.

## Phase Split

`t-task`, `t-task-check`, and `t-run` all progress by phase, with `t-task-check` as an optional check. A typical web order is `backend -> frontend -> demo`; insert `miniapp` and/or `flutter` when those clients are part of the delivery scope.

- `backend`: backend APIs, data models, permissions, business logic, backend tests, and read-only acceptance.
- `frontend`: React pages, components, state, frontend tests, and read-only acceptance.
- `miniapp`: miniapp pages, platform capabilities, build verification, and read-only acceptance.
- `flutter`: Flutter views, Riverpod state, data layers, unit/widget/integration tests, and read-only acceptance.
- `demo`: Playwright Demo/E2E based on user stories, with acceptance for real user paths.

Each phase starts with `/t-tools:t-task <feature> --phase <phase>`, may run `/t-tools:t-task-check <feature> --phase <phase>` depending on risk, and then `/t-tools:t-run <feature> --phase <phase>` executes items serially. The quick start expands backend only as an example; repeat the same loop for frontend, miniapp, flutter, and demo.

`/t-tools:t-super-run <feature> [--phase backend|frontend|demo]` is a single-main-session execution path optimized for GPT-5.6 Sol (`gpt-5.6-sol`)-class models. It combines planning and execution, dispatches no subagents, records outcome-level `dev -> test -> accept` state for backend/frontend or `dev -> accept` for demo, and actively uses Goal mode through implementation, validation, repair, and acceptance. Its state lives independently under `.ai/super-run/<feature>/` and must not overwrite or derive `.ai/task/<feature>/`. Without `--phase`, it selects the first applicable unfinished phase in `backend -> frontend -> demo` order. Miniapp and Flutter keep their existing stage commands; use `t-task -> [t-task-check] -> t-run` when explicit subagent ownership, fine-grained item handoffs, or consistent dispatch behavior across runtimes is required.

## Key Rules

- This README consistently uses `/t-tools:t-*` as the standard invocation format.
- All `t-*` skills are manual command entries and must not be invoked automatically by the model.
- `t-super-run` reads existing agent specifications as role guides without starting subagents, and uses outcome-level state, staged handoffs, and Goal mode for long-running execution and interruption recovery.
- `t-decision` is the product decision gate before PRD and technical research. It writes `.ai/decision/<feature>.md`; `Proceed` routes to `t-prd` or `t-tech-research` according to the main unknown, while `Research First` routes to `t-tech-research`.
- Confirmed decisions, resolved questions, and explicitly deferred questions persist across stages in `.ai/decision-log/<feature>.md` with stable DEC/Q IDs. Every stage must consult the log before asking, so it does not repeat a resolved question or apply a superseded decision.
- A completed PRD, technical research report, or design must have `needs_user_answer=0`. Questions that affect scope, business rules, permissions, security, compatibility, significant cost, acceptance, or risk acceptance must be asked before delivery, not silently stored as pending items, assumptions, or risks.
- `t-prd` and `t-tech-research` have no globally fixed order. Start with research when technical unknowns may change scope; start with a PRD draft when product boundaries determine the technical choice. If later findings change product semantics, rerun `t-prd`; both artifacts must converge without unexplained conflicts before `t-design`.
- `t-prd` only writes candidate requirements under `.ai/prd` and `.ai/user-stories`; `t-prd-publish` merges still-valid long-term product facts back into `docs/`.
- `t-doc` is for project documentation, onboarding tutorials, API references, configuration, and deployment notes. It is not for PRDs, technical designs, or small document edits.
- `t-dream` defaults to a read-only audit of PRDs, user stories, design/tasks, implementation facts, and project structure; use `--govern-prd` explicitly when PRD governance should write changes.
- `t-push` cleans clearly low-value comments from the current diff, summarizes a commit message, then calls `${CLAUDE_PLUGIN_ROOT}/scripts/push.py` to run affected CI, commit, and push.
- Before running `t-push`, it is recommended to first run `/code-review --fix` and `/simplify` in Claude Code, so the code is independently reviewed and simplified before the final commit; their diffs are independent of `t-push` and will not overwrite each other.

PRD, technical research, and design stages need explicit human calibration. If you are not sure how to do the spoken walkthrough, open [Do Not Shortcut the Intent](human/speech-template.en.md) and follow its headings: getting started, user story walkthrough, UI/UX walkthrough, third-party integration walkthrough, third-party library introduction, and closing. After ingesting that walkthrough, AI should first output its key understanding, evaluate executability, feasibility, and missing details, search the web for similar products and best practices when needed, write the content and answers into `.ai/future/[feature].md`, then generate or revise PRD, technical research, and design inputs. After `/t-tools:t-prd`, first step away from the generated artifact and state the PRD you would accept, then ask the AI to revise against it. After `/t-tools:t-design`, review the UX from the user's perspective: entry points, paths, feedback, defaults, and error states, then ask the AI to revise the technical design.

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

For tools that do not support `claude --plugin-dir` (Codex, ZCode, etc.), see [Using t-tools in Other AI Coding Tools](human/use-in-other-agents.en.md): place a dispatcher skill under `~/.agents/skills/` that routes `/t-tool <skill>` to the cloned repository directory.

## Projects Using This Plugin

- [Herald](https://github.com/timzaak/herald) — A multi-tenant authentication and authorization system
- [RMQTT-Things](https://github.com/timzaak/rmqtt-things) — An IoT thing-model management platform built on RMQTT
- [RWiki](https://github.com/timzaak/rwiki) — An AI-enhanced knowledge base built on Wiki.js data

> For Java backend support, see the `java` branch.
