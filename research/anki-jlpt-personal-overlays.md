# Personal content over upstream JLPT Notes, without losing learning records

- **Investigation date:** 2026-11-13.
- **User context:** Current Anki Desktop and AnkiMobile; no custom Fields or Template changes yet. Exact application versions and installed upstream release are unknown. These are user-supplied facts, not inspected Collection data.
- **Baseline:** Latest upstream release returned by GitHub was `26.09.06`, with `eggrolls-JLPT10k-v3.5.apkg`. Official Anki Desktop latest was `26.09.4`, published 2026-11-04; source behavior below is pinned to that release. [U1] [A1]
- **Evidence:** Context7 resolved the official Anki manual and add-on documentation first. Findings were checked against official documentation, pinned Anki source, upstream source, and actual upstream package databases. No dependencies were installed, no user Collection was opened, and no migration/import behavior was executed. Python inspection used the existing root `.venv` and standard-library tools only.

## Recommendation

**Keep the existing studied Notes and Cards. Put personal examples and comments in separate, user-owned Fields on those Notes, and maintain a separate overlay keyed by upstream `NoteID`. Apply future upstream changes with a field-aware updater, not an unprotected upstream `.apkg` import into the live Collection.** This is a proposed workflow, supported by Anki's in-place Note editing API, upstream's identity data, and the overwrite behavior established below. It is not an implemented or tested updater. [A2] [A3] [U2]

The simplest migration for this user is to **extend the existing local Note Type**, retaining its existing Fields and Card Types. No separate learning-record transfer should be necessary: adding Fields preserves existing values, and retained Card Types preserve their Cards. A separately named personal Note Type is optional, not required; if chosen, convert the existing Notes in place with explicit Card Type mappings rather than importing new copies. [A4] [A5]

Here, “without modifying upstream” means leaving the author's repository and downloaded release unchanged. The local Note Type and Templates necessarily change if new Fields should appear on Cards; changing a Template affects all Notes using that Note Type. If the user instead means *no changes even to the local upstream Note Type*, choose the optional personal Note Type conversion described below. [A4] [A6]

**Do all migration and update work on Desktop; use AnkiMobile for study and ordinary editing, then sync.** Complete Mobile-to-Desktop sync before structural changes, pause Mobile edits/reviews during the cutover, then upload the validated Desktop Collection and download it on Mobile if a one-way sync is requested. Schema changes are specifically among the operations normal sync cannot merge. [A7]

## 1. What the upstream actually contains

### Release packaging and source

- Release `26.09.06` includes a roughly 404.5 MB `.apkg` and `notes-diff-26.09.06.md`. The author's README directs users to download `.apkg`, describes updates roughly every one to two months, and recommends merge Note Types / update Notes Always / update Note Types Always. It explicitly warns that direct updates overwrite custom content, tags, Fields, and Templates. [U1] [U2]
- Repository sources are `deck-source/notes.csv`, `deck-source/templates/`, and `deck-source/medias/`. The checked release workflow generates a diff and draft release, but does **not** build an `.apkg`; the `.apkg` in this release was uploaded by the author. Do not assume cloning the repository supplies a complete identity-preserving package build pipeline. [U1] [U3] [U10]
- Despite the `.csv` extension, `notes.csv` declares `#separator:Tab`, `#html:true`, `#notetype column:1`, `#deck column:2`, and `#tags column:39`. At `26.09.06`, inspection found 10,641 data rows, each with 39 columns and the same Note Type name. There is no `#guid column`. The first *regular* column is `NoteID`, not the Note Type name or Deck name. Anki excludes the special columns from implicit Field mapping. [U5] [A8]

### Actual Note Type and Fields

Direct, read-only inspection of the release package's `collection.anki21` found **one normal Note Type**, named `eggrolls-JLPT10k-v3.5`, with internal Note Type ID `1756866447451` and **36 Fields in this order**. The following is the package schema, not an inference solely from the diff script. [U6]

