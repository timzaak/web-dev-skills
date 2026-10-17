# Continuously merging main into general

Use this guide to integrate origin/main while preserving generic workflows and opt-in domain templates. It does not authorize commits, pushes, or overwriting user changes. Read repository AGENTS.md first.

## Versions to maintain

The active general tree owns generic orchestration, state, recovery and acceptance, plus Web Demo/Figma. classic-stack holds migrated main-branch domain assets; java-backend holds Java backend adaptations from java. Each template.json records source_paths and a full upstream_revision. Domain files live in files/; matching shared runtime files come from that pinned Git commit. A successful main merge does not automatically upgrade either template.

## Prepare

```powershell
git status --short
git branch --show-current
git fetch origin main
git log --oneline --left-right general...origin/main
git diff --name-status general...origin/main
```

Work on general after committing or explicitly backing up current work. Do not reset, clean, or automatically stash user changes. Record pre-merge HEAD and both template revisions. Inspect changed skills and their contracts, guides, agents, scripts and downstream consumers, including new domains and runtime layouts.

## Classify changes

| Incoming change | Destination |
| --- | --- |
| Generic orchestration, state, recovery, outputs, scoring and dispatch | Active shared contracts and every affected consumer |
| Web Demo, Figma, logger package | Retained capability, without production-stack defaults |
| Domain-specific agents, guides, scripts and templates | classic-stack/files; keep original active paths removed |
| Java backend assets | java-backend independently, preserving Rust template contents |
| Files mixing workflow and domain rules | Merge generic portions into active code and preserve domain portions in templates |
| New frameworks/platforms | Classify and extend the appropriate source_paths; do not automatically register them |
| Public docs and metadata | Keep generic entrypoints accurate; advertise domains through the catalog |
| Tests | Keep meaningful generic tests active; run domain tests in exported runtimes |

## Merge and resolve

```powershell
git merge origin/main
git status --short
git diff --name-only --diff-filter=U
git show origin/main:agents/backend-dev.md
git show HEAD:templates/project-profiles/classic-stack/files/agents/backend-dev.md
```

A modify/delete conflict commonly means upstream changed a migrated domain asset. Compare upstream, the previous template and local adaptations; merge needed changes into the template path before git rm -- <reviewed-original-path>. Also classify newly added files that merged cleanly. For templates not yet committed, use working-tree contents instead of assuming HEAD contains them.

Do not resolve whole contract groups with blanket ours/theirs. Generic phases, output scopes and project-owned CI/environment behavior must not be replaced by domain defaults. To abandon an unfinished merge, use git merge --abort only after checking for user work added since merge began; do not force-reset.

## Update template baselines

Compare the recorded old revision with the proposed complete commit using git diff <old> <new> -- <source_paths>, and inspect new domain files outside the manifest. Merge template-specific changes rather than overwriting them. Extract reviewed files as bytes to preserve encoding and binary content:

```powershell
python -c "from pathlib import Path; import subprocess; p='agents/backend-dev.md'; dst=Path('templates/project-profiles/classic-stack/files')/p; dst.parent.mkdir(parents=True,exist_ok=True); dst.write_bytes(subprocess.check_output(['git','show','origin/main:'+p]))"
```

Do not execute that overwrite when unreviewed template edits exist. Add new paths and reconcile upstream deletions in files/, source_paths and navigation. Set upstream_revision to the reviewed full git rev-parse origin/main result, then verify shared contracts, designs, entrypoints and script dependencies against that baseline. Changing the revision alone does not establish compatibility.

For Java, fetch origin java and compare origin/java independently. The Java template may remain pinned while main advances. Merging main does not require merging origin/java. Rebasing Java behavior onto a newer main runtime requires a complete, separately verified port of Java scripts/contracts, not mixing state versions.

## Validate and finish

```powershell
python -X utf8 -m unittest discover -s scripts/tests -v
python -X utf8 scripts/check-markdown-links.py
git diff --check
```

Check that domain defaults did not return to active directories. Walk changed skill behavior through success, missing inputs, downstream gates, failure recovery and repeated invocation. Prechecks remain optional and cannot replace acceptance. Run package npm checks when logger package code changes.

Export each affected template into a new external temporary directory:

```powershell
python scripts/export-template.py export classic-stack --output C:/temp/t-tools-classic-merge-check
python -X utf8 scripts/check-markdown-links.py --root C:/temp/t-tools-classic-merge-check
python -X utf8 -m unittest discover -s C:/temp/t-tools-classic-merge-check/scripts/tests -v
```

Use java-backend and a separate directory for Java. Never delete user contents to reuse a changed export directory. Fetch missing pinned history; if rewritten upstream history makes the commit unavailable, stop and restore the source or explicitly upgrade the baseline. Never silently use the latest branch head.

Inspect link report counts, not just the checker's exit code. Record pre-existing baseline problems with their origin and impact; do not hide newly introduced failures behind them. Unchanged templates need not rerun unrelated domain tests for a generic-only change.

Finish with no unresolved conflicts, consistent Chinese/English docs, catalogs, manifests and recorded revisions, and only intentional changes. Report generic changes, template changes, baseline migrations and evidence. Commit/push only within user authorization; a merge does not authorize publishing templates or implementing the future knowledge workflow.
