# Sandbox YAML preview and application

Sandbox preparation, non-mutating YAML preview, validated YAML application, and
historical direct YAML API import exploration. Commands cannot target a normal
user Collection; preview and application accept only a tool-created sandbox
folder name. Preview does not apply changes.

See [ticket 03 exploration findings](exploration.md) for executed evidence,
repository discrepancies, and the recommended next implementation steps.

## Environment

From the repository root:

```bash
python3 -m venv tools/headless_import/.venv
tools/headless_import/.venv/bin/python -m pip install -r tools/headless_import/requirements.txt
```

The official `anki` package is pinned to the inspected Desktop release (26.9.4).
The command checks version equality before backend access. `packaging` handles
zero-padding differences such as `26.09.4`. PyYAML is available for repository
exploration and direct import; no GUI or AnkiConnect dependency is used.

## Create a sandbox

```bash
tools/headless_import/.venv/bin/python tools/headless_import/create_sandbox.py
```

Each invocation creates a new persistent `tools/headless_import/.local/sandbox-*`
directory containing a Collection, its media directory, and a JSON manifest.
Both `.local/` and `.venv/` are ignored by Git. There is no Collection-path argument,
no access to the normal Anki data folder, and no Desktop profile registration.
`--anki-app /path/to/Anki.app` changes version inspection only.

The synthetic fixture contains:

- A `Headless_Preview_Fixture` Note Type with three ordinary Fields (`CustomID`,
  `Text`, `Extra`) and two Card Types (`Primary`, `Conditional`). Tags are native
  Note metadata, not an ordinary Field.
- Two normal Decks: `Preview Sandbox::Source` and `Preview Sandbox::Target`.
- A candidate managed Note with a quoted-string-compatible custom ID, old tags,
  and a native review-log row; an unrelated Note in the target Deck.
- A manifest recording identity, tags, review history, and candidate Deck IDs.
  YAML `deck` resolves by exact hierarchical name in the selected Collection.

The command closes and reopens only its own fresh Collection to verify baseline
persistence. It never reads/generates CSV, imports repository Notes, copies the
user's Collection, or syncs. Fresh Deck creation here is fixture setup only;
ticket 03 preview must reject missing target Decks instead of creating them.

## Preview YAML against existing sandbox Decks

Quit Anki Desktop completely. Select a tool-created sandbox and one or more
repository Note Types:

```bash
tools/headless_import/.venv/bin/python tools/headless_import/preview.py --sandbox sandbox-2gs8b2z0 --note-type Japanese_Mined_Vocab
```

YAML's `deck` declaration is the only Deck mapping input: it must exactly match
one existing normal Deck in the selected sandbox. No approved links, links JSON,
or alternate-name mapping is needed. Missing, ambiguous, or filtered targets fail;
no Decks are created. Repeat `--note-type` for more Note Types. Optional
`--propose-decks` lists exact-name candidates without applying changes.

The JSON report lists add/update/unchanged Notes, Field changes and tag additions
and removals, plus Note Type creation or retained Front/Back Template and shared
styling changes. Note Type effects include counts of managed and unrelated Notes
and newly generated Cards: changes affect **every** Note sharing that Note Type,
including Notes outside the selected YAML. New managed Cards include their requested and resolved Deck; existing
Card placement is ignored. The command uses a temporary SQLite backup API copy,
including committed WAL contents, opens Anki only on the copy, validates media
in the sandbox, and removes the copy on exit. It neither writes CSV nor applies
changes, creates Decks, uploads media, or retains backups. Creating fixture Decks
and media is a separate sandbox setup step. The selected Collection is independent
of YAML's `deck`; Desktop Profiles are not inspected.

## Guarded existing-Collection workflow (ticket 07)

Use `update_collection.py` for integrated rehearsal and approved application.
Quit Anki Desktop completely and select only a tool-created sandbox by name:

