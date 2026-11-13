# Headless Anki import/update feasibility

- **Investigation date:** 2026-11-10
- **Design feedback recorded:** 2026-11-13; source baseline remains unchanged.
- **Source baseline:** Anki 26.09.4, published 2026-11-04; the latest released version when investigated. [Official release](https://github.com/ankitects/anki/releases/tag/26.09.4)
- **Status:** Research and proposed design only. No updater implemented, packages installed, or tests run against a real Collection.
- **Evidence:** Context7 was consulted first for Anki and AnkiConnect documentation; exact behavior was checked against official documentation and upstream source.

## Outcome and scope

**Recommended approach: use Anki's official Python `anki.collection.Collection` API with Anki Desktop fully closed.** Official documentation supports using the `anki` module separately from the GUI and recommends it instead of directly reading/writing `.anki2` files. The Python Collection opens the Rust backend without importing the Desktop GUI. [Command-line use](https://github.com/ankitects/anki/blob/26.09.4/docs-site/addons/command-line-use.mdx), [Collection initialization](https://github.com/ankitects/anki/blob/26.09.4/pylib/anki/collection.py#L151-L184), [Rust bridge](https://github.com/ankitects/anki/blob/26.09.4/pylib/anki/_backend.py)

### User decisions

- Anki Desktop must remain fully closed during an update.
- Automate Notes, Note Types, Card Type Front/Back Templates, CSS, Deck creation, and existing Card placement.
- Preserve existing Card identity and review history; do not reset learning progress.
- Repository-managed content wins over edits to that content in Anki.
- Do not change Deck options/settings or automate AnkiWeb sync.
- Preserve manual deletion through `REPO_DELETE`; do not infer deletions from absent entries.
- Use one shared stylesheet per Note Type; adjust the repository structure rather than build a CSS compilation/merging tool.
- All repository-defined Decks already have corresponding Decks in Anki. Verify the API first, then link repository Deck definitions to those existing Decks.
- Personal tags need not be preserved on repository-managed Notes; use repository tags as the complete desired tag set.
- Read entry YAML directly in the proposed updater. CSV generation is only needed for the existing Desktop text-import workflow and can be retired after the API workflow is verified and repository instructions are updated.

These decisions define ownership and scope, not proof that a particular updater is safe. Safety and idempotency must be demonstrated on disposable Collections before live use. Referenced media handling is investigated below as a proposed supporting capability, not a separately confirmed user requirement.

## Verified capabilities

The following mechanisms exist in the pinned official Python source. They are capabilities, not an implementation proposal that has been executed.

| Operation | Official mechanism |
| --- | --- |
| Open Collection | `Collection(absolute_collection_path)` |
| Create Note Type | `col.models.new()`, `new_field()` / `add_field()`, `new_template()` / `add_template()`, then `add_dict()` |
| Update existing Note Type | Fetch existing object, modify it, then `col.models.update_dict()` |
| Update Front/Back Templates | Existing `tmpls` entries' `qfmt` / `afmt` properties |
| Update CSS | Note Type's single `css` property |
| Add Note | `col.new_note(notetype)`, populate fields/tags, then `col.add_note(note, deck_id)` |
| Update Note | `col.get_note(note_id)`, modify fields/tags, then `col.update_note(note)` |
| Create/reuse normal Deck | `col.decks.add_normal_deck_with_name(name)` |
| Find a Note's Cards | `col.card_ids_of_note(note_id)` |
| Move existing Cards | `col.set_deck(card_ids, deck_id)` |
| Add media | `col.media.add_file(path)` / `write_data(basename, bytes)` |
| Release Collection | `col.close()` |

Table sources: [Collection API](https://github.com/ankitects/anki/blob/26.09.4/pylib/anki/collection.py), [Note Type manager](https://github.com/ankitects/anki/blob/26.09.4/pylib/anki/models.py), [schema representation](https://github.com/ankitects/anki/blob/26.09.4/rslib/src/notetype/schema11.rs), [Deck manager](https://github.com/ankitects/anki/blob/26.09.4/pylib/anki/decks.py), [media manager](https://github.com/ankitects/anki/blob/26.09.4/pylib/anki/media.py).

Saving is automatic: `Collection.save()` and `autosave()` are deprecated no-ops. `close()` releases the backend Collection and database connection; it should run in cleanup even after failure. Native operations commit or roll back individually, but a sequence of API calls is not automatically one atomic deployment. [Lifecycle](https://github.com/ankitects/anki/blob/26.09.4/pylib/anki/collection.py#L281-L319), [native transactions](https://github.com/ankitects/anki/blob/26.09.4/rslib/src/collection/transact.rs)

## Note identity and review-history preservation

### Matching repository Notes

The repository's identity is the stable custom first Field, scoped by Note Type: **`(Note Type, exact custom ID)`**. It is not Anki's internal GUID. Official text-import documentation recommends placing custom IDs in the first Field and describes matching existing Notes of the same Note Type by that Field. [Text import and GUIDs](https://docs.ankiweb.net/importing/text-files.html)

Proposed reconciliation rules:

1. Validate quoted, nonempty stable IDs and uniqueness within each Note Type across all entry files.
2. Resolve an exact key to an existing Anki Note ID; verify the fetched Note's Note Type and first Field.
3. Fail on duplicate/ambiguous matches rather than choosing one or adding another Note.
4. Load and update existing Notes in place; retain internal Note IDs and GUIDs.
5. For new Notes, let Anki generate its internal identity; do not assign the custom ID as GUID.
6. Reject unexpected Note Type changes, renamed identity scopes, or unsupported schema mismatches.

Anki's Note object exposes internal ID/GUID, tags, and fields separately. Updating a loaded object retains those identities unless deliberately changed. New Notes receive an Anki-generated GUID. [Python Note representation](https://github.com/ankitects/anki/blob/26.09.4/pylib/anki/notes.py#L36-L80), [native new Note](https://github.com/ankitects/anki/blob/26.09.4/rslib/src/notes/mod.rs#L143-L155)

### Ordinary Note updates

Native Note updates save Note content and generate missing Cards. Card generation excludes template ordinals already represented by existing Cards. Therefore ordinary field/tag updates retain existing Cards and their scheduling/history rather than recreating them. Changes can nevertheless activate conditional Card Types and add new Cards. [Native update](https://github.com/ankitects/anki/blob/26.09.4/rslib/src/notes/mod.rs#L432-L478), [missing-Card generation](https://github.com/ankitects/anki/blob/26.09.4/rslib/src/notetype/cardgen.rs#L94-L159)

The proposed updater must never delete/re-add a Note to implement an update, answer Cards, reset due dates, or write scheduler state directly. Acceptance tests must verify preservation, not merely compare displayed text.

## Note Types and Card Type Templates

For existing Note Types, mutate the fetched Field/template objects in place and retain their IDs, ordinals, and unrelated settings. Do not reconstruct the entire Note Type from repository names on each run. Official update methods accept the existing Note Type representation and perform native checks. [Note Type updates](https://github.com/ankitects/anki/blob/26.09.4/pylib/anki/models.py#L224-L238)

Verified native Template behavior:

- Retained templates preserve their existing Cards, including Cards whose questions become empty.
- Front Template changes can generate previously missing Cards.
- Removing a template removes its Cards.
- Reordering retained templates changes existing Card ordinals rather than recreating the Cards.
- Structural changes can mark the schema modified.

These behaviors are visible in [native template-change handling](https://github.com/ankitects/anki/blob/26.09.4/rslib/src/notetype/schemachange.rs#L122-L176).

**Blast radius:** a Note Type's Templates affect every Note using that Note Type, including Notes outside repository entry files. The generation pass runs for the Note Type, not just a supplied entry subset. [Note Type-wide generation](https://github.com/ankitects/anki/blob/26.09.4/rslib/src/notetype/cardgen.rs#L269-L292)

**Proposed MVP restriction:** create missing Note Types with the approved schema; for existing Note Types, update only retained Front/Back Templates and shared CSS. Reject Field/template additions, removals, renames, reorderings, and Note Type conversion until an explicitly approved migration exists. Preserve unrelated metadata and template Deck overrides; flag overrides that conflict with intended placement rather than silently changing them.

## CSS: move shared styling to the Note Type level

**Anki stores one stylesheet per Note Type, shared by all its Card Types.** The official manual supports Card-Type-specific selectors such as `.card1` and `.card2`. This differs from the repository's per-Card-Type `style.css` source organization. [Official styling documentation](https://docs.ankiweb.net/templates/styling.html), [Note Type CSS representation](https://github.com/ankitects/anki/blob/26.09.4/rslib/src/notetype/schema11.rs#L40-L59)

**Decision:** keep one human-authored stylesheet per Note Type, matching Anki's native model. The user clarified that “per-note styling” means per Note Type, not per individual Note. The small expected number of Card Types does not justify a CSS compilation or merging tool.

**Action item — adjust repository structure:** move styling to `note-types/{NoteTypeName}/style.css`; retain `front.html`, `back.html`, and `design.md` under each Card Type. Update [AGENTS.md](../AGENTS.md) and affected design/schema documentation to replace the current per-Card-Type styling rule. This report records the action item only; no styles or repository instructions are migrated here.

Current styles reuse unscoped selectors such as `.card` and `.sentence`, with differing declarations. See the [Comprehension stylesheet](../note-types/Japanese_Mined_Vocab/card-types/Comprehension/style.css) and [Production stylesheet](../note-types/Japanese_Mined_Vocab/card-types/Production/style.css). Reconcile these declarations deliberately during migration rather than simply concatenate the files. Shared rules can remain unscoped; author Card-Type-specific differences directly using Anki's supported selectors where needed. Keep Card Type ordering stable if using `.cardN`, and validate Front/Back rendering on intended clients.

The updater will read the single stylesheet directly into the Note Type's `css` property. The repository wins for this styling and managed Templates. Updating them still affects unmanaged Notes sharing the same Note Type; require explicit ownership of that shared Note Type or stop.

## Deck creation and existing Card placement

**User context:** all Decks defined by this repository already have corresponding Decks in Anki. Deck creation is an API capability, not the initial deployment strategy.

**Action item — link existing Decks after API verification:** inspect existing normal Decks on a disposable Collection copy, confirm correspondence with repository definitions, and resolve those approved links to Collection-local Deck IDs. Exact hierarchical names may be used to propose matches, but fail on missing or ambiguous links instead of silently creating a Deck. Links must be validated for the selected Collection; do not assume IDs are portable to another Collection. API verification and the mapping format remain unimplemented. [Deck lookup APIs](https://github.com/ankitects/anki/blob/26.09.4/pylib/anki/decks.py)

Normal Deck creation/reuse is available through `add_normal_deck_with_name()`. Existing Card placement uses `Collection.set_deck()`, not a Note Field or a default Deck property. [Deck creation](https://github.com/ankitects/anki/blob/26.09.4/pylib/anki/decks.py#L105-L113), [Collection move API](https://github.com/ankitects/anki/blob/26.09.4/pylib/anki/collection.py)

Native moves retain Card identity and do not replace review history. For ordinary review Cards moving between normal Decks, the operation retains due date, interval, ease, review count, and lapse count. However, do **not** promise every scheduling-related property is unchanged: learning/relearning remaining steps can adjust to the destination preset; FSRS data is cleared/recomputed with `reschedule: false`; filtered-Deck state is restored when leaving one; moving into a filtered Deck is rejected. [Exact native move](https://github.com/ankitects/anki/blob/26.09.4/rslib/src/card/mod.rs#L370-L425), [Card-level move](https://github.com/ankitects/anki/blob/26.09.4/rslib/src/card/mod.rs#L194-L205)

Proposed MVP: linked existing normal Decks only; leave options/settings unchanged; initially reject filtered-Deck Cards to simplify guarantees. Report learning/FSRS adjustments separately from review-history preservation. Move managed Notes' Cards after Template/Note updates so newly generated Cards also receive their intended placement. Creating missing Decks requires a separately approved extension.

**Unresolved precedence:** entry YAML can specify `Japanese::Tadoku::<title>`, while `Japanese_Mined_Vocab/note-type.md` names `Japanese::Vocabulary`. Proposed rule: entry `deck` is authoritative, and schema Target Deck documents the default/intended scope. Obtain approval and reconcile documentation before implementation. This intentionally differs from text import, which updates existing Notes in their current Decks. [Official import placement behavior](https://docs.ankiweb.net/importing/text-files.html)

## Repository data and ownership constraints

### `Tags` discrepancy must be resolved explicitly

The repository's [Note Type schema](../note-types/Japanese_Mined_Vocab/note-type.md) and [entry configuration](../note-types/Japanese_Mined_Vocab/entries/entries-config.yaml) list `VocabID`, six additional ordinary Fields, and `Tags` eighth as a “Field.” The [converter](../tools/yaml_to_csv.py) emits `#tags column:8`, mapping that column to native metadata. Anki stores tags separately from Note fields. [CSV headers](https://docs.ankiweb.net/importing/text-files.html), [Note representation](https://github.com/ankitects/anki/blob/26.09.4/pylib/anki/notes.py#L60-L80)

Do not silently redefine the schema or create an eighth ordinary `Tags` Field. Resolve the schema/config terminology and inspect the target Note Type first. The proposed YAML adapter treats the entry's `Tags` value as native `note.tags`, not an ordinary Field, once this interpretation is approved in the repository schema. `{{Tags}}` remains Anki's native special-field syntax.

**Decision:** personal tags do not need to be preserved on repository-managed Notes. Use replacement semantics: the YAML tag set replaces the Note's existing tags; an absent, null, or empty `Tags` value means an empty tag set. No personal-tag merge or ownership namespace is needed for the initial design. This is limited to matched repository-managed Notes, not Collection-wide tag removal. Keep support for workflow tags such as `REPO_DELETE`, and report tag removals in the change summary. This policy does not remove tags or change schemas now.

### Normalization and generated artifacts

**Yes: YAML can be the direct source for adding/updating Notes through the API, without an intermediate CSV.** Anki does not itself parse this repository's YAML format. The proposed updater parses YAML, validates it against the schema/config, resolves Note identity and the linked Deck, assigns ordinary Field values and native tags, then calls `add_note()` or `update_note()`. CSV headers and Desktop import dialogs are not involved. [Official Collection access and Note updates](https://addon-docs.ankiweb.net/the-anki-module.html), [headless use](https://github.com/ankitects/anki/blob/26.09.4/docs-site/addons/command-line-use.mdx), [Collection API](https://github.com/ankitects/anki/blob/26.09.4/pylib/anki/collection.py)

The [converter's `entry_to_row()`](../tools/yaml_to_csv.py) currently normalizes values with `str(value).strip()` and replaces internal newlines with `<br>`. Preserve the intended HTML Field content when migrating existing Notes, without coupling the API updater to CSV generation. Keep Field order, quoted stable IDs, required values, and unknown-Field validation aligned with the approved schema/config. Tags need their own metadata parsing rather than HTML Field normalization.

**Action item — retire the mandatory CSV workflow after API verification:** update [AGENTS.md](../AGENTS.md), [tools documentation](../tools/README.md), Note Type workflow documentation, and affected tests so YAML-to-Collection updates replace Desktop CSV import as the canonical workflow. Decide explicitly whether to remove or retain the converter, generated CSV files, and root `entries/` symlinks as an optional fallback. Do not delete those artifacts as part of this investigation. Until the instructions are changed, existing entry YAML edits still require CSV regeneration; this report does not override the active rules.

### Manual deletion only

Absence from YAML is not authorization to remove a Note. Under the proposed API workflow, add `REPO_DELETE` in YAML, apply the tag update through the API, and let the user manually delete matching Notes before removing their YAML entries. CSV is unnecessary for this future workflow, but the existing regeneration/import rule remains active until amended. Do not automatically remove empty Cards, delete templates, or garbage-collect media.

## Media and backup safety

Repository media uses a flat namespace and stable basenames; references contain `[sound:basename]` or `<img src="basename">`, not a `media/` path. Anki's `add_file()` / `write_data()` may rename a filename when its content collides. Always inspect the returned basename. [Media API](https://github.com/ankitects/anki/blob/26.09.4/pylib/anki/media.py#L90-L101)

Proposed stable-media policy: identical bytes under the expected basename are a no-op; missing files may be added; different bytes under the same basename block the update pending explicit replacement/reference decisions. Do not silently accept collision-renamed assets, replace their meaning, or remove existing files. Media writes are not covered by an assumed whole-run database rollback.

**Back up before opening a live Collection with a potentially different version.** Opening can upgrade its schema and rejects unsupported old/new schemas. Therefore even an inspection-only dry run must use a consistent disposable copy if opening could migrate it. Pin the package to the actual installed Anki release; do not make upgrading/downgrading part of routine reconciliation. [Open-time migration](https://github.com/ankitects/anki/blob/26.09.4/rslib/src/storage/sqlite.rs#L476-L545)

Preserve a consistent Collection backup, any necessary WAL state, and media separately. Do not copy only a live `.anki2` file while ignoring its WAL. Native backup creation checkpoints the database before reading it; automatic backups exclude media. A media-inclusive Collection package or separately captured media is needed for full recovery. [Native backup](https://github.com/ankitects/anki/blob/26.09.4/rslib/src/collection/backup.rs#L25-L49), [WAL checkpoint requirement](https://github.com/ankitects/anki/blob/26.09.4/rslib/src/storage/sqlite.rs#L560-L585), [official backup documentation](https://github.com/ankitects/anki/blob/26.09.4/docs-site/manual/backups.mdx)

Anki's database connection uses exclusive locking, WAL, and zero busy timeout. Require Desktop to remain closed, prevent simultaneous updater runs, and stop on lock failure; never bypass locking. Do not replace a live Collection with a stale test copy. [Connection configuration](https://github.com/ankitects/anki/blob/26.09.4/rslib/src/storage/sqlite.rs#L62-L69)

## Alternatives and sync implications

| Approach | Fit for this request |
| --- | --- |
| Official headless Python Collection API | Recommended: directly reconciles existing Notes/Note Types and moves Cards with Desktop closed. |
| AnkiConnect | Requires running Anki Desktop and an active profile, so does not meet the closed-Desktop requirement. |
| Generate/import `.apkg` | Useful for distribution, but not a first-field-key reconciliation mechanism for existing CSV-imported Notes. |

Sources: [official headless documentation](https://github.com/ankitects/anki/blob/26.09.4/docs-site/addons/command-line-use.mdx), [AnkiConnect upstream documentation](https://git.sr.ht/~foosoft/anki-connect), [official packaged-Deck documentation](https://docs.ankiweb.net/importing/packaged-decks.html).

Official Collection APIs can export/import `.apkg` without the GUI. Package Note updates match GUIDs; independently generated package Notes do not automatically match repository custom first-field IDs. The package Card importer skips existing Note/template pairs rather than updating/moving those Cards, making packages unsuitable as the primary placement reconciler. [Package APIs](https://github.com/ankitects/anki/blob/26.09.4/pylib/anki/collection.py), [GUID matching](https://github.com/ankitects/anki/blob/26.09.4/rslib/src/import_export/package/apkg/import/notes.rs#L337-L355), [existing-Card handling](https://github.com/ankitects/anki/blob/26.09.4/rslib/src/import_export/package/apkg/import/cards.rs#L99-L110)

No automated AnkiWeb sync is proposed or tested. Native changes carry modification/sync metadata, and structural changes can require a full sync. Later sync and any upload/download decision remain the user's responsibility in Anki Desktop; headless local updates are not proof of a tested headless sync workflow. [Native Note updates](https://github.com/ankitects/anki/blob/26.09.4/rslib/src/notes/mod.rs#L480-L508), [schema-change handling](https://github.com/ankitects/anki/blob/26.09.4/rslib/src/notetype/schemachange.rs)

## Proposed MVP stages and acceptance criteria

These stages are unimplemented and require explicit authorization beyond this report.

1. **Resolve configuration and action items:** actual installed Anki version/package compatibility, exact target profile and Collection path, native `Tags` schema interpretation, entry Deck precedence, and shared Note Type ownership. Record the approved Note Type-level stylesheet layout and YAML-only workflow in repository instructions before implementation; CSV retirement follows API verification. Existing root/tools virtual environments may be used later; no install or tooling execution is needed for this report.
2. **Validate and plan:** schemas, quoted IDs, duplicate keys, YAML parsing/Field normalization, Template Field references, shared stylesheet, existing Deck links/overrides, media references/collisions if included, and structural-change rejection. Produce an explicit change summary, including replacement of personal tags on managed Notes.
3. **Rehearse on a consistent disposable copy:** record baseline identities, scheduling/history, tags, Decks, media, and Card counts; apply the plan and reopen the copy to verify persistence. Opening the copy may migrate it.
4. **Link and apply only after safety checks:** after API verification, approve links to existing Decks. Require Desktop closed, single updater, verified backup/recovery path, correct version/profile, and successful rehearsal. Persist retained Templates/shared CSS, reconcile Notes/tags directly from YAML, then place Cards in linked Decks. Report partial progress if a later operation fails; do not claim whole-run atomicity.
5. **Accept only with evidence:** existing Note IDs/GUIDs and Card IDs preserved; review-history rows unchanged; ordinary review scheduling retained; learning/FSRS move adjustments explained; conditional/new Card generation reported; unmanaged content unaffected except approved Note Type-wide effects; stable media basenames retained; manual deletion workflow preserved.
6. **Verify idempotency:** a second identical run creates no duplicate Notes, Note Types, Cards, or media and no unexpected Decks; makes no unnecessary content/tag/placement changes; and leaves review history unchanged. Test lock failure, duplicate IDs, schema mismatch, missing/ambiguous Deck links, tag replacement/clearing, media collision if included, and interrupted/partial-run recovery before production use. The API path must work without generating or reading CSV.

**Conclusion:** the official headless API supports the requested workflow. The safe MVP is an in-place, version-pinned reconciliation tool with conservative schema/media handling—not database rewriting, Note recreation, package-based identity substitution, or automated deletion/sync.
