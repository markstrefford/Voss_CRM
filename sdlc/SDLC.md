---
title: SDLC for Reimagined Industries
purpose: How Claude Code should approach all development work in this repo
version: 3.1
---

# SDLC

This repository follows an AI-native, spec-anchored, compile-on-demand SDLC. The filesystem is the source of truth. Git history is the audit trail. Claude Code is the primary development agent. There is no external tracker (Jira, Notion, etc.) and none should be introduced without an ADR.

## Principle

Capture is unstructured. Compilation gives material its shape. Execution acts on what's been compiled. The hierarchy — epic, story, task, decision, runbook — is emergent, not imposed. Nothing is pre-classified at capture; nothing is forced into a destination it doesn't fit.

## Directory layout

    /raw/                     unstructured capture, no rules
    /work/
      active/                 things being worked on, any shape
      done/                   archived
    /docs/
      architecture/           long-standing architectural docs
      strategy/               strategy docs
      decisions/              ADRs, point-in-time decisions
      runbooks/               operational guides
    SDLC.md                   this file
    CLAUDE.md                 repo-specific context, references this file
    STATE-<repo>.md           current state, regenerated at session end
    .claude/agents/           sub-agent definitions (verifier, etc.)

`/raw/` holds anything captured. `/work/` holds compiled artefacts being acted on. `/docs/` holds compiled artefacts that explain the system. Items move between these by being compiled, not by being filed.

**`/work/done/` shape.** The default is one file per artefact, matching how it was structured in `/work/active/`. For bulk historical imports (pre-SDLC done items, legacy changelog entries), a single consolidated file is acceptable — name it `done-historical.md` or similar. Going forward under the SDLC, new done items get their own files.

**Pre-existing content.** Files that pre-date the SDLC (legacy backlogs, changelogs, scratch docs) are treated as raw material to be compiled. They live where they currently live until compilation moves them. Compilation of legacy content follows the same rules as compilation of `/raw/` items: each item becomes a compiled artefact in the right destination, or is discarded, or is parked. Nothing is moved without being compiled.

## File conventions

Files in `/raw/` have no required structure. Free-form notes. They have no frontmatter, no id, no status.

Compiled artefacts (anything in `/work/` or `/docs/`) have YAML frontmatter:

    ---
    id: stable-id
    kind: task | story | epic | decision | runbook | strategy | architecture
    project: <repo-slug>                  # the repo this artefact belongs to
    status: active | blocked | done       # for /work/ items only
    parent: optional-parent-id            # when relationships exist
    children: [optional-child-ids]        # when relationships exist
    sources: [paths-to-raw-sources]       # what this was compiled from
    created: 2026-04-29
    updated: 2026-04-29
    verified-on: 2026-04-29               # for /docs/ items
    tags: [optional]
    ---

Filename matches `id`. IDs are stable; never rename once assigned. The `kind` field describes what the artefact *is*, not what folder it sits in. The folder follows the kind.

### ID format — hierarchical lineage

Compiled work artefacts (`epic`, `story`, `task`) carry their lineage in the id, separator `-`:

- Epic: `e<NN>-<slug>` — e.g. `e02-rns-automation`
- Story: `e<NN>-s<NN>-<slug>` — e.g. `e02-s06-unified-signals-risks-extraction`
- Task: `e<NN>-s<NN>-t<NN>-<slug>` — e.g. `e02-s06-t10-extract-risks-into-poll`