| Field positions, 1-based | Exact Field names | Purpose evident from source/values |
| --- | --- | --- |
| 1 | `NoteID` | Stable upstream content identifier; UUID-shaped strings |
| 2–5 | `VocabKanji`, `VocabPitch`, `VocabPoS`, `VocabFurigana` | Japanese word, pitch, part of speech, reading |
| 6–9 | `VocabDefSC`, `VocabDefTC`, `VocabPlus`, `VocabAudio` | Simplified/traditional Chinese definitions, supplementary content, word audio |
| 10–15 | `SentType1`, `SentKanji1`, `SentFurigana1`, `SentDefSC1`, `SentDefTC1`, `SentAudio1` | Example/related-word slot 1 |
| 16–21 | `SentType2`, `SentKanji2`, `SentFurigana2`, `SentDefSC2`, `SentDefTC2`, `SentAudio2` | Slot 2 |
| 22–27 | `SentType3`, `SentKanji3`, `SentFurigana3`, `SentDefSC3`, `SentDefTC3`, `SentAudio3` | Slot 3 |
| 28–33 | `SentType4`, `SentKanji4`, `SentFurigana4`, `SentDefSC4`, `SentDefTC4`, `SentAudio4` | Slot 4 |
| 34–36 | `Order`, `Alt1`, `Alt2` | Ordering data and Card-generation switches |

**Important source discrepancy:** `scripts/diff_notes.py` calls the ordering column `Sort`; the actual `.apkg` Field is **`Order`**. A build/updater must explicitly reconcile that alias or prefer the package schema; creating a new `Sort` Field would be incorrect for this package. `Notetype`, `Deck`, and `Tags` in the script's 39-column list are metadata, not three additional Fields. Native tags are rendered as `{{Tags}}`. The package's Browser sort Field index is 1, i.e. `VocabKanji`; the presence of `Order` does not establish that it is the Note Type's selected sort Field. [U4] [U5] [U6]

There is **no dedicated personal-comment Field** in this package. `VocabPlus` and all four sentence slots are already upstream-owned content. An apparently empty sentence slot is not a reserved personal slot and could be populated by a later upstream release. Separate personal Fields avoid this ownership collision. [U4] [U6]

### Card Types and Templates

The package contains two Card Types, both with persistent Template IDs: [U6]

| Card Type | Ordinal | Template ID | Generation condition in upstream Templates |
| --- | --- | --- | --- |
| `日-中` | 0 | `-1811355755207440921` | Wrapped in `{{^Alt1}}`: enabled when `Alt1` is empty |
| `中-日` | 1 | `-6774217282949026239` | Wrapped in `{{#Alt2}}`: enabled when `Alt2` is nonempty |

The source Front/Back Templates use word, definition, pronunciation, sentence, and audio Fields, plus the special fields `{{Tags}}` and `{{FrontSide}}`. The README says `中-日` is off by default and describes changing its conditional to enable it broadly. The inspected release has exactly 10,641 Cards, all ordinal 0; no ordinal-1 Cards. Preserve whichever Card Types the user has actually studied, not merely the distribution in the author's export. [U2] [U6] [U7]

Upstream provides one CSS file for the Note Type. Anki stores CSS on the Note Type, whereas this repository stores `style.css` per Card Type; a future local build must compile/scopingly combine those sources into Anki's shared CSS rather than presume two independently installed stylesheets. [U7] [A6] [A9]

## 2. Identities that must not be confused

| Identity | Actual role | Preservation requirement |
| --- | --- | --- |
| Upstream `NoteID` Field | External content key; upstream diff aligns rows with this | Keep unchanged; use exact matching plus Note Type/lineage scope |
| Anki Note GUID | Native cross-package duplicate/update key | Preserve existing GUIDs; do not substitute the UUID-shaped `NoteID` |
| Anki numeric Note ID | Collection-local Note identity | Update existing Notes rather than delete/re-add |
| Note Type ID and Field/Template IDs | Schema identity and merge matching | Retain existing objects/IDs when extending or patching |
| Anki Card ID, Note ID, Card Type ordinal | Existing Card identity and Card Type association | Keep studied Cards and map Card Types correctly |
| Review-log entries' Card ID | Links review records to Cards | Verify records still refer to retained Cards |

Sources: upstream diff's `KEY_FIELD = "NoteID"` and package data; Anki package import's GUID lookup and Note ID remapping; schema matching; Card import; Card/review-log structures. [U4] [U6] [A3] [A10] [A11] [A12] [A18]