```bash
tools/headless_import/.venv/bin/python tools/headless_import/update_collection.py --sandbox sandbox-NAME --note-type Japanese_Mined_Vocab
```

The report contains the selected `collection`, proposed `deck_links` (exact YAML
Deck name and existing ID), shared Note Type effects, Note/Field/tag changes, and
an `approval` token. `rehearsal_verified: true` means the complete change was
executed on a disposable SQLite backup API copy and reopened to verify retained
identities, history, scheduling, existing placement, content/tags, Templates/CSS,
and new managed Card placement. Committed WAL contents are included without source
checkpoints. Referenced media is copied only into the disposable workspace, then
removed with it; no media archive or recovery package is produced.

Review the report, approve the Collection-bound Deck links, and copy its token:

```bash
tools/headless_import/.venv/bin/python tools/headless_import/update_collection.py --sandbox sandbox-NAME --note-type Japanese_Mined_Vocab --approve TOKEN --approve-deck-links --approve-note-types
```

`--approve-note-types` is required only when creating a Note Type or changing
retained Templates/shared styling. It approves ownership and effects on **all**
Notes sharing those Note Types, including unrelated Notes. `--approve-deck-links`
approves only the IDs/names in that token's selected Collection; it creates no
Decks. Repeat `--note-type` identically for multiple selections.

Approval is bound to the complete Collection database state, selected raw source
files (including comments), referenced target-media bytes, manifest, versions,
and resolved Deck IDs. Apply rehearses again and rejects stale tokens; it also
revalidates inputs and target immediately before application, then compares the
complete database evidence and source inputs again under Anki's native lock before
the first managed operation. Inline CSS media references in YAML Fields are also
validated and bound to approval. A changed target,
input, or interrupted partial application requires a fresh preview and token.
Tokens are not security credentials or saved recovery artifacts. Identical no-op
inputs may reuse the same token if the entire target state is still unchanged.
Source hashing and parsing use the same captured bytes, so a concurrent source
edit cannot substitute unapproved HTML/CSS or YAML between those two operations.

This command checks the pinned 26.9.4 environment, matching sandbox manifest,
and Collection schema version 18 **before** Anki opens the disposable copy, so
unsupported schema upgrades are not attempted. Desktop must remain closed;
updater contention and native locks block work. A Desktop Profile owns one
Collection; it is not a Collection name or YAML Deck. No Profile resolution or
normal Desktop profile-registry access is provided. Arbitrary Collection paths
and Profile names are rejected.

Only new managed Cards are placed, including Cards generated by shared Template
changes. Every existing Card retains its Deck ID without mismatch reports. Anki's
placement for new unrelated Cards is untouched. Missing Decks/media and structural
Note Type mismatches block application. There is no sync, Deck/options creation,
schema migration, Note/Card deletion, media upload/deletion, backup/restore, target
replacement, or whole-run atomicity guarantee. On failure the report describes
committed progress, not a rollback; do not retry using old approval assumptions.

### Executable sandbox-only end-to-end smoke procedure

With Desktop closed, run from the repository root using the existing exploration
environment:

```bash
HEADLESS_SMOKE_REPORT=1 PYTHONPATH=tools/headless_import tools/headless_import/.venv/bin/python -m unittest test_update_collection.GuardedCommandTests.test_complete_workflow_smoke -v
```

This procedure creates a **fresh tool-created sandbox with matching manifest**
inside a temporary isolated fixture repository. It sets up synthetic YAML,
Templates, CSS, and referenced media without editing repository entry sources.
It explicitly selects that existing sandbox by name, runs the public guarded
rehearsal, checks its Collection and Deck IDs, then passes the exact token and
Deck-link/Note Type ownership approvals to the public apply command. It independently
reopens the selected Collection to check persisted effects and history/scheduling/
placement preservation, obtains fresh approval, and runs again to prove a no-op.
The printed report identifies the selected sandbox and approved links. Fixture
and temporary rehearsal resources are disposed on exit. This is an API workflow
smoke check, not a Desktop rendering check; no personal/live Collection is accessed.

