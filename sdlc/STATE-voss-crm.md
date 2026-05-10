# State — last updated 2026-05-09

**Active focus:** `e01-s01-mcp-write-surface` planned (5 tasks); awaiting operator review before Execute.
**Last completed:** Planned `e01-s01-mcp-write-surface` — five task artefacts written with ACs and test specs (t01 → t05).
**Next:** Operator reviews/edits the plan, then Execute starts at `e01-s01-t01-api-company-name-resolution` (blocking dependency for t02).

## Open questions

- `project:` field on artefacts uses `voss-crm`, not in SDLC's listed values (`constellation | signalstrata | agent-os`). Add as a new project, or slot under an existing one?
- Unified-search diff (read-side, sibling of this epic) still uncommitted on `security-hardening-modal-deploy`; `raw/unified-search-fix.md` is its capture. Commit before filing to `/work/done/` under `e01`, or compile-then-commit?
- ADR for SDLC adoption itself — file now or wait for first real architectural decision?
