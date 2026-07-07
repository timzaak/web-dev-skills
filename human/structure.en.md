# Skill and Subagent Design in T-Tools

T-Tools is not a loose collection of prompts. It is an AI programming workflow for engineering delivery. It constrains Claude Code from an ad hoc Q&A tool into an executable, recoverable, and verifiable collaboration system.

Core responsibilities:

- `skills/`: workflow orchestration, including stage progression, prerequisite checks, state updates, and failure recovery.
- `agents/`: specialized execution, split by roles such as dev, test, accept, and diagnose.
- `protocols/`: shared contracts for state structures, output structures, scoring rules, and quality gates.
- `guides/`: engineering standards for backend, frontend, demo, product, and shared quality rules.
- `.ai/` and `docs/`: runtime artifacts and long-term business facts in the target project.
- Humans: state real intent, make tradeoff decisions, point out detail preferences, and calibrate AI output through Preview, check, and accept stages.

Before working on a requirement, PRD, or technical research, use [Do Not Shortcut the Intent](speech-template.en.md). It lets humans naturally walk through the starting goal, user story, UI/UX, third-party integration, third-party library introduction, and closing instruction; AI then evaluates executability, feasibility, missing details, and open questions, and records them in `.ai/future/[feature].md` when needed.

## Four Layers

### Skills: Workflow Controllers

A skill is an imperative workflow entry point, not "a prompt that lets the model improvise." It usually:

- Validates inputs and prerequisites.
- Reads upstream documents and state.
- Dispatches the right subagent.
- Writes standardized artifacts.
- Advances `.ai/task/**/.state.json`.
- Provides a recoverable path when something fails.

The main path is:

```text
t-decision -> t-tech-research -> t-prd -> t-prd-check
-> t-design -> t-design-check
-> t-task -> t-task-check
-> t-run -> t-code-review
-> t-demo-run -> t-demo-accept
-> t-prd-publish -> t-push -> t-release
```

Not every project needs every optional stage, but check / accept stages are not decorative. They stop upstream problems before those problems move downstream.

### Agents: Specialized Executors

Subagents are split by engineering role instead of making one agent own every responsibility:

- `backend-dev` / `frontend-dev` / `miniapp-dev`: implementation.
- `backend-test` / `frontend-test` / `miniapp-test`: testing.
- `backend-accept` / `frontend-accept` / `miniapp-accept`: read-only acceptance with evidence.
- `demo-dev` / `demo-accept` / `demo-diagnose`: Playwright Demo/E2E maintenance, acceptance, and diagnosis.
- `context-curator` / `structure-review` / `backend-consistency`: context, structure, and implementation consistency audits.
- `html-show`: converts Markdown into HTML Preview.

The point is responsibility boundaries. When something fails, the workflow hands off to the right role instead of asking one agent to implement, test, accept, and explain everything in the same pass.

### Protocols: Shared Contracts

`protocols/` is the single source of truth shared by skills and agents. It defines:

- The state structure of `.ai/task/[feature]/.state.json`.
- The execution order of `phase -> slot -> item`.
- Structured output when an agent completes or fails.
- The `tests_to_run` set required after a fix.
- PRD Preview location, content model, and check scope.
- Scoring and blocking rules for PRD, design, task, Demo, and t-dream checks.

Shared rules should be changed in protocols first, not copied across multiple skill or agent documents.

### Guides: Engineering Standards

`guides/` contains concrete engineering practice:

- `backend/`: backend architecture, development, testing, validation, TDD, and quality gates.
- `frontend/`: frontend development patterns, testing strategy, `data-testid`, and quality gates.
- `miniapp/`: miniapp development, testing, validation, and quality gates.
- `demo/`: E2E, selectors, Page Objects, diagnosis, and common failure handling.
- `product/`: product documents and user story standards.
- `core/`: environment configuration and general quality standards.

Agent documents only say when to read guides, how to execute, and what to return. They do not duplicate guide rules.

## Key Designs

### PRD: Make AI's Product Understanding Visible

`t-prd` first writes `.ai/prd` and `.ai/user-stories` drafts, then generates an HTML Preview. Markdown remains the formal contract; Preview is the human entry point for reviewing that contract quickly.