Concrete package example: the `NoteID` value `4691ed6a-a0bb-11ef-9eca-75d1f1bae144` belongs to numeric Note ID `1736762889883` and GUID `yf4u:HnV@:`. Those three values are distinct. All 10,641 `NoteID` values in the checked source release were unique. [U5] [U6]

### Cross-release identity evidence, not a perpetual guarantee

Read-only package comparisons joined Notes on exact first-Field `NoteID` and Cards on `(NoteID, ordinal)`: [U6] [U8] [U9]

| Older package → `26.09.06` | Common Notes | Added / removed relative to older package | Identity results for common entries |
| --- | --- | --- | --- |
| `26.07.13` v3.5 | 10,634 | 7 / 0 | All numeric Note IDs, GUIDs, and corresponding Card IDs identical |
| `26.04.26` v3 | 10,161 | 480 / 10 | All numeric Note IDs, GUIDs, and corresponding Card IDs identical |

All three inspected packages have the same internal Note Type ID, all 36 Field IDs, and both Template IDs. The v3 package's Note Type **name** differs, but the identities match. This supports an in-place update path for the common Notes in these releases; it does not prove that every historical or future release, the AnkiWeb variant, or this user's Collection has matching identities. [U6] [U8] [U9]

The author explicitly says **v2 and v3 are independent and cannot update each other by direct import**. Therefore an installed v2 Collection needs a separately assessed migration. Do not generalize the observed v3→v3.5 identity continuity backwards to v2. [U2]

## 3. What recent Anki updates preserve—and overwrite

### `.apkg` Note updating

Anki finds existing Notes by **GUID**, not by `NoteID` or word text. In the pinned importer, updating replaces the incoming Note's numeric ID with the existing Note's ID, then saves the incoming content and tags. When merging is disabled and Note Types conflict, the importer can skip updates and create/use a separate Note Type for incoming Notes instead. [A3]

The default update policy is modification-time based. Editing a personal Field changes the *whole Note's* modification time: it is not a per-Field conflict-resolution system. Thus “If newer” can prevent needed upstream updates while a forced update can overwrite user content. [A2] [A3] [A13]

Since Anki 23.10, import exposes update controls for Notes and Note Types, schema merging, and **Import any learning progress**. Disabling learning-progress import avoids adopting the author's exported scheduling/history for newly imported Cards; it does not reset existing studied Cards. The manual also says that disabling this option strips imported `leech`/`marked` tags. [A13] [A10]

Implementation nuance: in Anki `26.09.4`, the generic `should_update()` used for Notes treats **Always** as “different modification timestamps,” not “rewrite even when timestamps are identical.” Note Type selection during the merge path has a separate check where Always returns true. Do not rely on repeated same-package imports as an unconditional content refresh mechanism. [A3]

### Schema merging is not personal-content protection

The manual states that merge preserves the union of Fields and Templates, and uses Field/Template IDs introduced in 2.1.67, falling back to names when IDs are missing. The actual latest JLPT package contains IDs for all Fields and both Templates. [A13] [U6]

**But keeping a Field definition does not keep its value.** The pinned importer expands incoming Notes to the merged schema, inserting empty strings for Fields absent upstream, then writes the incoming Note. Its regression test `should_merge_conflicting_notetype_even_without_original_id` explicitly ends with the local-only Field value becoming `""`. The same blank-padding mechanism is used by `reorder_fields()`. Consequently, adding `UserNotes` locally and enabling merge plus Note updates is not sufficient protection. [A3] [A4]

Matching Template objects are not HTML/CSS three-way merged. The selected incoming or existing Note Type supplies the matching objects' content; merge adds missing objects. Thus Update Note Types Always can replace personal modifications to an existing Back Template or the shared CSS, even while retaining additional Fields. “Never update Note Types” is not a complete structural freeze if merge is enabled: the merge path still constructs and saves a union schema. [A3] [A11]

### Scheduling and review history

For existing Cards, the pinned `.apkg` importer skips a Card whose `(existing Note ID, Card Type ordinal)` already exists; it does not overwrite that Card's schedule. Incoming review-log entries are imported only for newly added Cards recorded in its Card-ID map. This is why a normal identity-compatible package update can change Note text without replacing the user's existing scheduling or review history. Schema changes/Card Type remapping still need testing. [A10]

