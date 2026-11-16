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


def selection_names(names):
    names = sorted(set(names))
    if any(not name or Path(name).name != name or name in (".", "..") for name in names):
        raise ValueError("Note Type must be a directory name")
    return names


def load_selection(tool, names, captured=None):
    return [load_source(tool.parents[1] / "note-types" / name, captured) for name in selection_names(names)]


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


def validate_model(model, source):
    if (model["name"] != source["name"] or model["type"] != 0
            or [field["name"] for field in model["flds"]] != source["fields"]
            or [template["name"] for template in model["tmpls"]] != [t["name"] for t in source["templates"]]):
        raise ValueError(f"Unsupported Note Type schema mismatch: {source['name']}")


def model_for_source(col, source, existing_only=False):
    model = col.models.by_name(source["name"])
    if model:
        validate_model(model, source)
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


def plan_note_types(col, sources):
    plan = []
    for source in sorted(sources, key=lambda source: source["name"]):
        model = col.models.by_name(source["name"])
        if model:
            validate_model(model, source)
            changes = [{"name": template["name"], "front_changed": template["qfmt"] != desired["qfmt"],
                        "back_changed": template["afmt"] != desired["afmt"]}
                       for template, desired in zip(model["tmpls"], source["templates"])
                       if template["qfmt"] != desired["qfmt"] or template["afmt"] != desired["afmt"]]
            css_changed = model["css"] != source["css"]
            action = "update" if changes or css_changed else "unchanged"
            count = len(col.models.nids(model["id"]))
        else:
            changes = [{"name": template["name"], "front_changed": True, "back_changed": True}
                       for template in source["templates"]]
            css_changed, action, count = True, "create", 0
        plan.append({"note_type": source["name"], "action": action,
                     "templates_changed": [change["name"] for change in changes], "template_changes": changes,
                     "styling_changed": css_changed, "existing_notes_affected": count})
    return plan


def execute_note_types(col, sources, plan, report):
    for source, item in zip(sorted(sources, key=lambda source: source["name"]), plan):
        if item["action"] == "create":
            model_for_source(col, source)
        elif item["action"] == "update":
            model = col.models.by_name(source["name"])
            for native, desired in zip(model["tmpls"], source["templates"]):
                native["qfmt"], native["afmt"] = desired["qfmt"], desired["afmt"]
            model["css"] = source["css"]
            col.models.update_dict(model)
        report.append(dict(item))


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
                deck = col.decks.get(card.did, default=False)
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


def card_placement_evidence(col, model, card_ids):
    result = []
    for cid in sorted(card_ids):
        card = col.get_card(cid)
        deck = col.decks.get(card.did, default=False)
        result.append({"id": cid, "card_type": model["tmpls"][card.ord]["name"],
                       "deck": {"id": card.did, "name": deck["name"] if deck else None}})
    return result


def place_new_managed_cards(col, operation, item, committed=False):
    """Place only the delta from IDs captured before Note/Template updates.

    The caller supplies one managed Note; shared Template effects on other Notes
    are deliberately outside this boundary. Record actual placement even when a
    native move fails, so committed-progress reports describe recoverable facts.
    """
    note, target = operation["note"], operation["target"]
    model = operation["model"]
    new_cards = sorted(set(col.card_ids_of_note(note.id)) - operation["old_cards"])
    if not new_cards:
        return

    if committed:
        item["new_card_ids"] = new_cards
        item["new_cards"] = card_placement_evidence(col, model, new_cards)
    for cid in new_cards:
        card = col.get_card(cid)
        deck = col.decks.get(card.did, default=False)
        if card.odid or not deck or deck["dyn"]:
            raise ValueError(f"Filtered newly generated Card: {item['note_type']}, {item['id']}")
        template = model["tmpls"][card.ord]
        if template.get("did") and template["did"] != target["id"]:
            raise ValueError(f"Conflicting Template Deck override: {item['note_type']}, {item['id']}")
    item["new_cards_deck"] = target
    misplaced = [cid for cid in new_cards if col.get_card(cid).did != target["id"]]
    try:
        if misplaced:
            col.set_deck(misplaced, target["id"])
    finally:
        if committed:
            item["new_cards"] = card_placement_evidence(col, model, new_cards)


def execute_plan(col, plan, report, committed=False):
    for operation in plan:
        item = dict(operation["item"])
        note, entry = operation["note"], operation["entry"]
        target = operation["target"]
        if item["action"] != "unchanged":
            note.fields = entry["fields"][:]
            note.tags = entry["tags"][:]
            if item["action"] == "update":
                col.update_note(note)
            else:
                col.add_note(note, target["id"])
            # Record the committed Note operation before any placement can fail.
            report.append(item)
        else:
            report.append(item)
        if committed:
            item["note_id"] = note.id
        place_new_managed_cards(col, operation, item, committed)


def selection_plan(col, sources, decks):
    types = plan_note_types(col, sources)
    existing = [source for source in sources if col.models.by_name(source["name"])]
    notes = plan_notes(col, existing, decks, existing_only=True)
    managed = {operation["note"].id for operation in notes if operation["item"]["action"] != "add"}
    cards = {nid: set(col.card_ids_of_note(nid)) for source in existing
             for nid in col.models.nids(col.models.by_name(source["name"])["id"])}
    for item in types:
        model = col.models.by_name(item["note_type"])
        nids = set(col.models.nids(model["id"])) if model else set()
        item["existing_managed_notes"] = len(nids & managed)
        item["existing_unrelated_notes"] = len(nids - managed)
    return types, notes, managed, cards


def execute_selection(col, sources, decks, selection, report, committed=False):
    types, plan, managed, cards = selection
    try:
        execute_note_types(col, sources, types, report["note_types"])
        for item in report["note_types"]:
            model = col.models.by_name(item["note_type"])
            new_managed = new_unrelated = 0
            for nid in col.models.nids(model["id"]):
                new = set(col.card_ids_of_note(nid)) - cards.get(nid, set())
                if nid in managed:
                    new_managed += len(new)
                else:
                    new_unrelated += len(new)
            item["managed_new_cards"] = new_managed
            item["unrelated_new_cards"] = new_unrelated
        plan = plan_notes(col, sources, decks, existing_only=True)
        for operation in plan:
            if operation["note"].id:
                operation["old_cards"] = cards.get(operation["note"].id, set())
        execute_plan(col, plan, report["notes"], committed)
        return plan
    except (Exception, KeyboardInterrupt):
        if committed:
            # Template generation precedes per-Note operations. Even Notes not
            # reached before failure may already have committed managed Cards.
            report["generated_cards"] = []
            for operation in plan:
                nid = operation["note"].id
                new = set(col.card_ids_of_note(nid)) - operation["old_cards"] if nid else set()
                if new:
                    report["generated_cards"].append({
                        "note_type": operation["item"]["note_type"], "id": operation["entry"]["id"],
                        "note_id": nid, "new_cards": card_placement_evidence(col, operation["model"], new),
                    })
        raise


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
                    if args.propose_decks:
                        result = {"proposals": resolved_decks}
                    else:
                        selection = selection_plan(col, sources, resolved_decks)
                        result = {"note_types": [], "notes": []}
                        execute_selection(col, sources, resolved_decks, selection, result)
                finally:
                    col.close()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as exc:
        sys.exit(f"Preview stopped: {exc}")


if __name__ == "__main__":
    main()
