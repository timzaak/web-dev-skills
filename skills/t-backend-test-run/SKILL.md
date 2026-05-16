---
name: t-backend-test-run
description: Run targeted Rust backend tests, diagnose failures, delegate production-code fixes, and retest without weakening scenario-test semantics.
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Task
  - Agent
---

# Backend Test Run

Runtime boundaries: `protocols/runtime-boundaries.md`

本 skill 只负责 backend/test runner item 的测试执行、失败诊断、生产代码修复编排和重测。它不编写新场景测试，不改变业务验收语义。场景测试 authoring 属于 `backend-test` authoring item。

## Core Workflow

1. Analyze scope with `git status` and `git diff --name-only`.
2. Choose the narrowest reliable command from `protocols/backend-test-execution.md`.
3. Run targeted tests via `${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py`.
4. Classify failures as compilation, runtime, assertion, environment, or unclear semantics.
5. Delegate production-code fixes to `backend-dev` with scenario-test write restrictions.
6. Rerun the targeted command.
7. Escalate to full suite only when the user asks or the targeted scope is no longer reliable.

## Semantic Safety

The runner may fix only mechanical test issues such as imports, module registration, helper call signatures, or obvious path mistakes.

The runner must not change:

- scenario-test assertions
- status-code expectations
- permission expectations
- business-rule expectations

If test semantics may be wrong, stop and use the stop report from `protocols/backend-test-execution.md`.

## Delegation Contract

When delegating to `backend-dev`, use `Agent(subagent_type="backend-dev")` and include in the prompt:

```markdown
Task: Fix this backend test failure in production code.

Test command: `<command>`
Failing test: `<test_name>`
Failure: `<message>`
Relevant docs: `<User Story/PRD paths>`
Reason implementation appears wrong: `<diagnosis>`

Hard constraints:
- Do not modify `backend/**/tests/scenarios/**`.
- Do not modify any `*_scenarios.rs`.
- Do not change scenario-test assertions, status-code expectations, permission expectations, or business-rule expectations.
- If a test semantics change seems required, return `requires_test_semantics_change` with evidence instead of editing tests.
```

## Report

Report the commands executed, pass/fail result, fixes applied, files changed, semantic conflicts, and whether full-suite escalation was used.

## Shared References

- `protocols/runtime-boundaries.md`
- `protocols/backend-test-execution.md`
- `protocols/tests-to-run-contract.md`