The checked latest package itself has **zero review-log entries** and all exported Cards are new (`type=0`, `queue=0`). That observation applies only to that package, not a general promise about every future export. Leave learning-progress import off for upstream content updates anyway. [U6] [A13]

Changing a Note Type in place can preserve scheduling, but **only retained/mapped Cards retain their identity**. Anki's conversion source deletes unmapped Cards, rewrites mapped ordinals on retained Cards, keeps the existing Note object, and generates missing Cards. Its test verifies an existing Card keeps its Card ID even when mapped to a different ordinal. Inspect the mapping rather than blindly accepting suggested names/positions. [A5] [A14]

Likewise, editing Templates preserves Cards for retained Card Types, but deleting a Card Type removes its Cards, and changes to Front Templates can generate missing Cards. New Cards do not inherit the schedule of an existing Card simply because their Notes contain the same vocabulary. [A4] [A10]

## 4. Proposed overlay/update architecture

The following is a **design recommendation**, not an assertion that Anki natively offers an “overlay” feature.

### Content ownership

- **Upstream-owned:** existing vocabulary/definition/audio/sentence Fields, with an explicit policy for `Order`, `Alt1`, `Alt2`, tags, and Deck placement. Do not silently treat upstream's Card-generation switches as safe to overwrite.
- **User-owned:** suggested new Fields `UserExamples` and `UserNotes`; possibly `UserExampleAudio`, `UserExampleTranslation`, and `UserExampleSource` if required. These names are proposals, not existing upstream Fields.
- **Generated Templates:** upstream baseline plus a reproducible local patch adding personal sections, preferably on the Back only initially. Patches must fail clearly if upstream anchors/schema change.
- **Learning state:** existing Cards and review-log records; not owned by an upstream-content updater. Preserve Deck options, FSRS settings, suspension, flags, and existing Card placement by default.

Separating personal Fields avoids modifying upstream's content slots. Anki's editing API can load a Note, change chosen Fields, and save it without rebuilding it; the native schema-change code preserves retained Card Types. This supports the design, but does not substitute for acceptance tests. [A2] [A4]

Illustrative external overlay record, **not a file/schema created by this investigation**:

```yaml
NoteID: "4691ed6a-a0bb-11ef-9eca-75d1f1bae144"
UserExamples: "自分で作った例文。"
UserNotes: "My explanation or mnemonic."
```

Key records by `(upstream lineage, NoteID)`, and maintain a validated mapping to existing Anki Note IDs/GUIDs. Reject missing, duplicated, or ambiguous identities rather than silently adding duplicates. Scope user-created Notes separately. Upstream uses `NoteID` for diffs; Anki uses GUIDs for packages and first Fields/Note Type scopes for ordinary text import. [U4] [A3] [A8]

If implemented here, declare a parent `note-type.md` and `entries-config.yaml` before authoring actual entry YAML; preserve this repository's Note Type → entries/Card Types hierarchy, quoted first-Field IDs, generated-CSV workflow, and flat `media/` naming rules. This report is research only and does not establish or modify those schemas. [R1]

### Recommended update route: selective in-place application

1. Pin a release and inspect its `.apkg` in a **disposable, unsynced staging Profile/Collection** to obtain the actual schema, media, GUIDs, and content. The source text/diff remains useful for reviewing changes; resolve `Sort`→`Order` explicitly if parsing source. [U4] [U6]
2. Resolve upstream content keys to the user's **existing** Notes. Fetch those Notes and update only approved upstream-owned Fields; leave user-owned Fields untouched. Create genuinely new upstream Notes separately, with an explicit identity strategy that remains compatible with the selected future update route. Never delete/re-add existing Notes to update them. The official `anki` module supports Note updates and can operate independently of the GUI. [A2] [A15]
3. Patch retained Templates/Field objects in place, keeping their IDs and ordinals. Compile the upstream baseline plus the local personal sections into Front/Back Templates and shared CSS. Refuse unexpected Field/Card Type removals or identity changes until a migration is approved. [A4] [A11]
4. Copy required media with Anki's media APIs, or through a separately tested staging/import procedure; do not rewrite media references to repository paths. The manual requires flat media references such as `[sound:filename.mp3]` and `<img src="filename.jpg">`. Existing upstream media names do not follow this repository's naming convention; avoid renaming imported references casually. Name newly repository-managed personal assets according to this repository's convention. [A8] [R1]
5. Produce an audit/dry-run report: changed Fields, added Notes/Cards, removed upstream content, conflicts, media changes, and schema changes. Treat disappearing upstream Notes as a review queue, not an automatic delete instruction. The author says removed content and changed Deck structure require manual cleanup; preserve studied retired Notes unless explicitly approved otherwise. [U2]

