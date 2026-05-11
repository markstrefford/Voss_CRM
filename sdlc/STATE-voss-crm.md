# State — last updated 2026-05-11

**Active focus:** Story `e01-s01-mcp-write-surface` shipped (5 tasks, 5 commits, +24 tests, verifier PASS). Branch `security-hardening-modal-deploy` ready for deploy.
**Last completed:** `e01-s01-t05-mcp-update-snooze-follow-up` — closed the last write-side gap. Story moved to `/work/done/`.
**Next:** Deploy + confirm. Then decide on `e01` epic close-out (retroactive filing of read-side / unified-search work).

## Open questions

- **Deploy gate:** Modal container needs redeploy with the new search + write-surface code; Claude Desktop MCP server needs restart so `tool_search` and the five new `tool_update_*`/`tool_snooze_*` tools register. The "API error 404" Claude app saw on search was pre-redeploy; confirm post-redeploy.
- **Retroactive `e01-s01` for the read side:** unified-search work (commits `0f3e95c`, `007c193`) lives in git but has no `/work/done/` artefact under `e01`. Compile `sdlc/raw/unified-search-fix.md` into a `done` artefact to close out the epic, or leave the raw note as the audit record?
- **Project field on artefacts:** still using `voss-crm` (not in SDLC's listed `constellation | signalstrata | agent-os`). Add as a known project value or slot under existing?
- **Tool docstring polish (verifier nice-to-have):** `tool_create_contact`'s docstring doesn't mention `company_name` resolution, only `tool_update_contact`'s does. Small parity fix, file as a follow-up task if worth doing.
