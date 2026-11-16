#!/usr/bin/env python3
"""Preview YAML changes against a disposable copy of a tool-created sandbox."""

import argparse
import json
import shutil
import sqlite3
import sys
import tempfile
import unicodedata
from pathlib import Path

from create_sandbox import prerequisites
from import_yaml import load_source, sandbox_access


def load_selection(tool, names):
    names = sorted(set(names))
    if any(not name or Path(name).name != name or name in (".", "..") for name in names):
        raise ValueError("Note Type must be a directory name")
    return [load_source(tool.parents[1] / "note-types" / name) for name in names]


def validate_media(collection, sources):
    media_dir = collection.parent / "collection.media"
    if media_dir.is_symlink():
        raise ValueError("Sandbox media directory must not be a symlink")
    for source in sources:
        for name in sorted(source["media"]):
            media = media_dir / name
            if Path(name).name != name or media.is_symlink() or not media.is_file():
                raise ValueError(f"Missing or unsupported target media reference: {name}")
    return media_dir


def copy_database(source_path, destination_path):
    def progress(status, remaining, total):
        if status in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
            raise ValueError("Collection is locked; preview stopped")

    source = sqlite3.connect(source_path.as_uri() + "?mode=ro", uri=True, timeout=0)
    try:
        destination = sqlite3.connect(destination_path)
        try:
            source.backup(destination, progress=progress)
        finally:
            destination.close()
    finally:
        source.close()


def resolve_decks(col, requested, proposals=False):
    decks = col.decks.all()
    if proposals:
        return [{"requested": name, "candidates": [
            {"id": deck["id"], "name": deck["name"]}
            for deck in decks if deck["name"] == name and not deck["dyn"]
        ]} for name in sorted(requested)]
    resolved = {}
    for name in sorted(requested):
        matches = [deck for deck in decks if deck["name"] == name]
        if len(matches) != 1 or matches[0]["dyn"]:
            raise ValueError(f"Missing, ambiguous or filtered Deck target: {name}")
        resolved[name] = {"requested": name, "resolved": matches[0]["name"], "id": matches[0]["id"]}
    return resolved


def model_for_source(col, source, existing_only=False):
    model = col.models.by_name(source["name"])
    if model:
        if (model["name"] != source["name"] or model["type"] != 0
                or [field["name"] for field in model["flds"]] != source["fields"]
                or [template["name"] for template in model["tmpls"]] != [t["name"] for t in source["templates"]]):
            raise ValueError(f"Unsupported Note Type schema mismatch: {source['name']}")
        return model
    if existing_only:
        raise ValueError(f"Missing compatible existing Note Type: {source['name']}")
    model = col.models.new(source["name"])
    for name in source["fields"]:
        col.models.add_field(model, col.models.new_field(name))
    for template in source["templates"]:
        native = col.models.new_template(template["name"])
        native.update(template)
        col.models.add_template(model, native)
    model["css"] = source["css"]
    return col.models.get(col.models.add_dict(model).id)


def native_field_text(col, value):
    return unicodedata.normalize("NFC", value) if col.conf.get("normalize_note_text", True) else value


def normalized_entries(col, source):
    entries = []
    seen = set()
    for entry in source["entries"]:
        fields = [native_field_text(col, value) for value in entry["fields"]]
        if fields[0] in seen:
            raise ValueError(f"Duplicate stable ID after native normalization in {source['name']}: {fields[0]}")
        seen.add(fields[0])
        # Native tag storage always uses NFC, independent of the Field setting.
        tags = [unicodedata.normalize("NFC", tag) for tag in entry["tags"]]
        entries.append({**entry, "fields": fields, "tags": tags})
    return entries