A future implementation can build on the API approach investigated in [the existing headless-import research](anki-headless-import.md), but that report is not evidence that an updater already exists. An external Python updater should run with Desktop fully closed; an add-on should use Anki's Collection operations. Official docs strongly discourage direct database writes because they can bypass synchronization bookkeeping and integrity checks. [A2] [A15]

**Editing authority must be decided:** if personal content is edited in Desktop/Mobile, export/harvest those Fields into the overlay before any replay, with conflict detection. If YAML is authoritative, Anki edits must be deliberately reconciled or rejected. Otherwise a “safe” upstream updater can still overwrite newer user edits when it reapplies an old overlay. This is a proposed ownership rule, not a claim that Anki sync exports YAML. [A7]

### Alternatives and trade-offs

| Approach | Assessment |
| --- | --- |
| Existing local Note Type + selective updater | **Recommended:** minimal identity migration; requires implementing/rehearsing a field-aware update process. |
| Clone a personal Note Type, then Change Note Type on studied Notes | Useful for visibly separating local schema ownership. Map all original Fields and each studied Card Type explicitly; keep `NoteID` first. Do not import new copies and attempt to rediscover progress afterward. [A5] |
| Import upstream `.apkg`, then restore overlay and patch Templates | Simpler but has a loss window: snapshot personal Fields first; require successful restore/verification before syncing or study. Prefer doing the entire import/restore on a disposable Collection copy and validate before cutover. Raw import can blank personal Fields. [A3] |
| Build a combined `.apkg` from a fresh upstream staging Collection + current overlay | Feasible in principle using official import/edit/export APIs. Preserve GUIDs and schema IDs from upstream; use a current snapshot of user values, not blank placeholders. Test carefully: new GUIDs from rebuilding through plain-text import are incompatible with the user's original package identity. [A2] [A3] [A8] |
| Text update by existing `NoteID` | Useful for content-only updates because text import updates existing Notes in place and preserves scheduling. It does not provide Templates/media packaging; ensure correct Note Type, Field mapping, match scope, and treatment of omitted/blank personal Fields. A complete effective row or tested selective mapping is safer than assuming blank means “leave unchanged.” [A8] |
| Special Fields add-on | Potential convenient Field protection, but exact-version compatibility and the actual import path must be proved. It is not needed for the recommended selective updater. See caveats below. |
| Edit `VocabPlus`/unused upstream sentence slots | Avoid: these are upstream-owned, and the author warns that imports overwrite modifications. [U2] [U4] |

With a cloned personal Note Type, **do not presume a raw upstream import leaves that Note Type alone**. The merge importer detects matching-GUID Notes with conflicting Note Types, merges schemas, and can convert those Notes to the incoming Note Type. Keeping a distinct name is not an isolation boundary against future `.apkg` imports. [A3]

### Add-on caveats

- Upstream recommends Special Fields (`1102281552`). However, the maintainer of an Anki26+ fork (`92238674`) explicitly says the original is unmaintained/broken on current Anki, and cautions that the fork is new and should be tested with backups. Treat this as a maintainer claim, not a verified compatibility test on the user's unspecified version. Do not recommend installing the original blindly. Field protection also does not automatically reapply personal additions to a matching upstream Template. [U2] [P1] [A11]
- For actual v2→v3 identity breaks, upstream recommends Transfer Scheduling Info Advanced (`1249258442`). Its README makes review-history transfer **optional**, warns that target review history is overwritten, and says unstudied source Cards are skipped. Therefore “transfer scheduling” alone does not meet a requirement to preserve all review records. [U2] [P2]
- The transfer add-on's inspected source directly updates selected `cards` columns, including `data`, deletes target review-log rows, and recreates source review-log rows with slightly offset timestamps/IDs. Its target search can match multiple Cards, and the chosen Note Type controls available UI choices but is not explicitly included in the transfer search. It must not be treated as a proven exact one-to-one migration or a byte-identical review-history transfer. Current FSRS/sync compatibility needs rehearsal; copying `data` is not proof that every current scheduler property transfers correctly. Prefer retaining original Card identity when possible. [P3] [A2] [A12]

