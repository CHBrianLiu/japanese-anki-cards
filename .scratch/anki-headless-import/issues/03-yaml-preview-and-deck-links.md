# 03: Preview YAML changes against linked existing Decks

**What to build:** An author can preview repository YAML against a disposable Collection and see exactly which Notes, tags, and Deck links would change, without generating or reading CSV. Approved links connect repository-defined Decks to existing normal Decks; entry YAML determines the target Deck.

**Blocked by:** 02 — Prove headless Collection updates safely.

**Status:** ready-for-agent

- [ ] Parse and validate entry YAML, including Note Type, target Deck, required values, unknown Fields, quoted nonempty stable IDs, and duplicate IDs across all entry files of a Note Type.
- [ ] Match existing Notes by Note Type plus exact first-Field custom ID; fail on ambiguous Collection matches rather than choosing or creating duplicates.
- [ ] Preserve existing HTML Field normalization, including trimming and newline handling, independently of CSV generation.
- [ ] Define native tags as entry metadata, not an ordinary Note Type Field, and update schema/config documentation consistently while preserving the legacy CSV column layout and workflow during migration.
- [ ] Preview full tag replacement on managed Notes; absent, null, or empty tags mean an empty tag set. Preserve support for the REPO_DELETE workflow marker.
- [ ] Define an explicit Deck-link configuration and validate it for the selected Collection. Propose matches by exact hierarchical name, require approved correspondence, and reject missing, ambiguous, or filtered Deck targets without creating Decks.
- [ ] Reconcile target-Deck documentation so entry YAML is authoritative; validate declared schemas against the actual Collection and report unsupported mismatches.
- [ ] Reject missing referenced media in the target Collection; media uploads, replacements, and deletion are outside scope.
- [ ] Preview does not mutate the live Collection or generate CSV; any backend opening occurs only on a consistent disposable copy. Tests cover all rejection cases and deterministic summaries.