## Earlier sandbox application command

Review the preview above, keep Anki Desktop closed, then explicitly approve the
same selection:

```bash
tools/headless_import/.venv/bin/python tools/headless_import/apply_yaml.py --sandbox sandbox-2gs8b2z0 --note-type Japanese_Mined_Vocab --approve
```

If preview proposes creating a Note Type or updating shared Templates or styling,
also supply `--approve-note-types` to explicitly approve repository ownership and
the Note Type-wide effects shown in preview. No such approval flag is needed for
unchanged Note Types. Repeat `--note-type` to select more Note Types. Application
requires exact-name existing normal Decks. It shares preview's
YAML validation, normalization, matching, and per-Note Field/tag change reports.
Field Unicode normalization follows the selected Collection's Anki setting;
native tags use NFC. Stable IDs are matched in that same normalized representation,
with normalization collisions rejected rather than creating duplicate Notes.
Before target access it applies the entire selection to a disposable WAL-consistent
copy, reopens it, and verifies persistence and preservation. That copy is removed;
application creates no pre-import backup, snapshot archive, or restore artifact.

- Adds missing Notes with native identities; updates matches by exact Note Type
  and first-Field stable ID, retaining Note IDs/GUIDs and existing Card IDs.
- Creates missing Note Types, or updates only retained Front/Back Templates and
  shared styling of compatible Note Types. Structural Field/Card Type changes and
  conversions are rejected. Existing metadata and Template Deck overrides are retained.
- Replaces the complete managed Note tag set, including clearing personal tags.
  `REPO_DELETE` is only a tag; absent Notes and retained empty Cards are not deleted.
- Places **new Cards only**, including newly generated conditional Cards, in the
  YAML Deck. IDs are captured before native Note/Template updates; the reusable
  placement boundary handles only each managed Note's newly generated Cards.
  Cards already in the target Deck receive no placement operation. Existing Cards
  retain their placement without mismatch reports or moves, including learning,
  relearning, review, and Card Types intentionally split across normal Decks.
  Changing YAML `deck` affects future generated Cards only.
- Rejects invalid sources, ambiguous identities, schema mismatches, missing media,
  filtered Cards/Decks, and conflicting Template Deck overrides before target writes.
  Does not edit Deck options, unrelated Note content, or media. Anki may generate
  Cards for unrelated Notes when a shared Front Template changes; their placement
  is left to Anki and is not changed by the updater.
- Static media references in Templates and shared styling must exist in the sandbox
  media directory. Dynamic Template media references such as `<img src="{{Field}}">`
  are rejected because their assets cannot be validated for every affected Note.
- Reopens the target to verify Fields/tags, retained identities, Card placement,
  scheduling, and review-history rows. Reports new Card IDs, Card Type names, actual
  Deck IDs/names (`new_cards`), and verified persistence
  on stdout; a second identical application reports only `unchanged` Notes.
- On failure, releases the Collection/lock and reports completed native operations.
  Earlier writes may remain committed. Obtain a fresh preview and approval before
  retrying; no whole-run rollback or restoration is attempted.
  A placement failure reports the newly generated managed Cards' actual Decks,
  not just the intended destination. Failure reports also include `generated_cards`
  for all committed managed deltas, including Notes not reached before failure
  after shared Template generation. On retry those committed Cards are existing
  Cards and will not be moved automatically, even if placement was interrupted.

This earlier `apply_yaml.py` command has only immediate run approval; use the
guarded `update_collection.py` workflow above for Collection-bound approvals and
staleness checks. Both remain sandbox-only and do not retire the CSV fallback.

For intended-client rendering checks, use only a tool-created sandbox and its
synthetic Notes: inspect the updated Front and Back in Anki Desktop, including
each changed Card Type's shared styling, then quit Desktop completely before
running preview, application, or other headless operations. API rendering tests
do not replace this visual check.

