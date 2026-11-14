# Ticket 02: verified headless Collection-update findings

- **Ticket:** `.scratch/anki-headless-import/issues/02-headless-api-verification.md`
- **Implemented as:** commit `0bfa9c6`, branch `anki-headless/02-api-verification`
- **Verified on:** 2026-11-13 and re-verified 2026-11-14
- **Environment:** macOS arm64, Python 3.14.4, Anki Desktop 26.9.4, `anki` Python package 26.09.4, Anki Desktop closed
- **Status:** Verified capability evidence. The standalone command remains at `tools/verify_headless_api.py`; later-ticket tools import its helpers (`card_state`, `prerequisites`). See "Script capture checklist" for how this file maps to what the script proves.

This file records the *observed*, executed behavior of Anki's official headless
Python API on disposable Collections. [`research/anki-headless-import.md`](../../../research/anki-headless-import.md)
records the earlier *proposed* design and upstream-source reading; this document
is the empirical evidence that followed.

## How to run the verification

Use an existing repository virtual environment with the official `anki` package
matching the installed Desktop version. The original verification used an
isolated `--target` dependency directory on `PYTHONPATH` with the existing
repository `.venv`; the Python package version is reported by the command.
Do not point any other Collection command at a live Collection to substitute
for this check.

```bash
PYTHONPATH=.venv/anki-test-deps .venv/bin/python tools/verify_headless_api.py
PYTHONPATH=.venv/anki-test-deps .venv/bin/python -m unittest tools.test_headless_verification -v
```

The `PYTHONPATH` value above is the local verification environment, not a
repository prerequisite. If it is unavailable, prepare a matching package in
an existing repository virtual environment before running the commands. Do not
install packages system-wide or use an incompatible package. On macOS,
`--anki-app /path/to/Anki.app` selects the app for version inspection only.

## How the API works (as exercised)

Anki's official Python package talks to the same Rust backend the Desktop app
uses, without importing the GUI. Open a Collection with
`anki.collection.Collection(path)` and release it with `col.close()`.

| Operation | Call used | Observed behavior |
| --- | --- | --- |
| Open Collection | `Collection(str(path))` | Creates the file if absent; opening an older Collection can migrate its schema |
| Close / release | `col.close()` | Releases the backend and database lock; must run even on failure |
| Create normal Deck | `col.decks.add_normal_deck_with_name(name)` | Returns a Deck object; `.id` is the Collection-local Deck ID |
| Create Deck config | `col.decks.add_config(name)`, mutate `config["new"]["delays"]`, `col.decks.update_config(config)`, `col.decks.set_config_id_for_deck_dict(deck, config["id"])` | Sets per-Deck learning steps; used to prove move side effects |
| Create Note Type | `col.models.new(name)`, `col.models.new_field`/`add_field`, `col.models.new_template`/`add_template`, `col.models.add_dict(model)` | Returns the created model; note new/added fields and templates |
| Read Note Type | `col.models.get(model_id)` | Returns the current schema, including `tmpls` and `css` |
| Update Templates + CSS | Mutate `template["qfmt"]`/`["afmt"]` and `model["css"]`, then `col.models.update_dict(model)` | Persists retained templates/styles without changing template names or ordinals |
| Add Note | `col.new_note(model)`, set fields, `col.add_note(note, deck_id)` | Anki generates the internal Note ID/GUID and any Cards |
| Read Note | `col.get_note(note_id)` | Returns identity (`id`, `guid`), fields, and tags |
| Update Note | Mutate fields on the fetched Note, `col.update_note(note)` | Updates in place; retains Note ID/GUID; can generate missing Cards |
| Find a Note's Cards | `col.card_ids_of_note(note_id)` | Returns the Note's Card IDs, including newly generated Cards |
| Move Cards | `col.set_deck(card_ids, deck_id)` | Moves existing Cards in place, retaining Card identity and review history |
| Read a Card | `col.get_card(card_id)` | Card fields: `id`, `did` (deck), `type`, `queue`, `due`, `ivl`, `left` (remaining learning steps), `reps`, `memory_state`, `desired_retention`, `decay` |
| Review history (read-only) | `col.db.all("select * from revlog order by id")` | Full native review-log rows; compare the whole set, not just a count |
| Read raw rows/counts | `col.db.all(...)`, `col.db.scalar("select count(*) from notetypes")` | Used for idempotency row/object comparisons |
| Simulate a review | `card.start_timer()`, `col.sched.answerCard(card, ease)` | Produces real review history and scheduling state |
| Enable FSRS | `col.set_config("fsrs", True)` | Switches the Collection to FSRS for the run |
| Lock failure | A second `Collection(str(path))` | Raises `anki.errors.DBError` mentioning the lock |

## Verification procedure

The command:

1. Resolves the installed Desktop version from
   `/Applications/Anki.app/Contents/Info.plist` (`CFBundleShortVersionString`)
   and the installed `anki` package version via `importlib.metadata.version("anki")`,
   and **stops before any backend access** if the app is missing, the package is
   missing, or the versions are incompatible.
