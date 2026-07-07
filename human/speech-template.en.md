# Do Not Shortcut the Intent

This template is for humans. It is not a checklist for filling every ordinary PRD field. AI can usually infer routine pages, CRUD, loading states, form validation, and API breakdown. What you should speak through is: **the important judgment that AI is likely to guess wrong, but that determines requirement quality and solution direction**.

Its purpose is not to make you “write requirements.” It is to force the real answer into words: what you actually want, why the tradeoff matters, and where AI must not guess.

Aim for 5 to 10 minutes. You do not need to answer every line. Say the most important, most worrying, and most easily misunderstood parts.

## 1. Why This Really Matters

What I want to build is: [one sentence describing the feature or change].

This is not just another feature; it is meant to solve: [real user pain, business risk, workflow bottleneck, or delivery goal].

If AI remembers only one point, it should be: [the core judgment].

After this works, the change I most want users or the business to see is: [observable change].

## 2. The User Story Must Not Drift

The most important user is: [role], using it in: [scenario].

The key path is: enter from [entry point], do [key action], and finally see [result] in [place].

The part that must not be missed is: [entry, decision point, feedback, state, permission, or data result], because: [reason].

AI should not generalize this user story into: [common but wrong generic interpretation or scenario].

## 3. Product Boundaries and Tradeoffs

This release must include: [a few must-deliver capabilities].

This release explicitly does not include: [scope AI may otherwise expand into].

If time, cost, or complexity conflicts, protect: [highest-priority capability or user path].

Things that can be sacrificed or delayed are: [lower-priority capability, automation, reporting, configuration, batch operations, experience details, etc.].

## 4. What the User Must Understand

At first glance, the user must understand: [conclusion, state, next action, or risk].

The most important information is not “more fields”; it is: [the information that truly affects user judgment].

When the state is abnormal, failed, permission-denied, or waiting on a third party, the user must know: [what happened, whether retry is possible, whether the result was saved, what to do next].

I do not want the page to become: [AI's common but unacceptable display pattern, such as field dumping, too many cards, unclear flow, or unexplained states].

## 5. Permissions, Data, and Risky Operations

The most important permission boundary is: [who can view, who can edit, who only maintains, who must not touch it].

The most important data boundary is: [personal, team, tenant, realm, global, third-party account, etc.].

Risky operations include: [delete, refund, retry, close, authorize, export, sync, overwrite data, etc.].

These operations must have: [confirmation, audit, idempotency, rollback, read-only fallback, permission explanation, or other constraint].

AI must not assume: [roles, permissions, cross-tenant access, billing, compliance, or dangerous operation rules].

## 6. What Technical Research Must Clarify

If a third-party API is involved, the capability I really need is: [core capability].

The important question is not just “can we integrate it,” but: [the gap between official capability and our expectation, such as payments vs invoices, subscriptions, refunds, webhooks, rate limits, regions, compliance].

The likely conflict with the current tech stack is: [backend SDK, frontend SDK, version, runtime, auth method, deployment model, license, maintenance status].

The backend issue that needs early thinking is: [data model relationship, state machine, idempotency, duplicate request, concurrency, cascade delete, audit, data retention].

If webhooks or async flows exist, the main concern is: [out-of-order delivery, duplicate delivery, signature verification, retry, timeout, eventual consistency].

## 7. My Biggest Risks and Unknowns

The product risk I worry about most is: [user confusion, too long a path, permission misuse, high-cost wrong action, unexplained state, etc.].

The technical risk I worry about most is: [third-party limits, idempotency, ordering, data consistency, performance, compatibility, deployment complexity, etc.].

If only one risk can be solved first, I would solve: [risk], because: [reason].

What I have confirmed is: [confirmed decisions].

Questions that must be asked of me are: [questions that would change PRD, feasibility, or design direction].

What AI can investigate by itself is: [codebase facts, existing docs, dependency versions, official APIs, best practices].

## What AI Should Do After Ingesting This

AI should not directly expand the walkthrough into a long document. First output a “key understanding”:

- The 3 to 5 most important user stories and product boundaries.
- The highest-priority path, must-preserve capability, and explicit out-of-scope items.
- Permission, data boundary, and risky operation points that must not be guessed.
- Technical research focus: third-party APIs, stack compatibility, idempotency, webhooks, data consistency.
- Executability and feasibility judgment: what can enter PRD, what needs technical research first, and what belongs in design.
- Gap handling: what AI can verify, and what must be asked of the user.

AI must separate confirmed facts, user preferences, AI inferences, and open questions. Guesses in the spoken walkthrough must not be written as confirmed conclusions.
