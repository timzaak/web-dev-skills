# Generalizing T-Tools: Structural Process and Domain Knowledge

T-Tools ships with a built-in family of engineering domains: Web, Chrome extension, mini-program, Flutter, user-story demos, and Figma. Adapting it to other kinds of development work — data engineering, machine learning, CLI tools, games, embedded — does not require rewriting the workflow. It requires answering one question first: which parts of this system are independent of the type of project being built, and which parts must change with it.

The answer is a two-layer separation:

- **Structural process**: stage orchestration, execution loops, state and recovery, quality chains, acceptance gates. It is domain-agnostic. When adapting a new domain, run it as-is under the existing conventions and do not modify it.
- **Domain knowledge**: the phase set, per-role specs, test and validation commands, engineering practice preferences. It is derived from the characteristics of the target project and comes from summarizing best practices of similar projects. Since the same class of project usually admits several equally valid best practices, the final tradeoff must be made by a human — never silently picked by the AI.

## The Structural Layer: Run It As-Is

The following is independent of project type and belongs to the structural layer. Adapting a new domain does not modify these; it only registers the new domain into them:

- Main-path orchestration: after `t-decision`, branch by the primary unknown into `t-prd` / `t-tech-research` and converge before `t-design`; after implementation, close with accept, `t-push` local CI, and `t-release`.
- Phase execution loops: `t-super-run`'s outcome-level planning, main-session dev/test, and read-only accept; the `phase -> slot -> item` model of the standard path.
- State and recovery: the `.state.json` / `.pipeline.json` state machines, evidence invalidation and reopening, resuming with the same command from disk after an interruption.
- Quality chain: the fixed `review --fix -> simplify -> push` order, plus "no push while unfixed correctness findings exist".
- Gate shape: accept defaults to read-only with verifiable evidence; splitting heuristics that scale process weight with complexity; slot limits that trigger user confirmation.

To decide whether a rule is structural or domain knowledge, apply a substitution test: swap the project from a Web app to a data pipeline — does the rule still hold?

| Rule | Layer |
| --- | --- |
| Same failure three times without progress becomes `blocked` | Structural |
| accept is read-only and outputs evidence | Structural |
| When to insert a test slot | Structural (the rule itself) |
| backend runner commands must start with `uv run scripts/backend-test.py --` | Domain |
| Playwright locators use `data-testid` | Domain |
| Which commands run inside a test slot | Domain |

## t-super-run-all: Evidence the Structure Is Already Decoupled

The `t-super-run-all` skill in git history (added in commit `f87bf32`, removed in `94f4549`) is the most direct evidence that the two layers are decoupled. It was an unattended pipeline entry point: once design was complete, a single manual invocation authorized the whole chain, running every remaining active phase in order. Each phase first ran the `t-super-run` loop, then the quality chain `review --fix -> simplify -> push`; only after all of it passed did the pipeline move to the next phase.

How it was built shows the structural layer holds no domain knowledge:

- The phase order was defined as a "fixed projection" of the default order in [task-phase-execution.md](/protocols/task-phase-execution.md), taking only the entries hit by `active_phases`. The pipeline itself contained no knowledge of any phase's content.
- Every iteration first ran `super-run-next.py` to compute the next action from persisted state; advancing from memory was forbidden. The script only read state and contained no domain judgment.
- The `.pipeline.json` cursor, the `failures_without_progress` counter, the three-failures-without-progress escalation to `blocked`, and the stop conditions were all domain-agnostic rules.
- `t-prd-publish` and `t-release` stayed out of the chain and remained manual.

It was removed one day later, replaced by explicit `t-super-run --phase` invocation phase by phase. Note the removal diff: READMEs, protocols, scripts, and reference fixes in a few skills — `guides/` and `agents/` were untouched. A purely structural component could be added and removed wholesale without touching any domain content; that is what decoupling looks like.

