#!/usr/bin/env python3
"""Apply YAML Notes to an explicitly approved tool-created sandbox Collection."""

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

from create_sandbox import prerequisites
from import_yaml import sandbox_access
from preview import copy_database, execute_plan, load_selection, plan_notes, resolve_decks, validate_media


def retained_state(col, managed_ids):
    """Read-only evidence for retained identities, scheduling and unrelated data."""
    return {
        "identities": col.db.all("select id, guid, mid from notes order by id"),
        "unrelated_notes": [row for row in col.db.all("select * from notes order by id")
                            if row[0] not in managed_ids],
        # Native content updates may change mod/usn, but no scheduling columns.
        "cards": col.db.all("select id, nid, did, ord, type, queue, due, ivl, factor, "
                            "reps, lapses, left, odue, odid, flags, data from cards order by id"),
        "revlog": col.db.all("select * from revlog order by id"),
        "decks": sorted(col.decks.all(), key=lambda deck: deck["id"]),
        "models": sorted(col.models.all(), key=lambda model: model["id"]),
    }


def verify(col, plan, before, report):
    managed = {operation["note"].id for operation in plan}
    after = retained_state(col, managed)
    for key in ("unrelated_notes", "revlog", "decks", "models"):
        if before[key] != after[key]:
            raise ValueError(f"Preservation verification failed: {key}")
    for key in ("identities", "cards"):
        actual = {row[0]: row for row in after[key]}
        if any(actual.get(row[0]) != row for row in before[key]):
            raise ValueError(f"Retained {key} changed")
    for operation, item in zip(plan, report):
        note = col.get_note(operation["note"].id)
        entry = operation["entry"]
        if (note.fields != entry["fields"]
                or {tag.casefold() for tag in note.tags} != {tag.casefold() for tag in entry["tags"]}):
            raise ValueError(f"Persisted Fields/tags differ: {item['note_type']}, {entry['id']}")
        for cid in set(col.card_ids_of_note(note.id)) - operation["old_cards"]:
            if col.get_card(cid).did != operation["target"]["id"]:
                raise ValueError(f"New Card placement differs: {item['note_type']}, {entry['id']}")


def apply(collection, sources, requested, report):
    from anki.collection import Collection

    # Rehearse on a disposable WAL-consistent copy before opening the target.
    with tempfile.TemporaryDirectory(prefix="anki-rehearsal-") as temp:
        copy = Path(temp) / "collection.anki2"
        copy_database(collection, copy)
        media = Path(temp) / "collection.media"
        media.mkdir()
        for name in sorted({name for source in sources for name in source["media"]}):
            shutil.copyfile(collection.parent / "collection.media" / name, media / name)
        col = Collection(str(copy))
        try:
            decks = resolve_decks(col, requested)
            rehearsal_plan = plan_notes(col, sources, decks, existing_only=True)
            rehearsal_before = retained_state(col, {operation["note"].id for operation in rehearsal_plan
                                                    if operation["item"]["action"] != "add"})
            rehearsal = []
            execute_plan(col, rehearsal_plan, rehearsal)
        finally:
            col.close()
        col = Collection(str(copy))
        try:
            verify(col, rehearsal_plan, rehearsal_before, rehearsal)
        finally:
            col.close()

    col = Collection(str(collection))
    try:
        decks = resolve_decks(col, requested)
        plan = plan_notes(col, sources, decks, existing_only=True)
        # Ignore rehearsal-only Card effects when comparing the non-mutating plan.
        expected = [{key: value for key, value in item.items() if key != "new_cards_deck"}
                    for item in rehearsal]
        if [operation["item"] for operation in plan] != expected:
            raise ValueError("Collection changed during rehearsal; fresh preview required")
        before = retained_state(col, {operation["note"].id for operation in plan
                                      if operation["item"]["action"] != "add"})
        execute_plan(col, plan, report["notes"], committed=True)
    finally:
        col.close()
    col = Collection(str(collection))
    try:
        verify(col, plan, before, report["notes"])
        report["persistence_verified"] = True
    finally:
        col.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sandbox", required=True, help="Tool-created sandbox name, never a Collection path")
    parser.add_argument("--note-type", action="append", required=True, help="Repository Note Type; repeat to select")
    parser.add_argument("--anki-app", type=Path, default=Path("/Applications/Anki.app"))
    parser.add_argument("--approve", action="store_true", help="Approve applying this selection after reviewing preview")
    args = parser.parse_args()
    report = {"notes": [], "persistence_verified": False}
    tool = Path(__file__).resolve().parent
    try:
        if not args.approve:
            raise ValueError("Review preview, then supply --approve to apply")
        prerequisites(args.anki_app)
        sources = load_selection(tool, args.note_type)
        requested = {entry["deck"] for source in sources for entry in source["entries"]}
        with sandbox_access(tool / ".local", args.sandbox) as (collection, _manifest):
            validate_media(collection, sources)
            apply(collection, sources, requested, report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
    except (Exception, KeyboardInterrupt) as exc:
        sys.exit(f"Application stopped: {exc}. Native operations may already be committed; "
                 f"committed progress: {json.dumps(report, ensure_ascii=False)}. "
                 "Obtain a fresh preview and approval before retrying. No rollback or restoration attempted.")


if __name__ == "__main__":
    main()
