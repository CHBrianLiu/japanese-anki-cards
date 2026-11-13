# 04: Add and update Notes directly from YAML

**What to build:** An author applies a validated YAML selection to a disposable Collection using compatible existing Note Types and linked existing Decks. Missing Notes are added, matched Notes are updated in place, and repository Fields and tags win without resetting existing review history.

**Blocked by:** 03 — Preview YAML changes against linked existing Decks.

**Status:** ready-for-agent

- [ ] Apply the same validated and normalized data used by preview, without reading or generating CSV.
- [ ] Update existing Notes through native APIs, retaining internal Note IDs/GUIDs and existing Card IDs; let Anki generate internal identities for new Notes.
- [ ] Add new Notes to their linked existing normal Deck; update existing Notes without moving their existing Cards in this slice.
- [ ] Replace the complete tag set only on matched repository-managed Notes, including clearing personal tags when YAML tags are empty. Report additions and removals.
- [ ] Propagate REPO_DELETE as a tag only; never delete Notes absent from YAML, remove empty Cards, or automatically delete anything marked for cleanup.
- [ ] Reject unsupported Note Type schemas and missing referenced media before writes; leave unrelated Notes, Deck settings, Templates, and media untouched.
- [ ] Verify persisted Field/tag changes, unchanged existing review-history rows and ordinary review scheduling, and report any newly generated conditional Cards.
- [ ] A second identical application is a no-op. Failures release the Collection and report committed progress without claiming whole-run rollback.
