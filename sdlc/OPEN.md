# Open — deferred judgment queue

- 2026-06-23 No `.ri/config.md` in the repo, so tier and project are unset; this compile defaulted to tier-2 by judgment. Add a config to make the tier explicit. [e02-search-enrichment]
- 2026-06-23 RESOLVED — t03 (in-app search filters) dropped after senior-staff review: in-app filtering is better served by surfacing the existing contacts-list filters, which is separate work, not a search task. [e02-s01-search-filters]
- 2026-06-23 Segment vocabulary has drifted: live data carries free-form segments (Quant, AI Consultant, Ecosystem, Crypto/DeFi, Sell-side, Meridian…) far beyond the frontend enum (signal_strata/consulting/pe/other). Worth settling a canonical segment list before building any segment-filter UI. [e02-search-enrichment]
- 2026-06-23 Search filter params accept comma-separated values only (e.g. role=a,b), not the repeatable form (role=a&role=b). Fine for the MCP/API convention in use; revisit only if an HTTP client needs the repeatable form. [e02-s01-search-filters]
- 2026-06-23 Web contacts list re-sorts search results client-side (A–Z / recent), so engine ranking (s02) won't show there. Decide whether to add a "Best match" sort option to ContactsPage. [e02-s02-search-ranking]
