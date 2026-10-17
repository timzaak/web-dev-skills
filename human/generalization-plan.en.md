# Learning domain knowledge from real projects: proposed design

Status: proposal. This document designs future capabilities; no knowledge command, registry, or automatic publishing mechanism has been implemented. The general branch first removes production-domain presets and retains generic implementation, Web Demo, Figma, and existing quality/recovery contracts.

## 1. Objective and scope

Accumulate useful practices from actual delivery so later agents can locate, understand, verify, and reuse them. A local convention must not silently become a universal plugin default.

The plugin owns workflow structure; technical knowledge belongs first to the target project. Ordinary work does not require building a knowledge base first: existing AGENTS.md, code, configuration, and explicit user instructions remain valid inputs. Confirmation is needed when work depends on an unresolved choice or knowledge is explicitly being published. Optional checks remain optional; independent acceptance still closes implementation.

## 2. Assets and ownership

| Layer | Proposed location | Content | Consumption |
| --- | --- | --- | --- |
| Evidence | .ai/knowledge/<topic>/evidence.md | Actual paths, dependency versions, scripts, CI, representative implementations and results | Research facts only |
| Proposal | .ai/knowledge/<topic>/proposal.md | Alternatives, evidence, costs, decisions and proposed publication diff | Discussion, never an execution constraint |
| State | .ai/knowledge/<topic>/.state.json | Step, source fingerprints, proposal revision, decisions, errors and recovery | Knowledge skill owns progression |
| Decisions | .ai/decision-log/<feature>.md | Existing DEC/Q identifiers and supersession | Active decisions authorize publication; formal rules retain conclusions and rationale |
| Project rules | docs/engineering/index.md and <topic>.md | Scope, minimal rules, evidence, command navigation and maintenance conditions | Published, applicable and current |
| Repeatable operations | Project scripts/ | Verified operations that benefit from deterministic execution | Real project entrypoints |
| Portable packs | Separate, opt-in domain packages | Generalized candidates and applicability conditions | Re-evaluated and confirmed in each project |

Skills orchestrate and persist; agents execute one role or inspect read-only; future shared fields, state and gates belong in one knowledge protocol; project guides hold engineering practices. This proposal does not act as a runtime contract.

AGENTS.md links to the project engineering index. scripts/index.md remains the single source for command instructions; knowledge rules link to its entries instead of copying tables. Reuse an existing project documentation layout rather than creating a competing source. Plugin references retain ${CLAUDE_PLUGIN_ROOT}.

## 3. Extract facts before proposing choices

1. Read the current topic's project instructions, manifests/lockfiles, CI, scripts and representative implementation. Record paths, content fingerprints, versions and context; avoid importing the entire repository.
2. Collect successful examples, relevant failures and actual verification evidence. One file demonstrates a local observation, not team consensus.
3. Separate explicit existing constraints, proven facts, unconfirmed preferences and unknowns. Reuse existing decisions; show conflicting practices with their sources rather than blending them.
4. For consequential choices, present 2–4 internally consistent alternatives covering module boundaries, dependencies, test ownership, gates and evidence, with benefits, costs, migration effects and applicability. Do not invent alternatives for simple established facts.
5. Show the concrete proposed rule diff, scope, conflicts and failure behavior for user decision. Reuse valid prior authorization. A request for best practices does not approve a particular new preference.

Unanswered choices stay in proposals and Q records. They cannot become published rules, AGENTS.md instructions or role constraints. Unrelated work can continue. Organizing facts alone does not authorize new mandatory engineering gates.

## 4. Publish a reviewable project baseline

Propose one narrowly scoped t-knowledge entry for extraction, confirmation and materialization. It does not implement features, run the delivery chain or replace technical research.

Proposed explicit actions are propose, publish and resume. Publishing requires a selected concrete candidate, current sources, a visible publication diff and required verification. Prepare reviewable artifacts before the final confirmation, reusing authorization already given for the same scope.

Record decisions through the existing continuity contract, write the minimal confirmed rules and update the index. Do not change production implementation, plugin phases or default roles. Each rule records a stable ID, applicable paths/versions/conditions, its instruction and strength (required, recommended or example), rationale, evidence summary, confirmation basis, verification entry and invalidation conditions. Skip information that would not change later decisions.

Formal rules use stable rule IDs, retaining selected conclusions and reasons without depending on temporary DEC/Q ledgers that publication may remove. The temporary publication manifest maps decisions to rule IDs. Preserve source paths, versions/content fingerprints and verification conclusions in evidence summaries; raw logs are supplementary and their cleanup alone does not erase a rule’s basis.

Record old/new fingerprints, backups, targets and completed steps in the publication manifest. Prepare the complete publication set before replacing formal files sequentially, updating the index last. Reconcile user edits before recovery rather than assuming the state string proves success. Failed publication preserves the previous baseline and recovery step; mark the batch published only when all outputs agree. Generic roles load only rules relevant to their current module.