## 5. Safe migration and acceptance tests

These steps are **recommended experiments and acceptance criteria**. They have not been run against this user's Collection.

### Before making changes

1. Record exact Desktop/Mobile versions, upstream source/release, Note Type name/ID, Fields, Card Types, whether `中-日` exists/studied, and any duplicate `NoteID`/GUID situations. Obtain a small identity-preserving export if a developer will inspect it; do not assume a vocabulary text export contains scheduling. [A3] [A8]
2. Sync Mobile fully, then Desktop, and confirm recent Mobile reviews are present on Desktop. Pause Mobile study/editing for the migration. Schema conflicts can discard one side's unsynced work during a one-way sync. [A7]
3. Export an **Anki collection package `.colpkg` with media**, keep it outside the working Profile, and test restoration in a separate **unsynced** Profile. Automatic/Create Backup backups contain card data/scheduling but omit sounds/images. A `.colpkg` restore replaces Collection data; never restore the rehearsal over the live Profile accidentally. [A16] [A17]
4. Keep a separate snapshot of personal Field content and Templates once they exist, plus an identity/scheduling manifest. Test Profiles must not sync to the production AnkiWeb account; using multiple Profiles against one account can cause data loss. [A7]

### Initial local migration

1. On a restored disposable Collection, append the approved personal Fields to the existing Note Type, preserving existing Field/Card Type IDs and order. Start with personal sections on the Back so no new learning task or conditional Card generation is intended. Anki's schema-change tests preserve old values when adding a Field. [A4]
2. If choosing a cloned personal Note Type instead, use **Change Note Type** on existing Notes. Map each old Field to its counterpart and `日-中`→`日-中`, `中-日`→`中-日` wherever Cards already exist; map no studied Card Type to “nothing.” Inspect any proposed new Cards. [A5]
3. Test representative Notes: new, learning/relearning, mature review, suspended, flagged, and both directions if applicable. Preserve existing Decks/presets during this test. Moving Cards between Decks can adjust remaining steps and recalculate FSRS memory state in the pinned version, even without rescheduling due dates; do not bundle Deck reorganization into a content-only migration. [A12]

### Required checks before declaring success

- Every pre-existing target Note retains its numeric Note ID, GUID, and `NoteID`; expected Note Type changes are documented. [A3] [A5]
- Every pre-existing studied Card retains its Card ID and intended direction/Card Type mapping. No unexplained missing or duplicate Cards. [A4] [A5]
- Compare existing Cards' due dates, intervals, queue/type, review/lapse counts, ease/remaining steps, suspension/flags, original Deck/due state, and FSRS stability/difficulty/retention/decay/last-review values where present. Ignore only explicitly expected bookkeeping changes, not scheduler changes. [A12]
- Compare **full review-log records per retained Card**, not only aggregate review totals or the appearance of the next due date. IDs, timestamps, ratings, intervals, timing, and review kinds matter. [A10] [A18]
- Personal Fields remain identical; approved upstream corrections appear; unrelated Notes/Deck options remain untouched. Personal examples render on Desktop and Mobile and referenced media plays after full media sync. [A2] [A7] [A8]

### Update rehearsal matrix

