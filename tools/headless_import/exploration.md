# Ticket 03 exploration

Explored on 2026-11-16. Initial scope: environment preparation and synthetic API
access. Subsequently expanded by the user to direct YAML API import with missing
Deck creation in the sandbox. This is not completion of ticket 03.

## Executed evidence

- Created `tools/headless_import/.venv` with Python 3.14.4 and installed this
  tool's requirements there. All API invocations used that environment.
- Inspected Desktop 26.9.4 and installed official package 26.09.4; versions match.
- Created a fresh persistent synthetic Collection using `Collection(path)`.
  No existing Collection or normal Desktop profile registry was accessed.
- Created fixture Note Type/Decks/Notes using native APIs and recorded a native
  review-log row. Closed/reopened the fixture and verified Note GUID, Card IDs,
  tags, and complete review-log rows persisted.
- Three setup tests pass: fresh isolated fixtures, missing Desktop app rejection,
  and version mismatch rejection before creating a sandbox.
- `col.models.add_dict(model)` returns an operation result with the new ID;
  fetch the persisted schema with `col.models.get(result.id)` before creating
  Notes. It does not update the original dictionary's zero ID.
- The normal-Deck creation result provides `.id`; use the Deck manager to read
  the persisted hierarchical name rather than assuming a `.name` attribute.

The command's JSON output identifies the sandbox Collection and its manifest.
Each run makes a new sandbox; this is not Desktop profile registration, a
preview operation, or an approval of Deck links. Tests use temporary fixtures.

## Repository findings

Read entry YAML directly with PyYAML without invoking the CSV converter:

| Note Type | Entry files | Notes |
| --- | ---: | ---: |
| Japanese_Familiarity_Vocab | 0 | 0 |
| Japanese_Listening | 0 | 0 |
| Japanese_Mined_Grammar | 5 | 30 |
| Japanese_Mined_Vocab | 6 | 189 |
| Japanese_Sentence_Production | 3 | 50 |

The 269 existing entries have quoted IDs and no duplicate IDs within their
respective Note Types across files. This was an identity inventory, **not** full
required-Field/schema/media validation.

- All five entry configurations currently list `Tags` within `fields` for the
  legacy CSV column layout. Listening and Sentence Production documentation
  already distinguish native tags from ordinary Fields; the other three still
  describe tags as an ordinary Field. Ticket 03 needs one consistent contract.
- Mined Vocab's documented `Japanese::Vocabulary` target does not cover its
  `Japanese::Tadoku::<title>` entry declarations. Entry YAML must become explicitly
  authoritative; documentation can describe intended scope, not override it.
- Existing normalization is `str(value).strip()`, then CRLF to LF and LF to
  `<br>`; null becomes an empty string. Preserve this for ordinary Fields without
  importing CSV generation. Tags require separate parsing/replacement semantics.
- Existing converter validation checks that IDs parse as strings, but that does
  not enforce literal quoting for IDs that YAML already interprets as strings.
  Preview should inspect YAML scalar style as well. Consider rejecting duplicate
  YAML keys rather than accepting PyYAML's default last-value-wins behavior.
- Ticket 02 capability evidence exists, but its scripts were deliberately removed
  in commit `867c604`. The findings' suggested helper imports are unavailable.
  Do not restore the removed tool implicitly; implement the required guards in
  the future updater and retain the findings as historical evidence.

The initial exploration changed no entry YAML, generated CSV, Note Type schema,
repository agent instructions, or ticket status. The subsequent sandbox import
clarified Japanese_Mined_Vocab's schema documentation (see below); no entry YAML,
CSV artifact, repository agent instruction, or ticket status was changed.

## Subsequent direct YAML import

The user explicitly approved importing Notes directly from YAML, creating missing
Decks through the API, and treating Tags as native metadata. The longer-term goal
is CSV workflow retirement; this experiment itself reads/generates no CSV and does
not retire repository-wide rules before the guarded workflow is verified.

