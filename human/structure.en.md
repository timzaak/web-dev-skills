# Skill and Subagent Design in T-Tools

T-Tools is not a loose collection of prompts. It is an AI programming workflow designed for engineering delivery. Its goal is to constrain Claude Code from an ad hoc Q&A tool into an executable, recoverable, and verifiable collaboration system.

The core idea can be summarized as:

- `skills/` handles workflow orchestration.
- `agents/` handles specialized execution.
- `protocols/` handles shared contracts.
- `guides/` handles engineering standards.
- `.ai/` and `docs/` handle runtime artifacts and business facts in the target project.

## Four-Layer Structure

### Skills: Workflow Controllers

A skill is an imperative workflow entry point, for example:

- `/t-tools:t-prd`
- `/t-tools:t-prd-preview`
- `/t-tools:t-prd-check`
- `/t-tools:t-design`
- `/t-tools:t-design-check`
- `/t-tools:t-task`
- `/t-tools:t-task-check`
- `/t-tools:t-run`
- `/t-tools:t-demo-run`
- `/t-tools:t-demo-accept`
- `/t-tools:t-push`

The responsibility of a skill is not to "write a prompt and let the model improvise." Its responsibility is to control stage progression:

- Validate inputs and prerequisites.
- Read upstream documents and state.
- Dispatch the appropriate subagent.
- Write standardized artifacts.
- Update task state.
- Provide a recoverable path when failures occur.

In this sense, a skill is closer to a lightweight workflow engine.

### Agents: Specialized Executors

Subagents are split by engineering role, for example:

- `backend-dev`: implements Rust backend features.
- `backend-test`: handles backend scenario tests, integration tests, and acceptance tests.
- `backend-accept`: performs read-only backend acceptance.
- `frontend-dev`: implements the React frontend.
- `frontend-test`: handles Vitest, Testing Library, and MSW tests.
- `frontend-accept`: performs read-only frontend acceptance.
- `prd-preview`: converts Markdown PRDs and user stories into same-directory HTML Previews for human review of product semantics and key paths.
- `demo-dev`: maintains independent Playwright demo/E2E tests based on user stories.
- `demo-accept`: verifies whether demo tests align with user stories, execution results, and test quality expectations.

The key point of this split is responsibility boundaries. Development agents may modify code; test agents focus on tests; acceptance agents are read-only by default and produce evidence-based reports. When something fails, the workflow hands off to the appropriate role instead of making one agent own every responsibility at once.

### Protocols: Shared Contracts

`protocols/` is the single source of truth shared across skills and agents. It defines:

- The state structure of `.ai/task/[feature]/.state.json`.
- The execution order of `phase -> slot -> item`.
- Structured output when an agent completes or fails.
- The `tests_to_run` set that must be returned after a fix.
- The file location, content model, technology boundary, and check scope for PRD HTML Previews.
- Scoring and blocking rules for PRD, design, and task checks.

This avoids having every skill or agent redefine its own fields, state machine, and quality criteria. When a shared rule needs to change, the protocol should be updated first instead of copying the same change across multiple agent documents.

### Guides: Engineering Standards

`guides/` contains concrete engineering standards, such as:

- Backend architecture, testing, validation, and quality gates.
- Frontend development patterns, testing strategy, and `data-testid` standards.
- Demo testing, selectors, Page Objects, and common failure handling.
- Product documentation and user story standards.

Agent documents only describe when to read these guides, how to execute the work, and what to return. They do not duplicate the rules inside the guides. This reduces rule drift.

## Workflow from PRD to Delivery

The recommended full T-Tools path is:

```text
PRD
-> PRD Check
-> Design
-> Design Check
-> Task
-> Task Check
-> Run
-> Backend Finalize
-> Demo Run
-> Demo Accept
```

This path breaks AI programming into product definition, design, task planning, implementation, testing, acceptance, and demo delivery. Every stage has an input contract, an output contract, and quality gates.

The important point is not to skip check or acceptance steps. The value of this project is not only content generation. It is also the ability to close each stage before upstream problems flow downstream.

## t-prd Design: Make AI Output Understandable First

The core change in `/t-tools:t-prd` is not "generate one more HTML file." It changes how humans review AI output.

In a traditional PRD flow, AI can easily produce a thousand lines of Markdown. That structure may be clear to the model, but it is expensive for humans to read: they have to hunt through a long document for the goal, scope, flow, states, permissions, exceptions, and acceptance criteria, then judge whether those pieces contradict each other. If humans cannot understand or finish reviewing the PRD at this stage, design, task planning, and implementation will amplify the wrong understanding downstream.

The purpose of the HTML Preview is to turn the AI's understanding of the requirement into a form that humans can scan, question, and correct quickly. Instead of reading the entire Markdown first, humans can use the Preview to see:

- What problem the AI thinks the feature should solve.
- Which key paths users will go through.
- Which states, boundaries, exceptions, and permissions were considered.
- Which parts are still only assumptions.
- Whether the requirement is clear enough to enter design.

So `/t-tools:t-prd` is closer to a "product-understanding visualization" stage. Markdown remains the formal contract, but the Preview becomes the human entry point for reviewing that contract. It turns product semantics buried in a long document into a scannable, discussable, feedback-friendly interface, so humans can catch AI misunderstandings earlier instead of finding them after technical design or code implementation.

