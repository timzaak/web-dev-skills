# Using t-tools in Other AI Coding Tools (Codex / ZCode)

This guide explains how to use this Claude Code plugin in AI coding tools that **do not support `claude --plugin-dir` loading, but do support a skills directory** — such as Codex and ZCode.

The core problem it solves: the plugin's native entry point is `/t-tools:t-*`, which relies on Claude Code's plugin loader. Other tools lack that loader, but they all discover and load skills from the unified `~/.agents/skills/` directory (a convention of the [open agent skills ecosystem](https://github.com/vercel-labs/skills)). So the adaptation is not to copy the whole plugin into the skills directory. Instead, place a **thin dispatcher skill** under `~/.agents/skills/` that routes `/t-tool <skill-name>` to this repo's `skills/<skill-name>/SKILL.md` after `git clone`.

## Why This Design

- **Single source of truth**: the repo's skills, agents, protocols, and guides are maintained in one place and updated via `git pull`. The `~/.agents/skills/t-tool/` dispatcher is just an entry point and rarely changes.
- **Path passthrough**: the dispatcher injects the repo root as `${CLAUDE_PLUGIN_ROOT}`, so sibling resources (`agents/`, `protocols/`, `guides/`, `templates/`, `scripts/`) keep resolving via their original semantic paths — no plugin loader required.
- **Stable triggering**: the `description` contains `/t-tool`, so the model reliably invokes the skill when the user types the slash command.

## Prerequisites

- This repository has been `git clone`d to a fixed path, e.g. `~/code/skills` or `C:/code/ai/skills`
- The target AI tool loads skills from `~/.agents/skills/` (Codex, ZCode, Cursor, Cline, etc. all do)
- Context7 MCP is configured (see [Install Context7](#install-context7) below)

## Installation Steps

### 1. Clone this repository to a fixed path

```bash
git clone <repo-url> ~/code/skills
```

All subsequent `${CLAUDE_PLUGIN_ROOT}` references point here, so pick a location you will not move often. Below, `<CLONE_PATH>` denotes it.

### 2. Create the dispatcher skill

Create `~/.agents/skills/t-tool/SKILL.md` with the content below. Replace `<CLONE_PATH>` with your clone path from step 1 (use forward slashes on Windows, e.g. `C:/code/ai/skills`), and `<Agent>` with your tool name (e.g. `Codex`, `ZCode`):

````markdown
---
name: t-tool
description: Dispatcher for the t-tools plugin. Use when the user types "/t-tool <skill-name>".
---

# t-tool — t-tools Plugin Dispatcher

Entry point for the **t-tools** plugin at `<CLONE_PATH>`. That plugin is not on <Agent>'s load path, so its sub-skills are not directly invokable — this dispatcher loads and runs them.

## Invocation

```
/t-tool <skill-name> [args...]
```

No argument → run `ls <CLONE_PATH>/skills/` to list available sub-skills, then stop.

## Procedure

1. Read `<CLONE_PATH>/skills/<skill-name>/SKILL.md`. Missing → list the directory and stop.
2. Execute it as the active skill. Substitute `${CLAUDE_PLUGIN_ROOT}` with `<CLONE_PATH>`; sibling resources (`agents/`, `protocols/`, `guides/`, `templates/`, `scripts/`) resolve under the same root.
3. Complete its full flow; do not re-dispatch.
````

The `description` is the trigger condition — keep the `/t-tool` literal in it.

### 3. Configure Context7 MCP

See [Install Context7](#install-context7) below. Context7 is a `requiredMcpServers` entry; without it, stages like `t-design` and `t-run` will fail.

## Invocation

`/t-tools:t-<skill>` in Claude Code maps to `/t-tool <skill>` in Codex / ZCode. The only difference is the namespace separator `:` becomes a space; arguments pass through unchanged:

| Claude Code | Codex / ZCode |
| --- | --- |
| `/t-tools:t-prd user-management` | `/t-tool t-prd user-management` |
| `/t-tools:t-prd-check user-management` | `/t-tool t-prd-check user-management` |
| `/t-tools:t-run user-management --phase backend` | `/t-tool t-run user-management --phase backend` |
| `/t-tools:t-super-run user-management --phase backend` | `/t-tool t-super-run user-management --phase backend` |

Running `/t-tool` with no argument lists every sub-skill under the repo's `skills/`.

## Working Directory Convention

The dispatcher skill does not change the plugin's runtime conventions for target projects. Start Codex / ZCode in the **target project root**, and ensure these directories exist:

- `docs/` — official product documents
- `.ai/` — workflow artifacts (PRD drafts, design, tasks, previews, etc.)

These paths are defined by protocols inside the skills and are independent of the AI tool.

## How Sub-Agents Load in ZCode/Codex

ZCode / Codex and other non-Claude tools usually do not auto-register `agents/*.md` the way `claude --plugin-dir` does. This plugin does not require users to configure extra agent registration; skills that invoke sub-agents explicitly inject the role spec according to `${CLAUDE_PLUGIN_ROOT}/protocols/subagent-dispatch.md`.

As long as the dispatcher-injected `${CLAUDE_PLUGIN_ROOT}` points at this repo clone and the repo still contains `agents/`, tools that support `~/.agents/skills/` plus sub-agent/task delegation can run with the same rule.

## Install Context7

Context7 serves up-to-date, version-specific documentation for third-party libraries; it is queried during stages like `t-design` and `t-run`. It is a Streamable-HTTP MCP server. The universal configuration elements are:

- Server URL: `https://mcp.context7.com/mcp`
- Authentication: pass the API key you obtain at [context7.com](https://context7.com) via the HTTP header `CONTEXT7_API_KEY`

**OpenAI Codex** (CLI / App / VS Code extension share one config):

Edit `~/.codex/config.toml`:

```toml
[mcp_servers.context7]
url = "https://mcp.context7.com/mcp"
http_headers = { "CONTEXT7_API_KEY" = "ctx7sk-..." }
```

Or, in the Codex App: Settings → MCP Servers → + Add servers.

**Other clients** (Cursor / Cline / Claude Code / Gemini CLI / ZCode, etc.):

Each client's MCP config location and syntax differ and change between versions. Treat the Context7 official docs as authoritative rather than the examples in this document:

- Context7 official repo: <https://github.com/upstash/context7>
- Per-client config index: <https://context7.com/docs> (the Clients section on the left lists each client's latest syntax)
- Codex page: <https://context7.com/docs/clients/codex>

After configuring, restart the client and trigger one library-docs lookup in a session to verify connectivity.

## Verification

After the three steps above, run from any target project directory:

```
/t-tool
```

It should list every `t-*` skill under `skills/`. Then try a lightweight command:

```
/t-tool t-decision demo-feature
```

If it reads `<CLONE_PATH>/skills/t-decision/SKILL.md` and runs its flow, the dispatcher, `${CLAUDE_PLUGIN_ROOT}` substitution, and Context7 are all wired up.

## Verified Tools

- **ZCode** — loads skills from `~/.agents/skills/` and supports MCP config out of the box.
- **OpenAI Codex** (CLI / App) — loads skills from `~/.agents/skills/` and supports MCP via `~/.codex/config.toml`.

Other tools that load skills from `~/.agents/skills/` (Cursor, Cline, etc.) work the same way in principle, but are not individually verified by this project.

## Maintenance and Updates

- **Update the plugin**: `cd <CLONE_PATH> && git pull`
- **The dispatcher skill rarely needs changes**, unless the repo's `skills/` directory layout has a breaking change
- **Context7 connection failures**: first check that the API key in `http_headers` is valid, then verify the latest config syntax for that client in the official docs