The episode also shows the structural layer carries its own tradeoffs. Unattended chaining buys speed; explicit per-phase invocation buys control points — a risk preference, not domain knowledge. Such tradeoffs are decided once and evolve with the repository normally; each new domain does not re-adjudicate them.

## The Domain Layer: Summarize Candidates First, Then Let a Human Choose

Today's domain knowledge lives in these places:

- The `supported_phases` set and per-phase activation conditions in [task-phase-execution.md](/protocols/task-phase-execution.md).
- Per-domain `*-dev` / `*-test` / `*-accept` role specs under `agents/`.
- Development patterns, test strategy, validation commands, and quality gates under `guides/<domain>/`.
- Concrete validation commands and test infrastructure: `uv run scripts/backend-test.py`, `npm run test:run`, `flutter test`, the Playwright / Patrol runners.
- Demo shape: Playwright E2E for Web and extensions, Android Patrol for Flutter.
- `t-init` project templates.

### Why a Human Must Choose

A class of project never has exactly one best practice. Backend testing can lead with scenario tests or with high-value unit tests; the boundary between frontend state management, component tests, and page E2E has several valid organizations; a CLI tool's "demo" can be a golden-output test or a recorded terminal replay. These choices have no objective optimum — only a better or worse fit with the team, the project stage, and the risk appetite.

Once a guide is written, every later dev / test / accept run reads and executes it. Making the preference choice once at adaptation time is cheapest; changing it mid-implementation means overturning constraints already on the rails. Silently writing an unconfirmed best practice into artifacts and continuing is exactly what repository rules forbid: gaps that need user adjudication must be surfaced to the user.

So the human choice in the generalization flow is not optional polish — it is the precondition for the domain layer to enter the main path. The existing mechanisms already reserve the place: `t-decision` branching, the decision-continuity contract, and `AskUserQuestion` confirmations are the recording channels for this choice.

## The Generalization Recipe

When adapting a new class of development work, proceed in this order:

1. **Confirm the structural layer suffices.** Does the new work still close the loop "requirement → design → implementation → testing → acceptance → wrap-up"? Nearly all development work does. The structural layer stays untouched.
2. **Start from the project's characteristics.** Read the target project itself: languages, frameworks, build and test tooling, existing scripts. Validation commands must come from the target project's real scripts — this existing rule is the anchor of the domain layer, and it prevents practices the project cannot even run.
3. **Summarize candidate best practices from similar projects.** Prepare 2–4 candidate sets, each internally consistent: architecture organization, test strategy, and validation gates must appear as a set, not be mixed into internal contradiction. Write down each set's cost and its effect on gates and evidence shape.
4. **A human makes the preference choice.** Hand the candidates and their tradeoffs to the user for adjudication, recorded through the existing decision mechanisms (stable DEC IDs or decision documents). Unconfirmed assumptions must not be written into guides or agents.
5. **Materialize the domain layer.** Land the choice: add `guides/<domain>/`; register the new phase in `task-phase-execution.md` with its activation conditions and default-order position; add the matching `*-dev` / `*-test` / `*-accept` agents; put deterministic, repeatable operations into `scripts/`; update `t-init` templates and the READMEs.
6. **Acceptance shape follows the domain; the acceptance bar does not.** accept stays read-only and evidence-based. Domain knowledge changes what the evidence looks like — which commands, which output, which demo form; it does not change "verifiable evidence is mandatory".

Not one of the six steps modifies the structural layer. If a new domain genuinely forces a structural change (say, no recoverable item boundary can be defined), you have hit a structural problem: handle it through the structural layer's normal evolution and sync the whole repository, rather than patching around it in the domain layer.

## Closing

T-Tools' capacity for generalization is not measured by how many domains it ships with, but by how clean the boundary between structural process and domain knowledge is. The structural layer supplies the rails: recoverable, verifiable, gated. The domain layer supplies the content: derived from project characteristics, summarized from similar projects, and landed after a human preference choice. The cost of adding a class of development work should approach "summarize candidate practices + one human choice + materialize one set of guide / agent / phase registrations", not a workflow redesign.
