#!/usr/bin/env python3
"""Rehearse, then explicitly approve updating an existing sandbox Collection."""

import argparse
import hashlib
import json
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

from packaging.version import Version

from apply_yaml import prepare, verify
from create_sandbox import prerequisites
from import_yaml import require_desktop_closed, sandbox_access
from preview import copy_database, load_selection, resolve_decks, selection_names, validate_media


def database_state(path):
    """Hash a single read transaction, including committed WAL, without checkpoints."""
    db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=0)
    try:
        # Python SQLite does not provide Anki's native collation. The dump only
        # needs a stable traversal order; no Anki matching or writes happen here.
        db.create_collation("unicase", lambda a, b: (a > b) - (a < b))
        db.execute("begin")
        if db.execute("select ver from col").fetchone() != (18,):
            raise ValueError("Unsupported Collection schema version; migrations are excluded")
        digest = hashlib.sha256()
        for statement in db.iterdump():
            digest.update(statement.encode("utf-8"))
            digest.update(b"\n")
        return digest.hexdigest()
    finally:
        db.close()


def input_state(tool, names, collection, versions):
    digest = hashlib.sha256()
    captured = {}
    names = selection_names(names)
    for name in names:
        source = tool.parents[1] / "note-types" / name
        files = [source / "note-type.md", source / "style.css"]
        files += sorted((source / "entries").glob("*.yaml"))
        files += sorted((source / "card-types").glob("*/front.html"))
        files += sorted((source / "card-types").glob("*/back.html"))
        for path in files:
            captured[path] = path.read_bytes()
            digest.update(str(path.relative_to(tool.parents[1])).encode())
            digest.update(hashlib.sha256(captured[path]).digest())
    sources = load_selection(tool, names, captured)
    media_dir = validate_media(collection, sources)
    for name in sorted({name for source in sources for name in source["media"]}):
        digest.update(name.encode())
        digest.update(hashlib.sha256((media_dir / name).read_bytes()).digest())
    digest.update((collection.parent / "manifest.json").read_bytes())
    digest.update(json.dumps(versions, sort_keys=True).encode())
    digest.update(str(collection.resolve()).encode())
    return digest.hexdigest(), sources


def approval_token(inputs, database, decks):
    return hashlib.sha256(json.dumps(
        ["sandbox-update-v1", inputs, database, decks], sort_keys=True
    ).encode()).hexdigest()


def native_database_state(col):
    """Full database evidence read while Anki owns the native Collection lock."""
    schema = col.db.all("select type, name, tbl_name, sql from sqlite_master order by type, name")
    evidence = [schema]
    for kind, name, _table, _sql in schema:
        if kind == "table":
            quoted = '"' + name.replace('"', '""') + '"'
            evidence.append([name, sorted(col.db.all(f"select * from {quoted}"), key=repr)])
    return hashlib.sha256(json.dumps(evidence, default=lambda value: value.hex(),
                                     ensure_ascii=False).encode()).hexdigest()


def update(tool, args, report):
    versions = prerequisites(args.anki_app)
    if Version(versions["package_version"]) != Version("26.9.4"):
        raise ValueError("Unsupported Anki package version; use the pinned exploration environment")
    with sandbox_access(tool / ".local", args.sandbox) as (collection, manifest):
        if (Version(manifest["package_version"]) != Version(versions["package_version"])
                or Version(manifest["desktop_version"]) != Version(versions["desktop_version"])):
            raise ValueError("Sandbox manifest version mismatch")
        inputs, sources = input_state(tool, args.note_type, collection, versions)
        requested = {entry["deck"] for source in sources for entry in source["entries"]}
        from anki.collection import Collection

        with tempfile.TemporaryDirectory(prefix="anki-rehearsal-") as temp:
            copy = Path(temp) / "collection.anki2"
            copy_database(collection, copy)
            state = database_state(copy)
            media = Path(temp) / "collection.media"
            media.mkdir()
            for name in sorted({name for source in sources for name in source["media"]}):
                shutil.copyfile(collection.parent / "collection.media" / name, media / name)
            col = Collection(str(copy))
            try:
                native_state = native_database_state(col)
                decks = resolve_decks(col, requested)
                links = [{"id": deck["id"], "name": deck["resolved"]} for deck in decks.values()]
                token = approval_token(inputs, state, links)
                if args.approve and args.approve != token:
                    raise ValueError("Stale approval; obtain a fresh preview and approval")
                rehearsal = {"note_types": [], "notes": []}
                signature, plan, before = prepare(col, sources, decks, rehearsal, True)
            finally:
                col.close()
            col = Collection(str(copy))
            try:
                verify(col, plan, before, rehearsal["notes"], sources)
            finally:
                col.close()

        # No retained snapshot or pre-apply backup: re-read the source transaction.
        fresh_inputs, fresh_sources = input_state(tool, args.note_type, collection, versions)
        if inputs != fresh_inputs or state != database_state(collection):
            raise ValueError("Inputs or Collection changed during rehearsal; fresh preview required")
        if not args.approve:
            report.update(rehearsal)
            report.update(collection=str(collection), deck_links=links,
                          approval=token, rehearsal_verified=True)
            return
        if not args.approve_deck_links:
            raise ValueError("Review Collection-bound Deck IDs, then supply --approve-deck-links")
        # Recheck Desktop and versions while retaining the outer updater lock.
        require_desktop_closed()
        if prerequisites(args.anki_app) != versions:
            raise ValueError("Anki versions changed; fresh preview required")
        fresh_inputs, fresh_sources = input_state(tool, args.note_type, collection, versions)
        if inputs != fresh_inputs or state != database_state(collection):
            raise ValueError("Inputs or Collection changed before application; fresh preview required")
        col = Collection(str(collection))  # Native lock failures are never bypassed.
        try:
            if native_database_state(col) != native_state:
                raise ValueError("Collection changed at native lock acquisition; fresh preview required")
            fresh_inputs, fresh_sources = input_state(tool, args.note_type, collection, versions)
            if inputs != fresh_inputs:
                raise ValueError("Inputs changed at native lock acquisition; fresh preview required")
            actual_decks = resolve_decks(col, requested)
            if actual_decks != decks:
                raise ValueError("Deck links changed; fresh preview required")
            _, plan, before = prepare(col, fresh_sources, actual_decks, report,
                                      args.approve_note_types, committed=True, expected=signature)
        finally:
            col.close()
        col = Collection(str(collection))
        try:
            verify(col, plan, before, report["notes"], fresh_sources)
            report["persistence_verified"] = True
        finally:
            col.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sandbox", required=True, help="Tool-created sandbox name, not a Profile or path")
    parser.add_argument("--note-type", action="append", required=True)
    parser.add_argument("--anki-app", type=Path, default=Path("/Applications/Anki.app"))
    parser.add_argument("--approve", metavar="TOKEN", help="Exact approval token from the reviewed rehearsal")
    parser.add_argument("--approve-deck-links", action="store_true")
    parser.add_argument("--approve-note-types", action="store_true")
    args = parser.parse_args()
    report = {"note_types": [], "notes": [], "persistence_verified": False}
    try:
        if args.approve is not None and not args.approve:
            raise ValueError("--approve requires the reviewed rehearsal token")
        update(Path(__file__).resolve().parent, args, report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
    except (Exception, KeyboardInterrupt) as exc:
        sys.exit(f"Update stopped: {exc}. Native operations may already be committed; "
                 f"committed progress: {json.dumps(report, ensure_ascii=False)}. "
                 "Obtain a fresh preview and approval before retrying. No rollback or restoration attempted.")


if __name__ == "__main__":
    main()
