# 04: Add and update Notes directly from YAML

**What to build:** An author applies a validated YAML selection to a disposable Collection using compatible existing Note Types and linked existing Decks. Missing Notes are added, matched Notes are updated in place, and repository Fields and tags win without resetting existing review history.

**Blocked by:** 03 — Preview YAML changes against linked existing Decks.

**Status:** ready-for-agent

- [ ] Apply the same validated and normalized data used by preview, without reading or generating CSV.
- [ ] Apply only to the explicitly selected disposable Collection in this slice; source preparation uses the WAL-inclusive SQLite backup mechanism from ticket 03 and does not open the source through Anki.
- [ ] Update existing Notes through native APIs, retaining internal Note IDs/GUIDs and existing Card IDs; let Anki generate internal identities for new Notes.
- [ ] Add new Notes to the approved existing normal Deck resolved from YAML `deck`; update existing Notes without moving their existing Cards. Ignore existing Card/YAML Deck differences without warnings or proposed moves.
- [ ] Replace the complete tag set only on matched repository-managed Notes, including clearing personal tags when YAML tags are empty. Report additions and removals.
- [ ] Propagate REPO_DELETE as a tag only; never delete Notes absent from YAML, remove empty Cards, or automatically delete anything marked for cleanup.
- [ ] Reject unsupported Note Type schemas and missing referenced media before writes; leave unrelated Notes, Deck settings, Templates, and media untouched.
- [ ] Capture pre-update Card IDs; verify persisted Field/tag changes, unchanged existing Card Deck IDs, review-history rows, and ordinary review scheduling. Report newly generated conditional Cards for the new-Card-only placement behavior verified in ticket 06.
- [ ] A second identical application is a no-op. Failures release the Collection and report committed progress without claiming whole-run rollback.

## Comments

- 2026-11-16: Existing placement preservation is now the full epic contract, not merely a temporary restriction in this slice. YAML `deck` governs new managed Cards only. Preview and application share normalized inputs and per-Note Field/tag change reporting; existing Deck differences are intentionally ignored.
