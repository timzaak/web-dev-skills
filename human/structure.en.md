# T-Tools structure

T-Tools separates engineering workflow from project domains: the plugin owns reliable progression; the target project supplies concrete engineering rules.

| Location | Responsibility |
| --- | --- |
| skills/ | Orchestration, prerequisites, role selection, state, recovery and aggregation |
| agents/ | One execution or independent read-only review role, never cross-stage orchestration |
| protocols/ | Single shared contracts for state, outputs, scoring, dispatch and gates |
| guides/ | General practices plus retained Web Demo/Figma guides |
| scripts/ | Repeatable operations requiring deterministic execution |
| templates/project-profiles/ | Opt-in domain sources exported with a pinned matching runtime |
| human/ | Explanations and proposals, never runtime state |

## Main workflow

After a decision, route to PRD or technical research by the main unknown and converge before design. Only purely technical work preserving product semantics can use research alone. Design follows real modules with project-design. Generic project-dev/test/accept implement, test and independently accept implementation; Web Demo retains separate roles.

Default t-super-run combines goal-level planning and execution: the main session performs dev/test, while acceptance is independently dispatched. Each call executes one explicit phase, persists in .ai/super-run/<feature>/ and resumes with the same command. For separate plan review, t-task -> t-run uses serial phase/slot/item execution and .ai/task/<feature>/. Their states are independent and are not migrated.

## Sources and gates

Project code/configuration establish implementation facts; AGENTS.md and confirmed project documents establish engineering constraints. Shared structures are in the [protocol index](/protocols/index.md), with [runtime boundaries](/protocols/runtime-boundaries.md). Commands must exist; missing/failing commands cannot fall back to another stack.

Prechecks remain optional; post-implementation acceptance requires reviewable evidence. Later changes reopen affected work and acceptance when evidence is invalid. The quality chain is review --fix -> simplify -> push, followed by the explicit release entry.

## Domain knowledge

The plugin no longer bundles production-domain guides, implementation roles or application scaffolds. Knowledge comes from actual implementation and verification. New preferences require human selection before becoming formal rules. See the [generalization rationale](/human/generalization.en.md) and [proposal](/human/generalization-plan.en.md).

Skill deliverables use the [authoring guide](/guides/core/skill-authoring.md) and [behavioral testing guide](/guides/core/skill-testing.md). Load Web Demo/Figma resources through their respective indexes rather than loading every guide.
