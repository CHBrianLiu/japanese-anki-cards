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
from preview import (copy_database, execute_selection, load_selection, resolve_decks,
                     selection_plan, validate_media)


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


def verify(col, plan, before, report, sources):
    managed = {operation["note"].id for operation in plan}
    after = retained_state(col, managed)
    for key in ("unrelated_notes", "revlog", "decks"):
        if before[key] != after[key]:
            raise ValueError(f"Preservation verification failed: {key}")
    names = {source["name"] for source in sources}
    if [model for model in before["models"] if model["name"] not in names] != [model for model in after["models"] if model["name"] not in names]:
        raise ValueError("Preservation verification failed: unrelated Note Types")
    for source in sources:
        model = col.models.by_name(source["name"])
        if (not model or model["css"] != source["css"]
                or model["type"] != 0
                or [field["name"] for field in model["flds"]] != source["fields"]
                or [{key: template[key] for key in ("name", "qfmt", "afmt")} for template in model["tmpls"]] != source["templates"]):
            raise ValueError(f"Persisted Note Type differs: {source['name']}")
        old = next((item for item in before["models"] if item["name"] == source["name"]), None)
        if old:
            ignored = {"css", "tmpls", "mod", "usn", "req"}
            if ({key: value for key, value in old.items() if key not in ignored}
                    != {key: value for key, value in model.items() if key not in ignored}):
                raise ValueError(f"Retained Note Type metadata changed: {source['name']}")
            for previous, current in zip(old["tmpls"], model["tmpls"]):
                if ({key: value for key, value in previous.items() if key not in {"qfmt", "afmt"}}
                        != {key: value for key, value in current.items() if key not in {"qfmt", "afmt"}}):
                    raise ValueError(f"Retained Card Type metadata changed: {source['name']}")
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


def prepare(col, sources, decks, report, approve_note_types, committed=False, expected=None):
    selection = selection_plan(col, sources, decks)
    type_plan, initial_notes, managed_ids, _cards = selection
    if not approve_note_types and any(item["action"] != "unchanged" for item in type_plan):
        raise ValueError("Review shared Note Type ownership and effects, then supply --approve-note-types")
    signature = (type_plan, [operation["item"] for operation in initial_notes])
    if expected is not None and signature != expected:
        raise ValueError("Collection changed during rehearsal; fresh preview required")
    before = retained_state(col, managed_ids)
    plan = execute_selection(col, sources, decks, selection, report, committed=committed)
    return signature, plan, before


def apply(collection, sources, requested, report, approve_note_types):
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
            rehearsal = {"note_types": [], "notes": []}
            signature, rehearsal_plan, rehearsal_before = prepare(col, sources, decks, rehearsal, approve_note_types)
        finally:
            col.close()
        col = Collection(str(copy))
        try:
            verify(col, rehearsal_plan, rehearsal_before, rehearsal["notes"], sources)
        finally:
            col.close()

    col = Collection(str(collection))
    try:
        decks = resolve_decks(col, requested)
        _, plan, before = prepare(col, sources, decks, report, approve_note_types, committed=True, expected=signature)
    finally:
        col.close()
    col = Collection(str(collection))
    try:
        verify(col, plan, before, report["notes"], sources)
        report["persistence_verified"] = True
    finally:
        col.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sandbox", required=True, help="Tool-created sandbox name, never a Collection path")
    parser.add_argument("--note-type", action="append", required=True, help="Repository Note Type; repeat to select")
    parser.add_argument("--anki-app", type=Path, default=Path("/Applications/Anki.app"))
    parser.add_argument("--approve", action="store_true", help="Approve applying this selection after reviewing preview")
    parser.add_argument("--approve-note-types", action="store_true", help="Approve shared Note Type ownership and effects")
    args = parser.parse_args()
    report = {"note_types": [], "notes": [], "persistence_verified": False}
    tool = Path(__file__).resolve().parent
    try:
        if not args.approve:
            raise ValueError("Review preview, then supply --approve to apply")
        prerequisites(args.anki_app)
        sources = load_selection(tool, args.note_type)
        requested = {entry["deck"] for source in sources for entry in source["entries"]}
        with sandbox_access(tool / ".local", args.sandbox) as (collection, _manifest):
            validate_media(collection, sources)
            apply(collection, sources, requested, report, args.approve_note_types)
        print(json.dumps(report, indent=2, ensure_ascii=False))
    except (Exception, KeyboardInterrupt) as exc:
        sys.exit(f"Application stopped: {exc}. Native operations may already be committed; "
                 f"committed progress: {json.dumps(report, ensure_ascii=False)}. "
                 "Obtain a fresh preview and approval before retrying. No rollback or restoration attempted.")


if __name__ == "__main__":
    main()
