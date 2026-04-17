---
name: t-backend-test-run
description: >
  后端测试运行器，支持自动错误检测与修复编排。分析代码变更，使用 nextest filtersets 运行定向测试，
  捕获错误，创建修复计划，并通过 backend-dev subagent 编排修复。
  是 /t-run 触发的 backend-test slot 的默认执行路径，也是 /t-task 生成 backend-test slot 的默认规划约束。
  当测试与实现冲突时，以 PRD/用户故事为优先级仲裁。
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Task
---

# Backend Test Run with Auto-Fix

## Runtime Dependencies

The following paths are target-project runtime dependencies, not plugin-owned resources:
- `spec/`
- `docs/`
- `.ai/`

Plugin-owned references should stay within `skills/`, `agents/`, `protocols/`, and `scripts/`. External paths only refer to files in the target project repository.

Orchestrates the complete test-fix-retest cycle for CAS Rust backend using `cargo nextest`.

## Core Workflow

### 1. Analyze Changes

```bash
git status
git diff --name-only
```

Map changes to test commands:
- Single test or helper impact → `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- <test_name>`
- Single crate / module impact such as `backend/core/src/domain/points/*` → `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- -E 'package(points)'`
- API-layer impact such as `backend/api/src/*` → `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- -E 'package(api)'`
- Multiple local impacts in one crate → `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- -E 'package(<crate>) and test(<pattern>)'`
- Cross-crate or unclear impact → document why targeted scope is insufficient, then escalate to full `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py`

### 2. Run Tests

Default rule: start with the narrowest reliable command. Full-suite execution is escalation, not the default.

**Basic commands:**
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py                           # All tests
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- <test_name>            # Specific test
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- -E 'package(<crate>)'   # By package
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- -E 'test(<pattern>)'    # By name pattern
```

**Advanced filtering:**
```bash
-E 'package(<crate>) and test(<pattern>)'  # Combine conditions
-E 'deps(<crate>)'                          # Package + dependencies
-E 'test(p1) + test(p2)'                    # Multiple patterns (OR)
-E 'not test(<unwanted>)'                   # Exclude
```

### 3. Parse Errors

Extract and categorize:
- **Compilation errors**: `error[E...]`, syntax, type mismatches
- **Runtime errors**: panics, unwraps, index out of bounds
- **Assertion failures**: test expectations not met
- **Infrastructure issues**: database, network, environment

Create error list with: test name, location, type, message, context.

### 4. Create Fix Plan

```markdown
# Backend Test Fix Plan

## Summary
- Total: <count> | Compilation: <count> | Runtime: <count> | Assertions: <count>

## Priority Order
1. [ ] Compilation errors (block all)
2. [ ] Runtime errors
3. [ ] Assertion failures
4. [ ] Escalate to full re-test only if targeted scope is no longer reliable

## Fixes
### Error 1: <description>
- Test: `<test_name>`
- File: `<file>:<line>`
- Action: <what to fix>
```

**Group by:** root cause, then module/file to minimize context switching.

### 5. Execute Fixes

Implementation ownership:
- `t-backend-test-run` coordinates the workflow and may update tests it owns
- Production-code fixes should be delegated to `backend-dev`
- If behavior is ambiguous, consult `docs/user-stories/` and `docs/prd/` before changing either test or implementation

For each error:

```bash
# Spawn backend-dev subagent with:
Task: Fix this backend test failure

Test: <test_name>
Error: <error_message>
File: <file_path>:<line>

The test is failing because: <details>

Consult docs/prd/ and docs/user-stories/ if behavior is ambiguous.

# After fix, verify:
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- <test_name>
# or
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- -E 'package(<crate>)'
```

Mark complete in fix plan after verification.

### 6. Verify & Report

```bash
# Targeted verification first
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py -- <targeted filter>
```

Only escalate to:
```bash
uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py
```
when the user explicitly asked for full coverage or targeted verification can no longer bound the impact.

```markdown
# Backend Test Run: Complete ✅

## Results
- Tests run: <count> | Passed: <count> | Failed: <count>
- Duration: <time>

## Fixes Applied
<list with file references>

## Next Steps
<recommendations>
```

## Conflict Resolution

When test vs implementation disagree:

**Priority:** User Stories > PRD > Existing Tests

**Check:**
1. `docs/user-stories/` - Committed behavior
2. `docs/prd/` - Product requirements
3. Existing passing tests - Established patterns

**Decision:**
- Implementation contradicts user story → Fix implementation
- Test contradicts user story → Fix test
- Both contradict user story → Escalate to user

**Document:**
```markdown
## Resolution: <test_name>
- Conflict: Test expects X, implementation does Y
- Consulted: User Story <US-ID>, PRD <section>
- Decision: Fixed <implementation|test>
- Reason: <explanation>
```

## Error Recovery

**Timeout/hang:**
```bash
timeout 60 uv run ${CLAUDE_PLUGIN_ROOT}/scripts/backend-test.py
```

**Compilation cascade:**
- Fix first error per file
- Re-compile before continuing (errors may be phantom)
- Focus on `core/src` → `api/src`

**Same root cause:**
- Group by root cause
- Fix once, verify multiple tests pass
- Update fix plan

## Progress Reporting

After each phase:
```markdown
## Test Run Progress
- Phase: <Analyze|Run|Parse|Fix|Verify>
- Status: <In progress|Complete|Blocked>
- Details: <brief update>
```

Be transparent about:
- Error count found
- Estimated fix time
- When user input needed
- Unexpected issues

## Success Criteria

✅ All targeted tests pass
✅ No compilation errors
✅ No runtime errors
✅ Fix plan fully executed
✅ User informed of all changes
✅ Full-suite escalation is only used when explicitly justified
