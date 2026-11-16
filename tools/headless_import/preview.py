#!/usr/bin/env python3
"""Preview YAML changes against a disposable copy of a tool-created sandbox."""

import argparse
import json
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

from create_sandbox import prerequisites
from import_yaml import load_source, sandbox_access


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


def resolve_links(col, requested, path, collection, proposals):
    decks = col.decks.all()
    if proposals:
        return [{"requested": name, "candidates": [
            {"id": deck["id"], "name": deck["name"]}
            for deck in decks if deck["name"] == name and not deck["dyn"]
        ]} for name in sorted(requested)]
    if path is None:
        raise ValueError("Approved Deck links are required; use --propose-decks for exact-name candidates")
    config = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(config.get("collection"), str) or Path(config["collection"]).resolve() != collection.resolve():
        raise ValueError("Deck links identify a different Collection")
    links = config.get("links")
    if not isinstance(links, list):
        raise ValueError("Deck links must be a list")
    resolved = {}
    for name in sorted(requested):
        matches = [link for link in links if isinstance(link, dict) and link.get("requested") == name]
        if len(matches) != 1:
            raise ValueError(f"Missing or ambiguous Deck link: {name}")
        link = matches[0]
        if link.get("approved") is not True or type(link.get("id")) is not int:
            raise ValueError(f"Deck link is not approved or has invalid ID: {name}")
        matches = [deck for deck in decks if deck["id"] == link["id"]]
        if len(matches) != 1 or matches[0]["name"] != link.get("name") or matches[0]["dyn"]:
            raise ValueError(f"Missing, mismatched or filtered Deck target: {name}")
        resolved[name] = {"requested": name, "resolved": matches[0]["name"], "id": matches[0]["id"]}
    return resolved


def model_for_source(col, source):
    model = col.models.by_name(source["name"])
    if model:
        if (model["name"] != source["name"] or model["type"] != 0
                or [field["name"] for field in model["flds"]] != source["fields"]
                or [template["name"] for template in model["tmpls"]] != [t["name"] for t in source["templates"]]):
            raise ValueError(f"Unsupported Note Type schema mismatch: {source['name']}")
        return model
    model = col.models.new(source["name"])
    for name in source["fields"]:
        col.models.add_field(model, col.models.new_field(name))
    for template in source["templates"]:
        native = col.models.new_template(template["name"])
        native.update(template)
        col.models.add_template(model, native)
    model["css"] = source["css"]
    return col.models.get(col.models.add_dict(model).id)


def preview_notes(col, sources, links):
    report = []
    for source in sorted(sources, key=lambda source: source["name"]):
        model = model_for_source(col, source)
        matches = {}
        wanted = {entry["id"] for entry in source["entries"]}
        for nid in col.models.nids(model["id"]):
            note = col.get_note(nid)
            if note.fields[0] in wanted:
                if note.fields[0] in matches:
                    raise ValueError(f"Ambiguous existing stable ID in {source['name']}: {note.fields[0]}")
                matches[note.fields[0]] = nid
        for entry in sorted(source["entries"], key=lambda entry: entry["id"]):
            target = links[entry["deck"]]
            nid = matches.get(entry["id"])
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
            if action != "unchanged":
                note.fields = entry["fields"][:]
                note.tags = entry["tags"][:]
                if nid:
                    col.update_note(note)
                else:
                    col.add_note(note, target["id"])
                new_cards = set(col.card_ids_of_note(note.id)) - old_cards
                for cid in new_cards:
                    template = model["tmpls"][col.get_card(cid).ord]
                    if template.get("did") and template["did"] != target["id"]:
                        raise ValueError(f"Conflicting Template Deck override: {source['name']}, {entry['id']}")
                if new_cards:
                    item["new_cards_deck"] = target
            report.append(item)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sandbox", required=True, help="Tool-created sandbox name, not a Collection path")
    parser.add_argument("--note-type", action="append", required=True, help="Repository Note Type name; repeat to select")
    parser.add_argument("--anki-app", type=Path, default=Path("/Applications/Anki.app"))
    parser.add_argument("--deck-links", type=Path, help="JSON approvals bound to the selected sandbox Collection")
    parser.add_argument("--propose-decks", action="store_true", help="Propose exact-name candidates without approving them")
    args = parser.parse_args()
    tool = Path(__file__).resolve().parent
    try:
        prerequisites(args.anki_app)
        names = sorted(set(args.note_type))
        if any(not name or Path(name).name != name or name in (".", "..") for name in names):
            raise ValueError("Note Type must be a directory name")
        sources = [load_source(tool.parents[1] / "note-types" / name) for name in names]
        requested = {entry["deck"] for source in sources for entry in source["entries"]}
        with sandbox_access(tool / ".local", args.sandbox) as (collection, _manifest):
            media_dir = collection.parent / "collection.media"
            if media_dir.is_symlink():
                raise ValueError("Sandbox media directory must not be a symlink")
            for source in sources:
                for name in sorted(source["media"]):
                    media = media_dir / name
                    if Path(name).name != name or media.is_symlink() or not media.is_file():
                        raise ValueError(f"Missing or unsupported target media reference: {name}")
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
                    links = resolve_links(col, requested, args.deck_links, collection, args.propose_decks)
                    result = {"proposals": links} if args.propose_decks else {"notes": preview_notes(col, sources, links)}
                finally:
                    col.close()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as exc:
        sys.exit(f"Preview stopped: {exc}")


if __name__ == "__main__":
    main()
