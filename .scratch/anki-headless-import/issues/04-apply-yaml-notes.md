# 04: Add and update Notes directly from YAML

**What to build:** An author applies a validated YAML selection to an explicitly selected sandbox Collection using compatible existing Note Types and linked existing Decks. Missing Notes are added, matched Notes are updated in place, and repository Fields and tags win without resetting existing review history. Application has no backup/restore prerequisite or mechanism.

**Blocked by:** 03 — Preview YAML changes against linked existing Decks.

**Status:** ready-for-agent

**Verification environment:** Use the dedicated `.venv`, tool-created sandbox Collections with matching manifests, and temporary fixtures documented in [`tools/headless_import/exploration.md`](../../../tools/headless_import/exploration.md). Never prepare tests from a personal Collection; fixture setup creates any needed existing Decks/media separately from application.

- [ ] Apply the same validated and normalized data used by preview, without reading or generating CSV.
- [ ] Apply only to the explicitly selected sandbox Collection in this slice, after preview/approval. Temporary preview/rehearsal copies use ticket 03's WAL-consistent copy path, but apply creates no pre-import backup, retained snapshot, media archive, or restore artifact. Do not carry over the exploration importer's snapshot behavior.
- [ ] Update existing Notes through native APIs, retaining internal Note IDs/GUIDs and existing Card IDs; let Anki generate internal identities for new Notes.
- [ ] Add new Notes to the approved existing normal Deck resolved from YAML `deck`; update existing Notes without moving their existing Cards. Ignore existing Card/YAML Deck differences without warnings or proposed moves.
- [ ] Replace the complete tag set only on matched repository-managed Notes, including clearing personal tags when YAML tags are empty. Report additions and removals.
- [ ] Propagate REPO_DELETE as a tag only; never delete Notes absent from YAML, remove empty Cards, or automatically delete anything marked for cleanup.
- [ ] Reject unsupported Note Type schemas and missing referenced media before writes; leave unrelated Notes, Deck settings, Templates, and media untouched.
- [ ] Capture pre-update Card IDs; verify persisted Field/tag changes, unchanged existing Card Deck IDs, review-history rows, and ordinary review scheduling. Report newly generated conditional Cards for the new-Card-only placement behavior verified in ticket 06.
- [ ] Public-command tests in the documented sandbox verify a second identical application is a no-op and reopen the target to prove persistence. Failures release the Collection and report committed progress plus fresh-preview/retry requirements without claiming whole-run rollback or attempting restoration.

## Comments

- 2026-11-16: Existing placement preservation is now the full epic contract, not merely a temporary restriction in this slice. YAML `deck` governs new managed Cards only. Preview and application share normalized inputs and per-Note Field/tag change reporting; existing Deck differences are intentionally ignored.
- 2026-11-16: User pivot: use the documented sandbox for all work/tests; application does not create or require backups. Preview copies are disposable validation inputs only. Existing exploratory Deck creation, Card movement, and snapshot retention are not canonical behavior. Acceptance remains unchecked.