The useful order is not to open the Preview immediately and follow the AI's narrative. First, step away from the generated artifact and use [Do Not Shortcut the Intent](speech-template.en.md) to state the requirement you would accept: what pain it solves, which user path matters most, what the UI/UX must make clear at first glance, how abnormal states should explain themselves, and whether third-party capabilities or libraries truly fit. Then review the Preview and ask the AI to revise the PRD, user stories, and Preview against that feedback.

`t-prd-check` is not just a format check. It verifies that the AI's written product understanding, the Preview, user stories, and formal documents are aligned. After implementation, testing, and Demo acceptance are complete, `t-prd-publish` merges still-valid long-term facts back into `docs/`.

### Tech Research: Make Feasibility Questions Explicit

`t-tech-research` is used to decide whether the requirement is feasible, which dependencies are needed, which existing modules are affected, and which risks may change PRD or design direction. The spoken template is not a replacement for the technical research report; it helps humans first state third-party API expectations, tech stack compatibility, frontend/backend SDK needs, data idempotency, webhook ordering, and permission boundaries.

After receiving the walkthrough, AI should separate confirmed technical constraints, facts that require official documentation, current-state facts that can be verified from the codebase, and product or technical decisions that must be asked of the user. Guesses in the walkthrough must not be written as confirmed conclusions.

### Design: Human-Led UX Choices

`t-design` is not only a translation from PRD to modules, APIs, and states. When a feature includes frontend UI, humans need to walk through the experience from the user's perspective:

- Where the user enters, and what they should understand first.
- How each step makes the next action clear.
- How loading, empty, error, permission-denied, dangerous-action, and success states behave.
- How defaults, undo, confirmation, save, and leaving the page affect trust.
- Which interactions are good, and which are usable but unacceptable.

AI can fill flows and boundaries, but "good UX" is a matter of taste and tradeoff. It must not be left for the model to generate from a generic template.

### Demo: Independent User Story Closure

The Demo stage is not a duplicate of backend or frontend testing. It uses Playwright E2E to validate real user paths against user stories, and treats the test code itself as part of acceptance.

- `demo-dev` turns user stories into executable demo tests.
- `demo-accept` checks coverage, roles, scenarios, assertions, execution results, and evidence.
- `demo-diagnose` identifies whether a failure belongs to demo tests, frontend implementation, or backend implementation, then hands off to the matching agent.

It verifies deliverable demonstrability and user story closure, not only whether code compiles.

## Execution Model

`t-task` decomposes design into a standard task directory:

```text
.ai/task/[feature]/
├── .state.json
├── backend/
├── frontend/
└── demo/
```

The model is `phase -> slot -> item`:

- `phase`: usually `backend -> frontend -> demo`.
- `slot`: for example, `dev -> test -> accept`.
- `item`: the smallest executable task file.

`t-run` executes only items. It does not directly execute manifests such as `index.md`, `dev.md`, `test.md`, or `accept.md`. At most one item may be `running` at a time. This trades some concurrency for smaller context, clearer failure localization, and recoverable state.

A fixing agent must return `tests_to_run`, explaining which backend, frontend, or Demo commands should be rerun after the fix. This keeps the risk of "Demo passes but lower-level regression fails" visible.

## Supporting Governance

`t-dream` is a cross-stage context cleanup and structure drift audit tool. By default it is read-only: it checks PRDs, user stories, designs, tasks, code, tests, and demos for stale content, duplication, conflicts, broken traceability, or implementation mismatch. Use `--govern-prd` only when PRD governance should write changes.

`t-push` is the local CI closure before commit. It detects backend / frontend / demo impact from the diff, runs the matching checks, then commits and pushes only after they pass. Formal version publishing remains governed by `t-release`; version files use semver without `v`, while git tags use the `v` prefix.

## Design Tradeoff

The core tradeoff of T-Tools is using more structure to reduce uncontrolled improvisation.

It does not try to make AI finish everything at once. It makes requirements, design, tasks, implementation, tests, acceptance, and release move through explicit documents, state, contracts, and gates. The model still reasons and implements, but it must follow those engineering rails.

One-sentence summary: T-Tools uses skills to orchestrate workflow, subagents to divide execution, protocols to solidify contracts, and guides to keep engineering behavior consistent, turning AI programming into a traceable, recoverable, and verifiable long-term workflow.