## Historical exploration: import Japanese_Mined_Vocab directly from YAML

`import_yaml.py` below is the earlier exploration command, **not** the ticket 04
application path. Its Deck creation, existing-Card moves, and retained database
snapshots are exploration behavior, not supported application behavior.

Quit Anki Desktop completely, then run from the repository root:

```bash
tools/headless_import/.venv/bin/python tools/headless_import/import_yaml.py --sandbox sandbox-2gs8b2z0
```

Substitute another tool-created sandbox folder name if needed. The command:

- Reads all six entry YAML files and the Note Type schema, both Card Types'
  Templates, and shared CSS. It never reads or generates CSV.
- Creates `Japanese_Mined_Vocab` with seven ordinary Fields. YAML `Tags` is native
  Note metadata, not an eighth Field. Existing config `fields` remains the legacy
  eight-column CSV layout; its final `Tags` column is excluded from Anki Fields.
- Imports Notes by exact Note Type plus first-Field `VocabID`. Existing matches
  are updated in place; ambiguous IDs are rejected. Tags replace the entire set;
  null, empty, or absent Tags clear it. `REPO_DELETE` does not delete anything.
- Uses each entry file's `deck` declaration, creates missing normal Decks through
  the API (including necessary hierarchy parents), and places generated Cards.
- Checks quoted IDs, duplicate source IDs/keys, required values, unknown Fields,
  schema/Template agreement, and referenced media already in the sandbox. HTML
  content is trimmed and internal CRLF/LF line breaks become `<br>`.
- Requires Desktop closed, checks package compatibility, validates the sandbox
  manifest, and locks concurrent imports. Makes a consistent SQLite backup,
  including WAL contents, under `before-import-*/collection.anki2` before backend
  access. Media is not copied because this command never modifies media; this
  database snapshot is **not** a full Collection/media recovery package.
- Closes/reopens to verify imported content, native tags, Card placement, and
  preservation of the synthetic baseline/review history. Writes `last-import.json`.

Native operations commit individually. On failure, earlier changes may already
be saved; inspect the reported progress and database backup. No automatic restore,
sync, deletion, media upload, Deck-option changes, or live Collection access occurs.
Existing Note Type structural or Template/CSS differences are rejected, not migrated.
Native moves may affect learning steps/FSRS state; do not use this sandbox experiment
as a production scheduler-preservation guarantee.

This user-approved exploration deliberately **creates** Decks, unlike the
linked-existing-Deck preview above. It does not implement Deck approvals, stale
approval detection, or production recovery guards. Repository-wide CSV retirement
remains a later workflow transition; no entry YAML or CSV artifact is changed here.

## Import other Note Types

With Anki Desktop completely closed:

```bash
tools/headless_import/.venv/bin/python tools/headless_import/import_yaml.py --sandbox sandbox-2gs8b2z0 --other-note-types
```

This imports Familiarity Vocab, Listening, Mined Grammar, and Sentence Production,
without re-importing the verified Mined Vocab Notes. Use repeatable
`--note-type Japanese_Mined_Grammar` arguments to select specific Note Types.
With no selection flag, the default remains Japanese_Mined_Vocab.

Card Type order comes from each `note-type.md`. Note Types with no entry files
still receive their Fields, Templates, and CSS; no placeholder Notes or Decks are
invented. Every present entry file must still contain at least one valid Note.
All selected sources are validated before the first import. Each Note Type gets
its own backup and `last-import-<NoteType>.json` report; imports commit separately,
so a later failure does not undo earlier successful imports. The importer verifies
that other Note Types' Notes/Cards and existing review history remain unchanged.

## Tests

```bash
tools/headless_import/.venv/bin/python -m unittest discover -s tools/headless_import -p 'test_*.py' -v
```

Tests use temporary synthetic Collections, never a user Collection.