def plan_notes(col, sources, resolved_decks, existing_only=False):
    plan = []
    for source in sorted(sources, key=lambda source: source["name"]):
        model = model_for_source(col, source, existing_only)
        matches = {}
        entries = normalized_entries(col, source)
        wanted = {entry["fields"][0] for entry in entries}
        for nid in col.models.nids(model["id"]):
            note = col.get_note(nid)
            matching_id = native_field_text(col, note.fields[0])
            if matching_id in wanted:
                if matching_id in matches:
                    raise ValueError(f"Ambiguous existing stable ID in {source['name']}: {note.fields[0]}")
                matches[matching_id] = nid
        for entry in sorted(entries, key=lambda entry: entry["id"]):
            target = resolved_decks[entry["deck"]]
            nid = matches.get(entry["fields"][0])
            note = col.get_note(nid) if nid else col.new_note(model)
            old_cards = set(col.card_ids_of_note(nid)) if nid else set()
            for cid in old_cards:
                card = col.get_card(cid)
                deck = col.decks.get(card.did)
                if card.odid or not deck or deck["dyn"]:
                    raise ValueError(f"Filtered source Card: {source['name']}, {entry['id']}")
            changes = {name: {"before": old, "after": new}
                       for name, old, new in zip(source["fields"], note.fields, entry["fields"]) if old != new}
            old_tags = {tag.casefold(): tag for tag in note.tags}
            new_tags = {tag.casefold(): tag for tag in entry["tags"]}
            added = sorted((new_tags[key] for key in new_tags.keys() - old_tags.keys()), key=str.casefold)
            removed = sorted((old_tags[key] for key in old_tags.keys() - new_tags.keys()), key=str.casefold)
            action = "add" if not nid else "update" if changes or added or removed else "unchanged"
            item = {"note_type": source["name"], "id": entry["id"], "action": action,
                    "fields": changes, "tags_added": added, "tags_removed": removed}
            plan.append({"item": item, "entry": entry, "note": note,
                         "model": model, "target": target, "old_cards": old_cards})
    return plan


def execute_plan(col, plan, report, committed=False):
    for operation in plan:
        item = dict(operation["item"])
        note, entry = operation["note"], operation["entry"]
        target, model = operation["target"], operation["model"]
        if item["action"] != "unchanged":
            note.fields = entry["fields"][:]
            note.tags = entry["tags"][:]
            if item["action"] == "update":
                col.update_note(note)
            else:
                col.add_note(note, target["id"])
            # Record the committed Note operation before any placement can fail.
            report.append(item)
            if committed:
                item["note_id"] = note.id
            new_cards = set(col.card_ids_of_note(note.id)) - operation["old_cards"]
            for cid in new_cards:
                template = model["tmpls"][col.get_card(cid).ord]
                if template.get("did") and template["did"] != target["id"]:
                    raise ValueError(f"Conflicting Template Deck override: {item['note_type']}, {entry['id']}")
            if new_cards:
                item["new_cards_deck"] = target
                misplaced = [cid for cid in new_cards if col.get_card(cid).did != target["id"]]
                if misplaced:
                    col.set_deck(misplaced, target["id"])
                if committed:
                    item["new_card_ids"] = sorted(new_cards)
        else:
            report.append(item)
        if committed:
            item["note_id"] = note.id


def preview_notes(col, sources, resolved_decks, existing_only=False):
    report = []
    execute_plan(col, plan_notes(col, sources, resolved_decks, existing_only), report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sandbox", required=True, help="Tool-created sandbox name, not a Collection path")
    parser.add_argument("--note-type", action="append", required=True, help="Repository Note Type name; repeat to select")
    parser.add_argument("--anki-app", type=Path, default=Path("/Applications/Anki.app"))
    parser.add_argument("--propose-decks", action="store_true", help="Propose exact-name candidates without approving them")
    args = parser.parse_args()
    tool = Path(__file__).resolve().parent
    try:
        prerequisites(args.anki_app)
        sources = load_selection(tool, args.note_type)
        requested = {entry["deck"] for source in sources for entry in source["entries"]}
        with sandbox_access(tool / ".local", args.sandbox) as (collection, _manifest):
            media_dir = validate_media(collection, sources)
            with tempfile.TemporaryDirectory(prefix="anki-preview-") as temp:
                copy = Path(temp) / "collection.anki2"
                copy_database(collection, copy)
                referenced_media = {name for source in sources for name in source["media"]}
                if referenced_media:
                    copy_media = Path(temp) / "collection.media"
                    copy_media.mkdir()
                    for name in sorted(referenced_media):
                        shutil.copyfile(media_dir / name, copy_media / name)
                from anki.collection import Collection
                col = Collection(str(copy))
                try:
                    resolved_decks = resolve_decks(col, requested, args.propose_decks)
                    result = {"proposals": resolved_decks} if args.propose_decks else {"notes": preview_notes(col, sources, resolved_decks)}
                finally:
                    col.close()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as exc:
        sys.exit(f"Preview stopped: {exc}")


if __name__ == "__main__":
    main()
