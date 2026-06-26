# State — last updated 2026-06-23

**Active focus:** None — `active/` is empty. Epic `e02-search-enrichment` is **complete**: s01 (multi-value filters) and s02 (relevance ranking) both shipped, verifier-passed, and merged. 150 tests green.
**Last completed:** `e02-s02` relevance ranking — results now best-first (own fields beat FK-resolved names); surfaces on the agent's search and Telegram. Whole epic done. Earlier this session: search filters (s01), sheet-ID read fix, create-contact dedup guard; contact book deduped 392 → 357.
**Next:** No active work. Open candidates: a "Best match" web sort (OPEN), the segment-vocabulary cleanup (OPEN), or a new line of work.

## Open questions

- 4 open (see `/sdlc/OPEN.md`) — no `.ri/config.md`; segment vocabulary drift; comma-separated-only filter params; web list re-sorts client-side so won't show s02 ranking.