- Added `import_yaml.py`, restricted by its CLI to tool-created `.local/sandbox-*`
  Collections with matching manifests. Desktop must be closed.
- Clarified Japanese_Mined_Vocab's seven ordinary Fields, native tags, preserved
  legacy eighth CSV column, and authoritative entry target Decks in `note-type.md`.
  The legacy configuration and converter are unchanged.
- Executed the importer against `sandbox-2gs8b2z0`: created the Note Type, six
  requested target Decks (plus necessary parents), 189 Notes, and 378 Cards.
- Saved the pre-import database snapshot at
  `.local/sandbox-2gs8b2z0/before-import-huhndxtc/collection.anki2` within this tool.
  It includes database/WAL state, not media. No media references were present in
  the vocabulary YAML and no assets were modified.
- Reopened the Collection to verify persisted content, tags, and placement;
  preserved the two synthetic baseline Notes/Cards and complete review history.
- All nine setup/import tests pass. Temporary-Collection tests demonstrate a
  second identical import is a no-op, native-tag replacement/clearing, HTML newline
  normalization, missing-Deck creation/Card movement, retained Note/Card identity,
  duplicate source/Collection ID rejection, unknown Fields, unquoted IDs, duplicate
  YAML keys, missing media, and arbitrary target-path rejection.

This mutating sandbox experiment does **not** satisfy ticket 03's non-mutating
preview or approved-existing-Deck requirements. No production Collection was opened.

### All remaining Note Types

After the user verified imported vocabulary Notes in Desktop, the importer was
generalized to selected repository Note Types and executed with `--other-note-types`
against the same sandbox on 2026-11-16. It did not re-import Mined Vocab.

| Note Type | Ordinary Fields | Notes added | Cards added |
| --- | ---: | ---: | ---: |
| Japanese_Familiarity_Vocab | 8 | 0 | 0 |
| Japanese_Listening | 6 | 0 | 0 |
| Japanese_Mined_Grammar | 7 | 30 | 60 |
| Japanese_Sentence_Production | 4 | 50 | 50 |

All four received their documented Card Types, Front/Back Templates, and shared
CSS. Familiarity and Listening have no entry files; no example Notes were invented.
Sentence Production created its three entry-declared target Decks; Grammar reused
the existing Tadoku Decks. Each import saved a separate pre-import database snapshot
and `last-import-<NoteType>.json` report inside the sandbox.

Reopen checks verified schemas, Templates/CSS, content, tags, and placement, plus
preservation of all other Note Types' Notes/Cards and complete existing review
history. The existing vocabulary Notes were left untouched. All ten setup/import
tests pass, including a public-CLI multi-Note-Type test that preserves previously
reviewed vocabulary Cards and proves an identical second run is a no-op.

The four schemas now document only ordinary Fields in their Fields tables and
describe native tags separately; legacy config/CSV layouts remain unchanged.
Card Type order is read from each schema rather than hardcoded. No entry YAML or
CSV artifact was edited, and no CSV was read/generated by these imports.

## Recommended ticket 03 approach (not implemented)

1. Put the public preview command in this tool directory, with the same dedicated
   environment. Keep synthetic Collection creation separate from preview so
   preview cannot accidentally create target Decks.
2. Coordinate a documented native-tags metadata contract across schemas/configs
   and instructions. Retain current CSV column order and `#tags column` mapping;
   do not retire the existing regeneration/import workflow in ticket 03.
3. Validate all source files in each selected Note Type for duplicate IDs. Match
   existing Notes by actual Note Type identity plus exact first-Field ID, rejecting
   ambiguous matches. Do not use fuzzy search as identity proof.
4. Define Deck links bound to the selected Collection, with explicit approval,
   existing Deck ID, and expected hierarchical name. Exact-name candidates are
   proposals only. Validate ID/name correspondence and reject missing/filtered
   targets, conflicting overrides, and filtered source Cards.