This also changes what `/t-tools:t-prd-check` means. PRD Check is not just a document-format check. It verifies that "the product understanding written by the AI" and "the product understanding humans see through the Preview" are aligned. Only after those two views agree does `/t-tools:t-design` have stable input.

`/t-prd-preview` has been extracted from `/t-prd` into a standalone skill. `/t-prd` triggers it automatically during its workflow, but it can also be invoked independently to regenerate the Preview. Preview output goes to `.ai/preview/<domain>/[feature].html`, outside version control. The PRD no longer tracks implementation progress; it focuses on business rules and target experience.

## Independent Demo Quality Verification

The demo stage is not a duplicate of backend or frontend testing. It is an independent quality verification line. It uses Playwright E2E tests to validate real user paths against user stories, and it treats the test code itself as part of acceptance.

The focus of `demo-dev` is to turn user stories into executable demo tests:

- Identify roles, scenarios, and acceptance goals from user stories.
- Maintain stable tests against the frontend implementation and shared selectors.
- Prefer user-observable behavior over internal implementation details.
- When a failure occurs, determine whether it belongs to the demo test, frontend implementation, or backend implementation, then hand off to the matching agent.

The focus of `demo-accept` is to verify demo quality:

- Whether tests cover the corresponding user stories.
- Whether roles, scenarios, and assertions align with acceptance goals.
- Whether tests compile and execute.
- Whether selectors, waits, Page Objects, and test data setup follow standards.
- Whether every conclusion is backed by evidence such as test files, logs, or command output.

Therefore, the demo stage acts as the quality gate for "deliverable demonstrability" and "user story closure." It validates not only whether code compiles or APIs return responses, but also whether the complete user journey from entry point to result matches product intent.

## Core Execution Model: phase -> slot -> item

`/t-tools:t-task` decomposes the design document into a standard task directory:

```text
.ai/task/[feature]/
|-- .state.json
|-- backend/
|-- frontend/
`-- demo/
```

The execution model has three layers:

- `phase`: `backend -> frontend -> demo`
- `slot`: for example, `dev -> test -> accept`
- `item`: the smallest executable task file

`/t-tools:t-run` executes only items. It does not directly execute manifests such as `index.md`, `dev.md`, `test.md`, or `accept.md`. Manifests are responsible for navigation, dependencies, and summaries; items contain concrete steps, inputs, expected files, verification commands, and completion criteria.

This design allows tasks to be broken down, ordered, retried, and audited.

## Why Items Are Scheduled Serially

`/t-tools:t-run` allows at most one item to be `running` at any time. It will:

- Read `.state.json`.
- Validate the phase, slot, item, and DAG.
- Find the first dependency-satisfied `pending` or `failed` item.
- Mark it as `running`.
- Dispatch the corresponding subagent.
- Write back `completed` or `failed` based on the result.
- Aggregate slot and phase status.

This mechanism trades some concurrency for stronger control:

- Smaller context.
- Easier failure localization.
- Easier state recovery.
- Downstream items do not continue running after upstream failures.
- Every handoff can be recorded.

For long-running projects, this determinism is more important than one-shot parallel execution.

## Quality Gates and Recovery

T-Tools makes quality control explicit:

- `/t-tools:t-prd-check` checks the PRD and user stories.
- `/t-tools:t-design-check` checks the technical design.
- `/t-tools:t-task-check` checks task decomposition, the DAG, and item executability.
- `backend-accept`, `frontend-accept`, and `demo-accept` produce read-only acceptance reports.
- When `/t-tools:t-demo-run` fails, it diagnoses first, then dispatches fixes to `demo-dev`, `frontend-dev`, or `backend-dev`.

A fixing agent must return `tests_to_run`, explaining which backend, frontend, or demo commands should be rerun after the fix. This makes the risk of "demo passes but lower-level regression fails" explicit.

## Local CI Closure Before Push

`/t-tools:t-push` is the daily commit entry point. It does not replace the release workflow. It detects the changed scope from git diff:

- `backend/**` triggers Backend CI.
- `frontend/**` triggers Frontend CI.
- `demo/**` triggers Demo CI.
- Documentation, scripts, or configuration-only changes skip business-area CI and go straight to commit confirmation.

After all affected checks pass, it runs `git add -A`, generates a commit message from the staged diff following project conventions, asks for confirmation, then runs `git commit` and `git push`. If any CI step fails, the flow stops and does not commit or push.

Formal version publishing remains governed by `/t-tools:t-release [version]`; version files use semver without `v`, while git tags use the `v` prefix.

## Design Tradeoff

The core tradeoff of this design is using more structure to reduce uncontrolled improvisation.

It does not try to make AI "finish everything at once." Instead, it emphasizes:

- Requirement semantics are written to `docs/` first.
- Technical plans are written to `.ai/design/` first.
- Execution plans are written to `.ai/task/` first.
- Every item has clear inputs, steps, boundaries, and verification.
- Every agent has clear responsibilities and output contracts.
- Every stage has checks or acceptance.

As a result, T-Tools is closer to engineering rails for AI programming. The model still performs reasoning and implementation, but it must move through documents, state, contracts, and gates.

## One-Sentence Summary

The design focus of T-Tools is not to make the model freer, but to make it more controllable: skills orchestrate the workflow, subagents divide execution responsibilities, protocols solidify contracts, and guides keep engineering behavior consistent, ultimately turning AI programming into a traceable, recoverable, and verifiable long-term workflow.