Numbering is global per kind (s06 doesn't restart at 1 inside e02 — it continues the project-wide story sequence). Filename = id verbatim.

**Rationale**: directory listings group naturally by epic; reading a filename surfaces parentage without opening it; `parent:` and `children:` in frontmatter remain authoritative for relationships but the id makes the common case visible.

**Tension with the stable-id rule**: if a story moves to a different epic, the id can't be renamed. File the move as a new id with `sources:` linking to the original; the original gets `status: done` with a note explaining the move. In practice cross-epic moves are rare (compile decisions are usually right) — the convention optimises the common case.

`/docs/` artefacts (`decision`, `runbook`, `strategy`, `architecture`) are not part of the work tree and use their own id formats (e.g. `0001-localhost-fastapi-triage-ui` for ADRs — sequential numeric prefix + slug).

## The verbs

Work is a small set of verbs applied as needed. They are not a sequence. You apply whichever fits.

### Capture
Drop material into `/raw/`. Anywhere, anytime, any shape. No structure, no decisions. The only rule: don't lose the thought.

### Compile
Read `/raw/` (and any other unstructured sources). For each item, decide what it should become and produce the compiled artefact. Possible outputs:

- a task in `/work/active/` (one commit's worth of work)
- a story in `/work/active/` (one coherent change worth specifying)
- an epic in `/work/active/` (one strategic commitment)
- a decision in `/docs/decisions/`
- an entry in `/docs/strategy/` or `/docs/architecture/`
- an addition to an existing artefact (link the source to it)
- discard

Compilation is a Claude operation. The operator approves the proposed compilation; Claude executes the file moves. The raw source is referenced in the `sources:` field of the compiled artefact and then deleted from `/raw/` — once compiled, it's been absorbed.

Compilation replaces what older workflows called triage, strategic planning, and story planning. They were always the same operation at different scales.

### Plan
For an artefact in `/work/active/` whose `kind` is `story` or `epic`, produce a task sequence. Each task entry must include:

- one-line outcome
- acceptance criteria
- test specification (defined before implementation)

Tasks are written as their own files in `/work/active/` with `parent:` linking to the story. The plan is committed alongside the story. The operator reviews and edits the plan before execution.

### Execute
Act on a task. Tests first, then implementation. Claude writes the tests defined in the task spec, confirms they fail, then implements until they pass. No skipping tests. No "I'll add tests later." If the task spec didn't define tests, stop and update the plan.

When the task is complete: update `status: done`, commit with a message referencing the task id (e.g. `task-12: extract simulation engine module`), move the file to `/work/done/`.

### Verify
Invoke the `verifier` sub-agent (defined in `.claude/agents/verifier.md`). It reads the spec, the plan, and the diff with no memory of how the implementation was built. It reports alignment, test coverage, architectural drift, and code smells.

The operator reviews the verifier output. Pass → continue. Fail → fix or kick the task back to active.

The verifier is non-negotiable. It is the single highest-leverage step in the loop and the most consistently skipped.

### File
At the end of any session that touches architecture, strategy, or operational behaviour, file the outputs back. Useful sessions don't dissipate, they compound.

- architectural decisions → `/docs/decisions/NNNN-title.md` (ADR format)
- operational changes → update relevant runbook in `/docs/runbooks/`
- strategy shifts → update or create in `/docs/strategy/`
- repo-wide conventions → update `CLAUDE.md`
- spec divergences → update the story spec to match what was actually built

If a session produced a thinking artefact worth keeping (architectural reasoning, a useful framing), file it as a doc with `sources:` pointing to where it came from. The system gets denser over time.

If nothing is worth filing, skip. Don't write filler.

### Refresh state
The final action of every working session: regenerate the STATE file. See the STATE file section below.

## STATE file — bridge to thinking sessions

The STATE file exists because Claude in the chat app cannot read the repo directly. The operator pastes it at the start of any conversation in the chat app that involves this repo. This is the only sanctioned bridge between repo state and architectural conversations elsewhere; do not introduce others without an ADR.

**Filename convention:** `STATE-<repo>.md`. Each repo's STATE file lives at `/sdlc/STATE-<repo>.md`.

The STATE file is regenerated at the end of every Claude Code session and must contain exactly:

    # State — last updated [ISO date]
    
    **Active focus:** [one line — what's currently being worked on]
    **Last completed:** [id — one line]
    **Next:** [id — one line]
    
    ## Open questions
    - bullet
    - bullet

Rules:

- Keep the STATE file under 30 lines. If it grows beyond a screen it stops getting pasted.
- "Active focus" is whatever shape best describes the current work — could be a story, a task, an epic, a doc compilation, anything. Don't force it into a typed slot.
- The "Open questions" field is the highest-value content. If Claude Code hits something during execution that needs architectural judgment, it goes here. Empty is fine; padding is not.
- When the STATE file has no open questions, the operator does not need a thinking session — they need to be in Claude Code executing.

When GitHub MCP becomes reliable in the chat app, the STATE file and this section can be removed. The workflow does not change.

## Status discipline

- An artefact in `/work/active/` is `active` if it's being worked on, `blocked` with a `blocker:` field if it isn't, `done` only when complete.
- A task is `done` only when tests pass, the diff is committed, and the verifier has signed off.
- A story is `done` when all its child tasks are done and the spec's acceptance criteria are met.
- Done artefacts move from `/work/active/` to `/work/done/`.
- Doc artefacts in `/docs/` carry `verified-on:` rather than status. They're either current (verified recently) or stale (not).

## Hard rules for Claude Code

1. **Read `SDLC.md` and `CLAUDE.md` at the start of every session.** No exceptions.
2. **Never start coding without a task artefact.** If the operator asks for code directly, propose compiling it into a task first.
3. **Never write implementation before tests.** If there's no test spec, update the plan first.
4. **Never mark a task done without verifier sign-off.**
5. **Never edit an artefact's `id` field.** IDs are stable.
6. **Never introduce an external tracker.** If the operator suggests it, require an ADR documenting the decision.
7. **Never skip filing for architectural changes.** The next session depends on it.
8. **Never end a working session without regenerating the STATE file** (`/sdlc/STATE-<repo>.md`).
9. **Never let `/raw/` accumulate beyond 20 items without prompting the operator to compile.**
10. **Never delete from `/raw/` without first producing a compiled artefact that references it as a source.** Compilation absorbs raw material; it doesn't discard it silently.
11. **Trust the document.** If a question can be answered by reading `SDLC.md`, `CLAUDE.md`, or any artefact already in the repo, read it and proceed. Do not ask the operator. Asking questions the repo answers is a failure mode, not a courtesy.
12. **Trust the operator's instruction.** When the operator gives a clear directive ("do X to all Y"), execute it. Do not ask for re-confirmation of the directive itself. Ask only if a specific item genuinely needs disambiguation, and ask once — not per item.
13. **No re-asking.** If the operator has answered a question once in this session, do not ask it again in any phrasing. Re-asking signals the prior answer wasn't trusted or wasn't retained. If genuinely unsure, state the prior answer back and confirm — do not start over.

## What stays human

The operator (Mark) decides:

- compilation outcomes — Claude proposes, operator approves
- plan approval — Claude proposes, operator edits, operator approves
- verifier sign-off — Claude reports, operator decides
- `CLAUDE.md` edits — these encode opinions and must sound like the operator
- ADRs — Claude can draft, operator must approve

## What runs without further approval

Within an approved task spec, Claude executes freely:

- writing tests as specified
- writing implementation against tests
- iterating on test failures
- updating documentation when behaviour changes
- generating runbook updates
- regenerating the STATE file
- proposing the next compilation, plan, or task

## Scaling note

This SDLC works for a single operator with AI agents. When a second human joins the loop, the substrate may need to change (filesystem → tracker), but the workflow stays identical: capture raw, compile into shape, plan when shape requires it, execute with tests-first, verify with fresh context, file outputs back, refresh state on exit. Migrating substrate is a one-time mechanical change; migrating workflow would be a rebuild.

## References

External thinking that informed this SDLC:

- Spec-Driven Development (arXiv 2602.00180) — spec-anchored is the practical middle between vibe coding and full waterfall.
- Anthropic internal practice — fresh-context PR review by a separate Claude instance.
- Augment Code's Coordinator / Implementor / Verifier pattern.
- Andrej Karpathy's LLM-managed wiki pattern — raw sources compiled by an LLM into structured artefacts; structure emerges from content rather than being imposed upfront. This SDLC adapts that pattern from knowledge management to development work.
- Loose-coupling, shared-edges principle from Reimagined Industries' Agent OS architecture, applied to the workflow itself.
