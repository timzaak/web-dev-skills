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

After Decision, the main path branches according to the primary unknown and converges before Design:

```text
t-decision
├─ technical unknowns may change product scope -> t-tech-research -> t-prd -> [t-prd-check] -> t-design
├─ product boundaries determine technical choices -> t-prd -> [t-tech-research -> t-prd update] -> [t-prd-check] -> t-design
└─ purely technical, no business-logic change -> t-tech-research -> t-design

t-design -> [t-design-check] -> t-task -> [t-task-check]
-> t-run
-> t-web-demo-run / t-flutter-demo-run -> matching demo accept
-> t-prd-publish -> t-push -> t-release
```

`t-prd` and `t-tech-research` have no globally fixed order. Start with research when feasibility, cost, dependencies, or compatibility may change product scope. Start with a PRD draft when product boundaries, user flows, or acceptance goals must be clear before selecting a technical route. If later research changes product semantics, rerun `t-prd` to update the draft. Before `t-design`, the artifacts must converge without unexplained conflicts. A purely technical proposal may skip PRD only when it does not change business logic, product rules, user-visible flows, or acceptance goals.

Not every project needs every stage. `t-prd-check`, `t-design-check`, and `t-task-check` are optional quality checks: use them for complex, high-risk, or multi-person work to stop upstream problems before they move downstream; simple low-risk changes may continue directly to the next stage. Implementation accept stages still close delivery acceptance.

### Agents: Specialized Executors

Subagents are split by engineering role instead of making one agent own every responsibility:

- `backend-dev` / `frontend-dev` / `miniapp-dev`: implementation.
- `backend-test` / `frontend-test` / `miniapp-test`: testing.
- `backend-accept` / `frontend-accept` / `miniapp-accept`: read-only acceptance with evidence.
- `web-demo-dev` / `web-demo-accept` / `web-demo-diagnose`: Playwright Demo/E2E maintenance, acceptance, and diagnosis.
- `flutter-demo-dev` / `flutter-demo-accept` / `flutter-demo-diagnose`: Android Patrol user-story demo maintenance, acceptance, and diagnosis.
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
- `web-demo/`: Playwright E2E, selectors, Page Objects, diagnosis, and common failure handling.
- `flutter/`: Flutter development, testing, and Android Patrol user-story demos.
- `product/`: product documents and user story standards.
- `core/`: environment configuration and general quality standards.

Agent documents only say when to read guides, how to execute, and what to return. They do not duplicate guide rules.

## Key Designs

### PRD: Make AI's Product Understanding Visible

`t-prd` first writes `.ai/prd` and `.ai/user-stories` drafts. Markdown is the formal contract and the human entry point for reviewing the AI's product understanding.

The useful order is not to follow the AI's generated artifact immediately. First, step away from the generated artifact and use [Do Not Shortcut the Intent](speech-template.en.md) to state the requirement you would accept: what pain it solves, which user path matters most, what the UI/UX must make clear at first glance, how abnormal states should explain themselves, and whether third-party capabilities or libraries truly fit. Then ask the AI to revise the PRD and user stories against that feedback.

`t-prd-check` is an optional quality check, not just a format check. It verifies that the AI's written product understanding, user stories, and formal documents are aligned. When it is skipped, `t-design` still performs its own mixed validation between drafts and published baselines for critical conflicts. After implementation, testing, and Demo acceptance are complete, `t-prd-publish` merges still-valid long-term facts back into `docs/`.

### Tech Research: Make Feasibility Questions Explicit

`t-tech-research` is used to decide whether the requirement is feasible, which dependencies are needed, which existing modules are affected, and which risks may change PRD or design direction. The spoken template is not a replacement for the technical research report; it helps humans first state third-party API expectations, tech stack compatibility, frontend/backend SDK needs, data idempotency, webhook ordering, and permission boundaries.

After receiving the walkthrough, AI should separate confirmed technical constraints, facts that require official documentation, current-state facts that can be verified from the codebase, and product or technical decisions that must be asked of the user. Guesses in the walkthrough must not be written as confirmed conclusions.

Technical research may happen before or after a PRD draft. When a draft exists, research treats it as a candidate product boundary but must not silently rewrite product decisions. If research shows that scope, business rules, user flows, or acceptance goals must change, hand the findings back to `t-prd` for an update instead of carrying the conflict into design.

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

- Runtime-specific demo dev agents turn user stories into executable demos.
- Matching demo accept agents check coverage, roles, scenarios, assertions, execution results, and evidence.
- Matching demo diagnose agents attribute failures to test assets, clients, backend, or environment before handoff.

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

`t-super-run` provides a single-main-session execution model. It generates no items and dispatches no subagents. Instead, the main session reads the current task's agent specification and related guides, executes the work, checkpoints status and evidence under `.ai/super-run/[feature]/`, and then switches roles. Backend/frontend use `dev -> test -> accept`; demo uses `dev -> accept`. Goal mode keeps the phase moving, while the state file supports recovery across context compaction. Keep the standard path when explicit subagent ownership or fine-grained handoffs are required.

A fixing agent must return `tests_to_run`, explaining which backend, frontend, or Demo commands should be rerun after the fix. This keeps the risk of "Demo passes but lower-level regression fails" visible.

## Supporting Governance

`t-dream` is a cross-stage context cleanup and structure drift audit tool. By default it is read-only: it checks PRDs, user stories, designs, tasks, code, tests, and demos for stale content, duplication, conflicts, broken traceability, or implementation mismatch. Use `--govern-prd` only when PRD governance should write changes.

`t-push` is the local CI closure before commit. It detects backend / frontend / demo impact from the diff, runs the matching checks, then commits and pushes only after they pass. Formal version publishing remains governed by `t-release`; version files use semver without `v`, while git tags use the `v` prefix.

## Design Tradeoff

The core tradeoff of T-Tools is using more structure to reduce uncontrolled improvisation.

It does not try to make AI finish everything at once. It makes requirements, design, tasks, implementation, tests, acceptance, and release move through explicit documents, state, contracts, and gates. The model still reasons and implements, but it must follow those engineering rails.

One-sentence summary: T-Tools uses skills to orchestrate workflow, subagents to divide execution, protocols to solidify contracts, and guides to keep engineering behavior consistent, turning AI programming into a traceable, recoverable, and verifiable long-term workflow.
