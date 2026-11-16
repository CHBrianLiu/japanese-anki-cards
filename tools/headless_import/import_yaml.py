#!/usr/bin/env python3
"""Import repository Note Types and YAML Notes into a tool-created sandbox."""

import argparse
import fcntl
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from html.parser import HTMLParser
from pathlib import Path

import yaml

from create_sandbox import prerequisites


NOTE_TYPE = "Japanese_Mined_Vocab"
NOTE_TYPES = (
    "Japanese_Familiarity_Vocab", "Japanese_Listening", "Japanese_Mined_Grammar",
    NOTE_TYPE, "Japanese_Sentence_Production",
)


class StrictLoader(yaml.SafeLoader):
    pass


def mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if key in result:
            raise ValueError(f"Duplicate YAML key {key!r} at line {key_node.start_mark.line + 1}")
        result[key] = loader.construct_object(value_node, deep=True)
    return result


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)


def normalize(value):
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        raise ValueError("Ordinary Field values must be scalars, not lists or mappings.")
    return str(value).strip().replace("\r\n", "\n").replace("\n", "<br>")


class MediaReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.names = set()

    def handle_starttag(self, tag, attrs):
        if tag in {"img", "audio", "video", "source"}:
            for key, value in attrs:
                if key in {"src", "poster"} and value:
                    self.names.add(value)


def media_references(text, styles=False):
    parser = MediaReferences()
    parser.feed(text)
    names = parser.names | set(re.findall(r"\[sound:([^\]]+)\]", text))
    if styles:
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        names.update(match.group(2).strip() for match in
                     re.finditer(r"url\(\s*(['\"]?)(.*?)\1\s*\)", text, re.IGNORECASE))
        names.update(re.findall(r"@import\s+['\"]([^'\"]+)['\"]", text, re.IGNORECASE))
        names = {name for name in names if name and not name.lower().startswith("data:")}
    return names