1. Add unmistakable personal sentinel values to a handful of Notes. Re-import a newer package with merge/update enabled in the disposable Profile to demonstrate the actual overwrite risk on the installed version; never perform this destructive experiment on live data. [A3]
2. Apply the proposed field-aware updater instead. Verify sentinel preservation **and** an actual upstream correction on the same Note. Test a locally newer Note, not only untouched Notes. [A3]
3. Apply the same update twice: no duplicate Notes/Cards, no scheduler/review-log changes, no lost personal content, and ideally no unnecessary writes. Account for the package importer's equal-timestamp nuance. [A3] [A10]
4. Simulate an added upstream Field, a renamed Field with preserved ID, a changed Front/Back Template, a newly activated Card Type, retired content, missing media, duplicate `NoteID`, stale overlay, and failed restoration. Require a clear abort/review result for unsupported cases. Schema matching is identity-based, and generation changes can add Cards. [A4] [A11]

### Production cutover

Once the rehearsal passes, take a fresh backup and reconcile any reviews/edits since the rehearsal. Repeat the validated procedure on Desktop, verify again, then sync. If a one-way sync is required, choose **Upload on Desktop**, then **Download on AnkiMobile**, only after both sides' pre-migration work has been consolidated. Media sync is always merged, even during a one-way Collection sync; wait for media completion separately. Resume Mobile study only after checking examples, notes, audio, and recent review history. [A7]

Do not delete the old backup or retired studied content merely because the new text looks correct. If the installed lineage is v2, stop and design/test a separate identity mapping and history-transfer plan before adopting v3/v3.5; the source's migration screenshots are not proof that all this user's Notes/history will map cleanly. [U2] [P2] [P3]

## 6. User information still needed

1. Exact Desktop and AnkiMobile versions, and installed JLPT version/source (GitHub `.apkg` or AnkiWeb alternative).
2. Current Note Type name/ID, any duplicates, and whether the reverse Card Type is enabled or studied.
3. Should personal examples **supplement** upstream examples or replace what is displayed? Back only, Front too, audio, furigana, translation, multiple examples, and source attribution requirements?
4. May the local upstream Note Type be extended, or must it remain untouched even locally, requiring a personal Note Type conversion?
5. Where will personal content be edited—repository YAML, Desktop, Mobile, or all three—and which wins on conflict?
6. Is implementing a small updater acceptable, or is a tested add-on/manual import-and-restore workflow preferred?
7. What counts as preservation: Card identity and complete history/FSRS state, plus Deck placement, suspension, flags, and retired Notes? The safest default here is to retain all of these.

## Evidence limitations and reproduction notes

- Source/package checks were real; live Anki imports, schema merges, add-ons, Mobile rendering, and migrations were **not** executed. Package identity continuity is observed for three releases, not guaranteed for the user's installation or future releases.
- Package inspection fetched explicit HTTP byte ranges for ZIP metadata and `collection.anki21`, decompressed the selected entry with Python `zipfile`, and queried it in an in-memory SQLite database. No media or user database was written. ZIP entry integrity was checked by `zipfile`; the full 404.5 MB asset's SHA-256 was **not** independently recomputed. GitHub lists its digest as `23fcc9bd39b87013c254ec15c4aa77d13dbd61f37d8b41914f6c43a0b7849ed2`. [U1]
- Reproduction queries include `select models from col`, `select id,guid,mid,flds from notes`, `select nid,ord,id from cards`, `select count(*) from revlog`, and `select type,queue,count(*) from cards group by type,queue`; split `flds` on `\x1f`. Identity comparisons use exact first-Field `NoteID`. These are read-only queries on release artifacts, not recommended writes to a live Collection. [U6] [U8] [U9]
- License: upstream declares CC BY-NC 4.0 and asks for egg rolls attribution, the release link, disclosure of modifications, and noncommercial use. Keep attribution if distributing a derived build. This is a statement of the author's terms, not a legal analysis. [U2]

## Primary sources

