# Generalizing T-Tools: workflow structure and domain knowledge

Generalization separates reliable workflow structure from domain knowledge derived from real projects and confirmed by people. The general branch removes production stack presets, retaining generic implementation, optional web-demo and Figma. The [knowledge workflow](generalization-plan.en.md) remains a proposal, not an implemented capability.

## Workflow structure

Orchestration, goal-level or phase/slot/item execution, disk recovery, invalidation, quality chains and independent read-only acceptance do not depend on a project's implementation language.

Replace the project with a data pipeline, CLI or another delivery type: a rule still applying is usually structural; a rule changing with framework, language or team preference is domain knowledge.

| Rule | Ownership |
| --- | --- |
| Three identical failures without progress become blocked | Structure |
| Independent read-only acceptance with reviewable evidence | Structure |
| Whether new test assets require a test role | Structure |
| Test framework and concrete commands | Domain |
| Architecture, module organization and team preferences | Domain |

The historical t-super-run-all illustrated a structural component that could be added or removed independently: it orchestrated phases, recovery and quality checks without owning implementation knowledge. Explicit phases versus unattended execution is a structural risk tradeoff, not a choice each new domain must redesign.

## Domain knowledge

Knowledge covers module organization, role practices, testing, verification entrypoints and evidence forms. Project names, one directory or model preferences cannot establish rules; first read actual instructions, code, configuration, scripts and confirmed documentation.

Similar projects may support several valid approaches. Present coherent alternatives, costs, applicability and gate effects, then obtain a human choice. Reuse valid decisions; unresolved choices must be exposed before formal rules or dependent work proceed.

## Current baseline

Skills orchestrate; generic project-design/dev/test/accept roles each own one responsibility. Designs follow actual project modules. implementation handles development/testing; web-demo activates only for real Web story delivery. CI, environment and validation come from project entrypoints, with no application environment defaults.

Web Demo and Figma practices remain bundled and consume project facts without selecting production frameworks. Shared phase, state and output contracts stay centralized. Removing presets does not remove recovery or acceptance gates. Preserve old domain state and replan instead of silently treating it as completed.

## Existing optional templates

Migrated domain assets, including the Java branch backend, remain in the [catalog](/templates/index.md). They export standalone runtimes from pinned sources and require explicit selection. Generic workflows do not load them automatically. See the [main merge guide](/human/merge-main.en.md).

## Future learning

Extract facts, propose evidence-based alternatives, obtain a choice and publish minimal project-local rules. Actual failures and verification produce incremental candidates; source drift triggers re-evaluation. Cross-project experiences remain opt-in candidates instead of automatic plugin defaults.

See the [proposal](generalization-plan.en.md) for artifacts, confirmation, publication recovery, invalidation, integration and acceptance cases.