def load_source(note_type_dir):
    note_type = note_type_dir.name
    config = yaml.load(
        (note_type_dir / "entries/entries-config.yaml").read_text(encoding="utf-8"),
        Loader=StrictLoader,
    )
    schema = (note_type_dir / "note-type.md").read_text(encoding="utf-8")
    field_names = re.findall(r"^\|\s*\d+\s*\|\s*`([^`]+)`", schema, re.MULTILINE)
    if config["notetype"] != note_type or not field_names or "Tags" in field_names:
        raise ValueError("Schema must declare ordinary Fields separately from native Tags.")
    columns = [field["name"] for field in config["fields"]]
    if not columns or columns[0] != field_names[0] or columns.count("Tags") > 1 or [name for name in columns if name != "Tags"] != field_names:
        raise ValueError("Legacy config ordinary Field order does not match schema.")
    required = {field["name"] for field in config["fields"] if field["required"] and field["name"] != "Tags"}
    card_section = schema.split("## Card Types\n", 1)[1].split("\n## ", 1)[0]
    card_types = re.findall(r"^\d+\.\s+\*\*([A-Za-z0-9_]+)", card_section, re.MULTILINE)
    actual_card_types = {path.name for path in (note_type_dir / "card-types").iterdir() if path.is_dir()}
    if not card_types or len(card_types) != len(set(card_types)) or set(card_types) != actual_card_types:
        raise ValueError("Documented Card Types must match Template directories in stable order")
    templates, media = [], set()
    for name in card_types:
        directory = note_type_dir / "card-types" / name
        template = {
            "name": name,
            "qfmt": (directory / "front.html").read_text(encoding="utf-8"),
            "afmt": (directory / "back.html").read_text(encoding="utf-8"),
        }
        for text in (template["qfmt"], template["afmt"]):
            references = re.findall(r"{{\s*[#^/]?\s*([^{}]+?)\s*}}", text)
            referenced_fields = {reference.split(":")[-1].strip() for reference in references}
            unknown = referenced_fields - set(field_names) - {"FrontSide", "Tags", "Type", "Deck", "Subdeck", "Card", "CardFlag"}
            if unknown:
                raise ValueError(f"{name}: undeclared Template Fields {sorted(unknown)}")
            references = media_references(text, styles=True)
            if any("{{" in reference or "}}" in reference for reference in references):
                raise ValueError(f"{name}: Dynamic Template media references are unsupported")
            media.update(references)
        templates.append(template)
    css = (note_type_dir / "style.css").read_text(encoding="utf-8")
    media.update(media_references(css, styles=True))
    entries, seen = [], set()
    paths = sorted((note_type_dir / "entries").glob("*.yaml"))
    for path in paths:
        if path.name == "entries-config.yaml":
            continue
        raw = path.read_text(encoding="utf-8")
        data = yaml.load(raw, Loader=StrictLoader)
        if not isinstance(data, dict) or data.get("notetype") != note_type:
            raise ValueError(f"{path.name}: incorrect Note Type")
        deck = data.get("deck")
        if not isinstance(deck, str) or not deck.strip() or deck != deck.strip():
            raise ValueError(f"{path.name}: missing or invalid target Deck")
        if any(not part.strip() or part != part.strip() for part in deck.split("::")):
            raise ValueError(f"{path.name}: invalid hierarchical Deck name")
        rows = data.get("entries")
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"{path.name}: expected nonempty entries")
        node = yaml.compose(raw, Loader=StrictLoader)
        entry_nodes = next(value for key, value in node.value if key.value == "entries")
        for row, row_node in zip(rows, entry_nodes.value):
            if not isinstance(row, dict):
                raise ValueError(f"{path.name}: entry must be a mapping")
            unknown = set(row) - set(field_names) - {"Tags"}
            if unknown:
                raise ValueError(f"{path.name}: unknown Fields {sorted(unknown)}")
            custom_id = row.get(field_names[0])
            id_node = next((v for k, v in row_node.value if k.value == field_names[0]), None)
            if (
                not isinstance(custom_id, str) or not custom_id.strip()
                or custom_id != custom_id.strip() or id_node.style not in {"'", '"'}
            ):
                raise ValueError(f"{path.name}: stable ID must be a quoted nonempty trimmed string")
            if custom_id in seen:
                raise ValueError(f"{path.name}: duplicate stable ID {custom_id}")
            seen.add(custom_id)
            for name in required:
                if not normalize(row.get(name)):
                    raise ValueError(f"{path.name}, {custom_id}: required {name} is empty")
            tags = row.get("Tags")
            if tags is not None and not isinstance(tags, str):
                raise ValueError(f"{path.name}, {custom_id}: Tags must be a string or null")
            values = [normalize(row.get(name)) for name in field_names]
            for text in values:
                media.update(media_references(text))
            entries.append({"id": custom_id, "fields": values, "tags": (tags or "").split(), "deck": deck})
    return {"name": note_type, "fields": field_names, "templates": templates, "css": css, "entries": entries, "media": media}


@contextmanager
def sandbox_access(local_root, sandbox_name):
    if not re.fullmatch(r"sandbox-[a-zA-Z0-9_-]+", sandbox_name):
        raise ValueError("Select a sandbox-* name, not a Collection path")
    root = local_root.resolve()
    sandbox = root / sandbox_name
    if sandbox.is_symlink() or sandbox.resolve().parent != root:
        raise ValueError("Sandbox must be a real direct child of this tool's .local folder")
    collection = sandbox / "collection.anki2"
    manifest_path = sandbox / "manifest.json"
    if not collection.is_file() or collection.is_symlink() or manifest_path.is_symlink():
        raise ValueError("Expected an existing tool-created sandbox Collection")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if Path(manifest["collection"]).resolve() != collection.resolve() or "baseline" not in manifest:
        raise ValueError("Sandbox manifest does not identify this Collection")
    running = subprocess.run(
        ["pgrep", "-ifl", r"/Applications/Anki.app/Contents/|anki-launcher|python.*-m aqt"],
        capture_output=True, text=True, check=False,
    )
    if running.returncode != 1:
        raise ValueError("Quit Anki Desktop completely before sandbox API import")
    with (sandbox / ".import.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another sandbox import is running") from exc
        yield collection, manifest


