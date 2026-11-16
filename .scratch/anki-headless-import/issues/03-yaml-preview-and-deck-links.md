# 03: Preview YAML changes against linked existing Decks

**What to build:** An author can preview repository YAML on a consistent disposable copy of a selected Collection and see per-Note Field/tag changes and approved Deck resolution for new managed Cards, without generating or reading CSV. Verify the complete preview path against sandbox Collections only. Copies exist solely for non-mutating preview, not backup or restoration. YAML's `deck` declaration supplies the requested Deck name, not a Collection name or a separate Deck definition. Existing Cards' placement is neither changed nor reported as a mismatch.

**Blocked by:** 02 — Prove headless Collection updates safely.

**Status:** resolved

**Verification environment:** Use the dedicated `.venv`, tool-created sandbox Collections with matching manifests, and temporary isolated fixtures documented in [`tools/headless_import/exploration.md`](../../../tools/headless_import/exploration.md). Setup may create fixture Decks/media separately; preview must not. No personal Collection or profile-registry access.

- [x] Parse and validate entry YAML, including Note Type, target Deck, required values, unknown Fields, quoted nonempty stable IDs, and duplicate IDs across all entry files of a Note Type.
- [x] Match existing Notes by Note Type plus exact first-Field custom ID; fail on ambiguous Collection matches rather than choosing or creating duplicates.
- [x] Preserve existing HTML Field normalization, including trimming and newline handling, independently of CSV generation.
- [x] Define native tags as entry metadata, not an ordinary Note Type Field, and update schema/config documentation consistently while preserving the legacy CSV column layout and workflow during migration.
- [x] Preview full tag replacement on managed Notes; absent, null, or empty tags mean an empty tag set. Preserve support for the REPO_DELETE workflow marker.
- [x] Define an explicit Deck-link configuration and validate it for the selected Collection. Propose matches by exact hierarchical name, require approved correspondence, and reject missing, ambiguous, or filtered Deck targets without creating Decks.
- [x] Use every entry source's nonempty top-level `deck` declaration as the requested existing Deck; do not require a second repository Deck definition. Select the source Collection separately; exercise target-selection/Profile semantics using sandbox fixtures, not personal Profiles.
- [x] Reconcile target-Deck documentation so entry YAML is authoritative; validate declared schemas against the actual Collection and report unsupported mismatches.
- [x] Reject missing referenced media in the target Collection; media uploads, replacements, and deletion are outside scope.
- [x] Create a temporary consistent preview database copy through SQLite's backup API so committed WAL changes are included. This API is a copy-consistency primitive, not a product backup mechanism: do not retain recovery snapshots, archive media, or provide restore. Do not force a checkpoint on the sandbox source or open it through Anki for inspection; all preview backend opening occurs only on the copy. Keep referenced sandbox media available without source-media writes, release connections, and clean up disposable resources on every exit path.
- [x] Produce deterministic summaries sorted by Note Type and stable ID: add/update/unchanged, changed Fields with before/after values, tags added/removed, and requested/resolved Deck for new managed Cards. Keep temporary paths/timestamps outside the deterministic summary; do not report existing Card/YAML Deck differences or propose moves.
- [x] Preview does not mutate the selected sandbox source Collection or generate CSV. Public-command sandbox tests cover all rejection cases, WAL-inclusive disposable copies, source database/media immutability, deterministic summaries, and disposal without retained backup artifacts.

## Comments

- 2026-11-16: Exploration already provides direct YAML parsing/normalization, exact identity matching, native tag replacement, and supported missing-media rejection in `tools/headless_import/`. All 14 current entry sources have nonempty `deck` declarations. That importer mutates the original sandbox and creates missing Decks, so it is not this preview implementation. Reuse the demonstrated behavior without carrying over Deck creation or existing-Card movement; acceptance remains unchecked pending the public preview path and complete tests.
- 2026-11-16: User pivot: all implementation verification and tests use the exploration sandbox environment. Remove product backup/recovery requirements; temporary consistent copies remain only for non-mutating preview. Historical importer snapshots are not required behavior. Existing Deck-link approvals and no-existing-Card-movement rules remain unchanged; no acceptance checks were completed by this revision.
- 2026-11-16: Implemented sandbox-only `tools/headless_import/preview.py` and public-command integration tests. Approved Collection-bound Deck links, disposable WAL-consistent copies, native tag replacement preview, media checks, and existing-Card placement preservation are documented in `tools/headless_import/README.md`. No personal Collection was accessed.