5. Obtain a consistent disposable database/media snapshot before opening an Anki
   backend. Do not copy a potentially live `.anki2` file without accounting for
   WAL state, and do not open the source through `Collection` to inspect it.
   Snapshot acquisition needs an explicit safety contract; this sandbox setup
   does not supply it.
6. Compare declared ordered ordinary Fields/Card Types against the actual schema;
   reject unsupported differences. Check referenced media in the target snapshot,
   not merely in the repository. Do not upload media.
7. Report deterministic additions, Field changes, full tag replacements/clears
   (including `REPO_DELETE`), and proposed Card placement through the public
   command. Leave unmatched Notes alone and generate/read no CSV.
8. Exercise that command against synthetic Collections and disposable copies,
   covering every ticket rejection case and asserting the source remains
   unchanged. Existing setup tests are not acceptance coverage for ticket 03.

The current sandbox proves isolated native API access is available. It does not
prove compatibility with the user's actual schemas, Decks, or media; that remains
unverified without a separately authorized representative snapshot.

## Ticket 07 guarded workflow acceptance (2026-11-16)

The dedicated `.venv` and tool-created sandbox fixtures are the end-to-end
verification environment, not merely preliminary exploration. No personal
Collection or normal Desktop Profile registry was inspected.

Executed the [documented sandbox-only smoke procedure](README.md#executable-sandbox-only-end-to-end-smoke-procedure):

```bash
HEADLESS_SMOKE_REPORT=1 PYTHONPATH=tools/headless_import tools/headless_import/.venv/bin/python -m unittest test_update_collection.GuardedCommandTests.test_complete_workflow_smoke -v
```

- Final smoke target: isolated `sandbox-p1idp7oh`, matching tool-created manifest,
  `Preview Sandbox::Target` approved ID `1794816156145`.
- Desktop closed; package 26.09.4 matched Desktop 26.9.4; Collection schema 18.
- Full disposable rehearsal verified before token approval; the public command
  received the exact token plus Deck-link and Note Type ownership approvals.
- Retained Front/Back Templates and CSS, managed YAML Fields/tags, new Notes, and
  Template-generated managed Cards persisted after independent reopening.
- Existing identities, history, scheduling, and Deck placement were preserved;
  new managed Cards used the approved existing Deck. Referenced media was unchanged.
- Fresh rehearsal/approval followed by a second application proved a no-op.
- Isolated fixture disposed on exit; no recovery backup, media archive, automatic
  restore, or target replacement was created. Historical `before-import-*` files
  elsewhere in older exploration sandboxes are unrelated to this workflow.

`test_update_collection.py` additionally executes the existing application behavior
suite through the guarded public command and covers Collection selection, manifest
and schema version rejection, Desktop reopening, updater/native locks, stale source/
media/history approval, source changes during rehearsal, committed WAL inclusion,
source immutability, partial failure/interruption and fresh-approved retry.
Review regression tests additionally reject scheduling changes at native lock
acquisition and missing media referenced by inline CSS in YAML Fields.
Source hash/parse interleaving also has a public-command regression: parsing uses
the exact captured approved bytes rather than rereading a concurrently edited Template.
Desktop UI rendering and personal/live Collection smoke testing are not gates here.

## Sources

- [Official command-line/headless use](https://github.com/ankitects/anki/blob/26.09.4/docs-site/addons/command-line-use.mdx)
- [Desktop ProfileManager](https://github.com/ankitects/anki/blob/26.09.4/qt/aqt/profiles.py): profiles are a Desktop concern, distinct from headless Collections.
- [Ticket 03](../../.scratch/anki-headless-import/issues/03-yaml-preview-and-deck-links.md)
- [Ticket 02 executed findings](../../.scratch/anki-headless-import/verification-findings.md)
- [Feature spec](../../.scratch/anki-headless-import/spec.md)

Context7 was consulted for official Anki documentation; pinned upstream source
and the installed matching package were checked for the APIs used here.
