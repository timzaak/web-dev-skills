# Do Not Shortcut the Intent

This template is for humans. It is not a checklist for filling every ordinary PRD field. AI can usually infer routine pages, CRUD, loading states, form validation, and API breakdown. What you should speak through is: **the important judgment that AI is likely to guess wrong, but that determines requirement quality and solution direction**.

Its purpose is not to make you “write requirements.” It is to force the real answer into words: what you actually want, why the tradeoff matters, and where AI must not guess.

Aim for 5 to 10 minutes. You do not need to answer every line. Say the most important, most worrying, and most easily misunderstood parts.

-- Getting Started

What I want to build is: [one sentence describing the feature or change].

It needs to solve: [real user pain, business risk, workflow bottleneck, or delivery goal].

After this works, the change I most want users or the business to see is: [observable change].

-- User Story Walkthrough

The core user story is: [role] uses the feature above in [scenario].

The key path is: enter from [entry point], do [key action], and finally see [result] in [place].

The part that must not be missed is: [entry, decision point, feedback, state, permission, or data result], because: [reason].

What needs serious thought is: [common but wrong generic interpretation or scenario].


-- UI/UX Walkthrough

In the UI interaction, the user must understand at first glance: [conclusion, state, next action, or risk warning].

When the state is abnormal, failed, permission-denied, or waiting on a third party, the user must know: [what happened, whether retry is possible, whether the result was saved, what to do next].

For page design, refer heavily to [design standards, existing pages].


-- Third-Party Integration Walkthrough

This work needs to integrate with [third-party platform], which must provide: [...]. Look closely at [local docs, official docs]. If its capabilities do not satisfy the need, tell me clearly. Also check whether it fits the existing tech stack and whether suitable SDKs are available.

During the integration, pay special attention to [idempotency, duplicate requests, unordered requests, cascade deletion, audit, error recovery].

-- Third-Party Library Introduction

I want to introduce [third-party library], which must provide: [...]. Search online for whether a better library exists. My evaluation standards are: [popular, simple, fits the current tech stack, does not introduce too many additional third parties].

-- Closing

Think through the above in detail, search the web for how similar products handle this and what related best practices look like, and ask me if anything remains uncertain. Write the above content and the answers into `.ai/future/[feature].md`.
