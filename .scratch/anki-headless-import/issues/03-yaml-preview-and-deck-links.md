# 03: Preview YAML changes against linked existing Decks

**What to build:** An author can preview repository YAML on a consistent disposable copy of a selected Collection and see per-Note Field/tag changes and approved Deck resolution for new managed Cards, without generating or reading CSV. YAML's `deck` declaration supplies the requested Deck name, not a Collection name or a separate Deck definition. Existing Cards' placement is neither changed nor reported as a mismatch.

**Blocked by:** 02 — Prove headless Collection updates safely.

**Status:** ready-for-agent

- [ ] Parse and validate entry YAML, including Note Type, target Deck, required values, unknown Fields, quoted nonempty stable IDs, and duplicate IDs across all entry files of a Note Type.
- [ ] Match existing Notes by Note Type plus exact first-Field custom ID; fail on ambiguous Collection matches rather than choosing or creating duplicates.
- [ ] Preserve existing HTML Field normalization, including trimming and newline handling, independently of CSV generation.
- [ ] Define native tags as entry metadata, not an ordinary Note Type Field, and update schema/config documentation consistently while preserving the legacy CSV column layout and workflow during migration.
- [ ] Preview full tag replacement on managed Notes; absent, null, or empty tags mean an empty tag set. Preserve support for the REPO_DELETE workflow marker.
- [ ] Define an explicit Deck-link configuration and validate it for the selected Collection. Propose matches by exact hierarchical name, require approved correspondence, and reject missing, ambiguous, or filtered Deck targets without creating Decks.
- [ ] Use every entry source's nonempty top-level `deck` declaration as the requested existing Deck; do not require a second repository Deck definition. Select the source Collection separately, using its Desktop Profile when applicable.
- [ ] Reconcile target-Deck documentation so entry YAML is authoritative; validate declared schemas against the actual Collection and report unsupported mismatches.
- [ ] Reject missing referenced media in the target Collection; media uploads, replacements, and deletion are outside scope.
- [ ] Create the disposable database snapshot through SQLite's backup API so committed WAL changes are included. Do not force a checkpoint on the source or open it through Anki for inspection; all preview backend opening occurs only on the copy. Keep referenced media available without source-media writes and release connections on every exit path.
- [ ] Produce deterministic summaries sorted by Note Type and stable ID: add/update/unchanged, changed Fields with before/after values, tags added/removed, and requested/resolved Deck for new managed Cards. Keep temporary paths/timestamps outside the deterministic summary; do not report existing Card/YAML Deck differences or propose moves.
- [ ] Preview does not mutate the source Collection, including a sandbox source, or generate CSV. Tests cover all rejection cases, WAL-inclusive copies, source database/media immutability, and deterministic summaries.

## Comments

- 2026-11-16: Exploration already provides direct YAML parsing/normalization, exact identity matching, native tag replacement, and supported missing-media rejection in `tools/headless_import/`. All 14 current entry sources have nonempty `deck` declarations. That importer mutates the original sandbox and creates missing Decks, so it is not this preview implementation. Reuse the demonstrated behavior without carrying over Deck creation or existing-Card movement; acceptance remains unchecked pending the public preview path and complete tests.
