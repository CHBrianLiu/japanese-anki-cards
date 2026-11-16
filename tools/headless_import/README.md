# Headless import exploration

Sandbox preparation, non-mutating YAML preview, and direct YAML API import
exploration. Commands cannot target a normal user Collection; preview and import
accept only a tool-created sandbox folder name. Preview does not apply changes.

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
  Candidate Decks are **not** approved links or a finalized configuration format.

The command closes and reopens only its own fresh Collection to verify baseline
persistence. It never reads/generates CSV, imports repository Notes, copies the
user's Collection, or syncs. Fresh Deck creation here is fixture setup only;
ticket 03 preview must reject missing target Decks instead of creating them.

## Preview YAML against existing sandbox Decks

Quit Anki Desktop completely. Select a tool-created sandbox and one or more
repository Note Types. First propose exact-name matches; the output is not approval:

```bash
tools/headless_import/.venv/bin/python tools/headless_import/preview.py --sandbox sandbox-2gs8b2z0 --note-type Japanese_Mined_Vocab --propose-decks
```

Create a JSON file of explicitly approved links for **every** requested `deck`.
Use the selected sandbox's absolute `collection.anki2` path from its manifest;
copy each target ID and exact hierarchical name from the proposals or another
verified existing normal Deck. For example (IDs below are illustrative):

```json
{
  "collection": "/absolute/path/to/sandbox-2gs8b2z0/collection.anki2",
  "links": [
    {"requested": "Japanese::Vocabulary", "name": "Japanese::Vocabulary", "id": 123456, "approved": true}
  ]
}
```

Run the preview with `--deck-links /path/to/links.json` in place of
`--propose-decks`. Repeat `--note-type` for more Note Types. Approved targets can
have different names from the requested names; each ID and name must match the
selected Collection. Missing, ambiguous, filtered, or unapproved links fail.

The JSON report lists add/update/unchanged Notes, Field changes and tag additions
and removals. New managed Cards include their requested and resolved Deck; existing
Card placement is ignored. The command uses a temporary SQLite backup API copy,
including committed WAL contents, opens Anki only on the copy, validates media
in the sandbox, and removes the copy on exit. It neither writes CSV nor applies
changes, creates Decks, uploads media, or retains backups. Creating fixture Decks
and media is a separate sandbox setup step. The selected Collection is independent
of YAML's `deck`; Desktop Profiles are not inspected.

## Import Japanese_Mined_Vocab directly from YAML

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