[U1]: https://api.github.com/repos/5mdld/anki-jlpt-decks/releases/latest "GitHub upstream release metadata, checked 2026-11-13"
[U2]: https://github.com/5mdld/anki-jlpt-decks/blob/26.09.06/README.md "Upstream author: updates, migration, customization, licensing"
[U3]: https://github.com/5mdld/anki-jlpt-decks/tree/26.09.06/deck-source "Pinned upstream source tree"
[U4]: https://github.com/5mdld/anki-jlpt-decks/blob/26.09.06/scripts/diff_notes.py "Pinned upstream Field list, NoteID diff key, Sort alias"
[U5]: https://github.com/5mdld/anki-jlpt-decks/blob/26.09.06/deck-source/notes.csv "Pinned upstream tab-separated Note source"
[U6]: https://github.com/5mdld/anki-jlpt-decks/releases/download/26.09.06/eggrolls-JLPT10k-v3.5.apkg "Actual inspected latest release package"
[U7]: https://github.com/5mdld/anki-jlpt-decks/tree/26.09.06/deck-source/templates "Pinned Front/Back Templates and CSS"
[U8]: https://github.com/5mdld/anki-jlpt-decks/releases/download/26.07.13/eggrolls-JLPT10k-v3.5.apkg "Actual inspected prior v3.5 package"
[U9]: https://github.com/5mdld/anki-jlpt-decks/releases/download/26.04.26/eggrolls-JLPT10k-v3.apkg "Actual inspected v3 package"
[U10]: https://github.com/5mdld/anki-jlpt-decks/blob/26.09.06/.github/workflows/draft-release.yml "Pinned release workflow generates diffs/drafts, not an apkg build"
[A1]: https://github.com/ankitects/anki/releases/tag/26.09.4 "Official Anki baseline release"
[A2]: https://docs.ankiweb.net/addons/the-anki-module "Official Collection editing and import/export API documentation"
[A3]: https://github.com/ankitects/anki/blob/26.09.4/rslib/src/import_export/package/apkg/import/notes.rs "Pinned package Note/schema importer and tests"
[A4]: https://github.com/ankitects/anki/blob/26.09.4/rslib/src/notetype/schemachange.rs "Pinned Field/Card Type schema-change behavior and tests"
[A5]: https://github.com/ankitects/anki/blob/26.09.4/rslib/src/notetype/notetypechange.rs "Pinned Change Note Type mappings, deletion, identity-preservation test"
[A6]: https://docs.ankiweb.net/templates/intro.html "Official Template/Note Type scope"
[A7]: https://docs.ankiweb.net/syncing.html "Official syncing, schema conflicts, one-way cutover, media, Profile warning"
[A8]: https://docs.ankiweb.net/importing/text-files.html "Official text import, identity/mapping, scheduling preservation, media"
[A9]: https://github.com/ankitects/anki/blob/26.09.4/rslib/src/notetype/schema11.rs "Pinned Note Type schema including shared CSS"
[A10]: https://github.com/ankitects/anki/blob/26.09.4/rslib/src/import_export/package/apkg/import/cards.rs "Pinned existing-Card skipping and incoming review-log handling"
[A11]: https://github.com/ankitects/anki/blob/26.09.4/rslib/src/notetype/merge.rs "Pinned Field/Template ID matching and merge behavior"
[A12]: https://github.com/ankitects/anki/blob/26.09.4/rslib/src/card/mod.rs "Pinned Card scheduling/FSRS representation and Deck-move behavior"
[A13]: https://docs.ankiweb.net/importing/packaged-decks.html "Official package update controls, merge, scheduling since 23.10"
[A14]: https://docs.ankiweb.net/browsing.html "Official Change Note Type scheduling/full-sync statement"
[A15]: https://docs.ankiweb.net/addons/command-line-use "Official GUI-independent anki module guidance"
[A16]: https://docs.ankiweb.net/backups.html "Official media-inclusive manual backups and restoration"
[A17]: https://docs.ankiweb.net/exporting.html "Official package/Collection export/import distinctions"
[A18]: https://github.com/ankitects/anki/blob/26.09.4/rslib/src/revlog/mod.rs "Pinned review-log record identity and review data"
[P1]: https://shigeyukey.github.io/shige-addons-wiki/special-fields.html "Special Fields fork maintainer: Anki26+, original incompatibility and test warning"
[P2]: https://github.com/kaCVanime/anki-transfer-scheduling/blob/master/README.md "Transfer add-on author's usage, optional review-history transfer, overwrite warning"
[P3]: https://github.com/kaCVanime/anki-transfer-scheduling/blob/master/__init__.py "Transfer add-on primary source; inspected 2026-11-13"
[R1]: ../AGENTS.md "This repository's schema, YAML/CSV, hierarchy, media, and deletion rules"