2. Creates a brand-new synthetic Collection in a temporary directory. The command
   takes **no Collection path argument**, so it cannot open or mutate a live
   Collection. The temporary directory is removed on exit.
3. Builds a Note Type with two Card Types — `Primary` and `Conditional`, whose
   Front is `{{#Extra}}{{Extra}}{{/Extra}}` — plus a source Deck, a destination
   Deck, and a destination Deck config with longer learning steps.
4. Adds Notes and simulates native reviews so the Collection has a review Card,
   a learning Card, and an existing destination review Card.
5. Uses native operations to update the Note, update the retained Front/Back
   Templates and CSS, and move Cards to the destination Deck.
6. Closes and reopens the Collection and asserts persistence.
7. Runs a second identical reconciliation and asserts it is a no-op.
8. Tests lock failure and connection cleanup after both success and failure.

The output is a JSON report; a failure prints `Verification stopped: ...` to
stderr and exits nonzero. The unittest suite checks the happy path, missing
Desktop app, incompatible Desktop version, and missing Python package.

## Version compatibility rules

- The Desktop version (`CFBundleShortVersionString`, e.g. `26.9.4`) and the
  package version (e.g. `26.09.4`) are compared for **equality**.
- With `packaging` available, `packaging.version.Version` is used; the two above
  strings compare equal despite zero-padding.
- Without `packaging`, a fallback compares numeric dot components as tuples
  (the components of `26.9.4` and `26.09.4` compare equal after `int`), so
  zero-padding is still tolerated.
- A missing app, a missing package, or a mismatch each produces an actionable
  prerequisite message and aborts before any backend access.
- Desktop version is only inspectable from the macOS `Info.plist`; on other
  platforms the check stops until a platform-specific implementation exists.

## Observed evidence (2026-11-13; re-confirmed 2026-11-14)

Report fields: `persistence_verified`, `review_history_rows`, `new_cards`,
`second_run_mutations`, `lock_failure_verified`, `connections_released`,
`learning_move`, `fsrs_move`, `destination_side_effect`, `warning`,
`desktop_version`, `package_version`.

- **Persistence:** after close and reopen, Note content, retained template
  `qfmt`/`afmt` and CSS, and Card placement all persisted.
- **Identity:** Note ID and GUID, Card IDs, and template names/ordinals were
  retained across the update and reopen.
- **Review history:** all 3 `revlog` rows remained equal to the baseline after
  the update, after reopen, after the no-op, and after cleanup.
- **Ordinary scheduling:** the review Card kept the same `due` and `ivl`.
- **Conditional Card generation:** updating the Note generated 1 new Card from
  the conditional Card Type; existing Cards were retained.
- **Learning-move effect:** the learning Card's remaining steps changed (`1` → `2`)
  because the destination Deck config has different learning steps.
- **FSRS-move effect:** after enabling FSRS and moving, the review Card gained
  `memory_state` (stability/difficulty); an existing destination Deck Card, which
  had no memory state before, also gained one. Review history and the ordinary
  review Card's due date/interval were unaffected.
- **Idempotency:** the second identical reconciliation returned no changes;
  `notes`, `cards`, `revlog` rows, `notetypes` count, and `decks` count were
  identical before and after. No-op Deck placement did not call `set_deck`.
- **Lock failure:** a second `Collection` open raised `DBError` mentioning the
  lock and the verification stopped safely.
- **Connection cleanup:** the Collection reopened cleanly after success, after
  the no-op, and after a synthetic in-backend failure. The script calls
  `col.close()` in `finally` blocks.
- **Atomicity warning:** native operations save individually; a multi-operation
  run is **not** atomic. FSRS moves may recompute memory state for other Cards
  already in the destination Deck.

**Not claimed:** byte-for-byte equality of all scheduler properties. Remaining
learning steps and FSRS memory data legitimately change on a move; due dates and
intervals for ordinary review Cards were preserved.

## Guardrails and limits

- The verification command takes no Collection path; it creates and removes its
  own synthetic temporary Collection. It is not an updater.
- Prerequisite failures occur before backend access.
- The command does **not** itself enforce that Anki Desktop is closed; a guarded
  application workflow must enforce that.
- This proof does not authorize live Collection access or establish a backup,
  target approval, or whole-run rollback procedure.

## Script capture checklist

The reusable API calls, guards, fixture behavior, and assertions in
`tools/verify_headless_api.py` and `tools/test_headless_verification.py` are
recorded above:

- [x] API calls and exercised behavior
- [x] Prerequisite/version-compatibility checks
- [x] Disposable-only fixture and temporary-directory lifecycle
- [x] Conditional Card generation and learning-step/FSRS side effects
- [x] Persistence, identity, review-history, and scheduling assertions
- [x] Second-run idempotency and no-op Deck placement
- [x] Lock-failure and connection-release checks
- [x] Non-atomicity warning and verified environment

Literal fixture strings (HTML/CSS, Note content) are test data, not a spec
contract. The script and its tests remain in place; later-ticket tools import
`card_state` and `prerequisites` from the script.