def backup_database(collection):
    backup_dir = Path(tempfile.mkdtemp(prefix="before-import-", dir=collection.parent))
    backup = backup_dir / "collection.anki2"
    def progress(status, remaining, total):
        if status in {sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED}:
            raise ValueError("Collection is locked; backup stopped before backend access")
    source = sqlite3.connect(collection.as_uri() + "?mode=ro", uri=True, timeout=0)
    try:
        destination = sqlite3.connect(backup)
        try:
            source.backup(destination, progress=progress)
        finally:
            destination.close()
    finally:
        source.close()
    return str(backup)


def fixture_state(col, manifest):
    ids = (manifest["baseline"]["note_id"], manifest["baseline"]["unrelated_note_id"])
    return {
        "notes": col.db.all("select * from notes where id in (?, ?) order by id", *ids),
        "cards": col.db.all("select * from cards where nid in (?, ?) order by id", *ids),
        "revlog": col.db.all("select * from revlog order by id"),
    }


def other_note_state(col, selected_model_id):
    """Protect already imported Note Types and their Cards from this import."""
    return {
        "notes": col.db.all("select * from notes where mid != ? order by id", selected_model_id),
        "cards": col.db.all(
            "select c.* from cards c join notes n on n.id = c.nid where n.mid != ? order by c.id",
            selected_model_id,
        ),
    }