## 5. Learn incrementally from delivery

Candidates come from rejected acceptance, confirmed diagnoses, regressions, invalid commands and verified engineering decisions. Include trigger, failure facts, root-cause evidence, fix, verification, applicability and counterexamples.

Acceptance and diagnosis roles only propose candidates. The knowledge skill deduplicates, links existing rules and produces a diff. Acceptance cannot change its own criteria while judging an implementation; each delivery does not automatically add policy.

Promotion depends on reuse value and adequate evidence, not a recurrence counter. A single high-impact failure can justify a proposal, while repeated failures may be the same unresolved defect. Rules must change future decisions and offer observable verification; incidental observations remain in reports.

## 6. State, recovery and invalidation

A future shared protocol should define draft -> awaiting-decision -> confirmed -> publishing -> published. Tool/write failures enter failed with the failed step and last valid artifacts. Resume from disk and unmet conditions, without repeating still-valid decisions.

- Deduplicate extraction by topic, source fingerprint and rule ID.
- Source changes before publication return the affected proposal to draft and show the diff; only affected preferences need reconfirmation.
- Interrupted publication reconciles formal files, temporary files and its manifest; finish the same batch or restore the old baseline without overwriting user edits.
- Changed dependencies, versions or commands mark affected published rules stale. Consumers must not enforce stale guidance. Continue unrelated work supported by current facts; expose unresolved choices.
- Conflicts use the existing supersession ledger, preserving reasons and evidence rather than stacking contradictory practices.
- Rules changing plans or evidence reopen affected work and acceptance under existing verification rules. New policy cannot retroactively prove a delivery correct.

Use content fingerprints, not existence checks alone. Distinguish a command's existence from a successful run in the current context. CI and environment operations remain project-owned.

## 7. Integration with existing entrypoints

| Entry | Future integration |
| --- | --- |
| t-init | Detect existing rules and real commands, establish navigation; never silently select architecture |
| t-decision / t-tech-research | Expose alternatives and unknowns; product changes still return to PRD |
| t-design | Load applicable confirmed rules and reference IDs/revisions |
| t-task / t-super-run | Persist only relevant paths/revisions; do not copy knowledge or mutate plugin contracts |
| project-dev / project-test | Consume rules within role boundaries; return observations as candidates |
| project-accept / t-dream | Independently detect drift and return evidence |
| review / simplify / push | Preserve the quality chain, revalidate invalidated evidence, reject missing project CI |

Current implementation plus optional web-demo is sufficient; do not register a new phase per language. Only genuine independent delivery/recovery boundaries would justify future project phase descriptors, which require a single complete contract covering registration, ordering, roles, state validation, consumers and compatibility. Accepting arbitrary phase strings alone would bypass shared contracts.

Web Demo and Figma remain bundled. URLs, identities, modules and verification commands still come from the target project and cannot reintroduce production stack defaults.

## 8. Cross-project reuse

First demonstrate value locally. Extract reusable content while preserving supported versions, prerequisites, counterexamples and project-specific differences. Portable packs are inactive candidates by default; a new project compares its own facts and team preferences, then adopts, adapts or rejects them.

[Existing classic-stack and Java templates](/templates/index.md) now preserve prior domain experience and export matching standalone runtimes. These explicitly selected historical sources do not implement automatic project knowledge extraction or publication. Maintain them separately from the generic runtime using the [merge guide](/human/merge-main.en.md).

The first implementation should support the project-local loop only. A global marketplace, automatic recommendation scoring and automatic upstream publication are outside this proposal's first delivery.

## 9. Delivery and acceptance

| Delivery | Scope | Evidence |
| --- | --- | --- |
| Current general branch | Remove presets, generic roles/phases, retain Web Demo/Figma, update docs | Links, design gates, project hooks, CI failure/recovery and Demo helpers |
| Project pilot | Knowledge protocol, minimal t-knowledge, project navigation | Complete facts -> alternatives -> user choice -> publication -> role consumption in one real project |
| Feedback iteration | Candidates, deduplication, invalidation and recovery helpers | No duplicate rules; drift review; interrupted writes preserve baseline; independent acceptance |
| Proven reuse | Opt-in portable domain packs | A second different project can selectively adopt without changing workflow structure |

Behavioral cases: reuse valid existing rules; expose conflicting practices; missing commands or zero cases cannot be published as verified; unanswered choices never reach formal rules; failed publishing preserves the baseline; changed sources invalidate affected approvals; identical inputs do not duplicate outputs; rule changes reopen affected evidence; non-Web projects do not gain Demo assets; retained Web Demo/Figma work against real project facts.

Success means a maintainable project knowledge baseline that later roles can consume selectively, not a larger number of knowledge files.