def import_yaml(local_root, sandbox_name, note_type_dir, anki_app):
    versions = prerequisites(anki_app)
    source = load_source(note_type_dir)
    note_type = source["name"]
    report = {**versions, "note_type": note_type, "notes_added": 0, "notes_updated": 0, "cards_moved": 0, "decks_created": [], "note_type_created": False}
    with sandbox_access(local_root, sandbox_name) as (collection, manifest):
        for name in sorted(source["media"]):
            if Path(name).name != name or not (collection.parent / "collection.media" / name).is_file():
                raise ValueError(f"Missing or unsupported target media reference: {name}")
        report["collection"] = str(collection)
        report["backup"] = backup_database(collection)
        from anki.collection import Collection
        col = Collection(str(collection))
        try:
            before = fixture_state(col, manifest)
            if len(before["notes"]) != 2:
                raise ValueError("Synthetic baseline Notes are missing; wrong or modified sandbox")
            model = col.models.by_name(note_type)
            other_before = other_note_state(col, model["id"] if model else -1)
            if model:
                if [f["name"] for f in model["flds"]] != source["fields"] or model["type"] != 0:
                    raise ValueError("Existing Note Type schema does not match repository")
                if [{k: t[k] for k in ("name", "qfmt", "afmt")} for t in model["tmpls"]] != source["templates"] or model["css"] != source["css"]:
                    raise ValueError("Existing Templates/CSS differ; automatic updates are outside this exploration")
                if any(t.get("did") for t in model["tmpls"]):
                    raise ValueError("Template Deck overrides are unsupported")
            matches = {}
            if model:
                for nid in col.models.nids(model["id"]):
                    note = col.get_note(nid)
                    if note.fields[0] in matches:
                        raise ValueError(f"Ambiguous existing stable ID: {note.fields[0]}")
                    matches[note.fields[0]] = nid
            decks = {}
            for name in sorted({entry["deck"] for entry in source["entries"]}):
                deck = col.decks.by_name(name)
                if deck and (deck["dyn"] or deck["name"] != name):
                    raise ValueError(f"Filtered or nonexact Deck match: {name}")
                decks[name] = deck["id"] if deck else None
            for entry in source["entries"]:
                if entry["id"] in matches:
                    for cid in col.card_ids_of_note(matches[entry["id"]]):
                        card = col.get_card(cid)
                        if card.odid or col.decks.get(card.did)["dyn"]:
                            raise ValueError(f"Filtered source Card for {entry['id']}")
            if model is None:
                model = col.models.new(note_type)
                for name in source["fields"]:
                    col.models.add_field(model, col.models.new_field(name))
                for template in source["templates"]:
                    native = col.models.new_template(template["name"])
                    native.update(template)
                    col.models.add_template(model, native)
                model["css"] = source["css"]
                model = col.models.get(col.models.add_dict(model).id)
                report["note_type_created"] = True
            for name, did in decks.items():
                if did is None:
                    decks[name] = col.decks.add_normal_deck_with_name(name).id
                    report["decks_created"].append(name)
            for entry in source["entries"]:
                nid = matches.get(entry["id"])
                note = col.get_note(nid) if nid else col.new_note(model)
                tag_key = lambda values: {tag.casefold() for tag in values}
                changed = note.fields != entry["fields"] or tag_key(note.tags) != tag_key(entry["tags"])
                if changed or not nid:
                    note.fields = entry["fields"][:]
                    note.tags = entry["tags"][:]
                    if nid:
                        col.update_note(note)
                        report["notes_updated"] += 1
                    else:
                        col.add_note(note, decks[entry["deck"]])
                        report["notes_added"] += 1
                cards = [cid for cid in col.card_ids_of_note(note.id) if col.get_card(cid).did != decks[entry["deck"]]]
                if cards:
                    col.set_deck(cards, decks[entry["deck"]])
                    report["cards_moved"] += len(cards)
            if fixture_state(col, manifest) != before:
                raise ValueError("Import altered synthetic fixture or review history")
            if other_note_state(col, model["id"]) != other_before:
                raise ValueError("Import altered Notes/Cards of another Note Type")
        except Exception as exc:
            raise RuntimeError(f"Sandbox import stopped; operations may already be committed. Progress: {json.dumps(report)}. Error: {exc}") from exc
        finally:
            col.close()
        col = Collection(str(collection))
        try:
            model = col.models.by_name(note_type)
            if (
                [field["name"] for field in model["flds"]] != source["fields"]
                or [{k: t[k] for k in ("name", "qfmt", "afmt")} for t in model["tmpls"]] != source["templates"]
                or model["css"] != source["css"]
            ):
                raise ValueError("Persisted Note Type schema, Templates, or CSS differ")
            actual = {col.get_note(nid).fields[0]: col.get_note(nid) for nid in col.models.nids(model["id"])}
            for entry in source["entries"]:
                note = actual[entry["id"]]
                if note.fields != entry["fields"] or {t.casefold() for t in note.tags} != {t.casefold() for t in entry["tags"]}:
                    raise ValueError(f"Persisted content/tags differ for {entry['id']}")
                if any(col.get_card(cid).did != decks[entry["deck"]] for cid in col.card_ids_of_note(note.id)):
                    raise ValueError(f"Persisted Deck placement differs for {entry['id']}")
            if fixture_state(col, manifest) != before:
                raise ValueError("Synthetic baseline changed after reopen")
            if other_note_state(col, model["id"]) != other_before:
                raise ValueError("Another Note Type's Notes/Cards changed after reopen")
            report["notes_verified"] = len(source["entries"])
            report["cards_verified"] = sum(len(col.card_ids_of_note(actual[e["id"]].id)) for e in source["entries"])
            report["persistence_verified"] = True
            report["other_note_types_preserved"] = True
        finally:
            col.close()
        (collection.parent / "last-import.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (collection.parent / f"last-import-{note_type}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sandbox", required=True, help="Tool-created sandbox-* folder name; never a live Collection path")
    parser.add_argument("--anki-app", type=Path, default=Path("/Applications/Anki.app"))
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--note-type", choices=NOTE_TYPES, action="append", help="Import a selected Note Type; repeat to select several")
    selection.add_argument("--other-note-types", action="store_true", help="Import all repository Note Types except Japanese_Mined_Vocab")
    args = parser.parse_args()
    tool = Path(__file__).resolve().parent
    reports = []
    try:
        selected = [name for name in NOTE_TYPES if name != NOTE_TYPE] if args.other_note_types else args.note_type or [NOTE_TYPE]
        selected = list(dict.fromkeys(selected))
        directories = [tool.parents[1] / "note-types" / name for name in selected]
        # Validate every selected source before the first Collection mutation.
        for directory in directories:
            load_source(directory)
        for directory in directories:
            reports.append(import_yaml(tool / ".local", args.sandbox, directory, args.anki_app))
    except Exception as exc:
        sys.exit(f"Import stopped: {exc}. Completed imports: {json.dumps(reports, ensure_ascii=False)}")
    print(json.dumps(reports[0] if len(reports) == 1 else reports, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
