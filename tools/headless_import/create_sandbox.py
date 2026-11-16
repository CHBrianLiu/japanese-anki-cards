#!/usr/bin/env python3
"""Create a fresh, synthetic headless Collection; never open a user Collection."""

import argparse
import json
import plistlib
import sys
import tempfile
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from packaging.version import Version


def prerequisites(anki_app: Path) -> dict:
    """Inspect versions before importing or opening the Anki backend."""
    info_path = anki_app / "Contents" / "Info.plist"
    if not info_path.is_file():
        raise ValueError(f"Anki Desktop version cannot be inspected: {info_path}")
    with info_path.open("rb") as handle:
        desktop_version = plistlib.load(handle)["CFBundleShortVersionString"]
    try:
        package_version = version("anki")
    except PackageNotFoundError as exc:
        raise ValueError("Install this tool's requirements in its .venv first.") from exc
    if Version(desktop_version) != Version(package_version):
        raise ValueError(
            f"Anki version mismatch: Desktop {desktop_version}, package {package_version}. "
            "Prepare a matching package in this tool's .venv before backend access."
        )
    return {"desktop_version": desktop_version, "package_version": package_version}


def create_sandbox(local_root: Path, anki_app: Path) -> dict:
    versions = prerequisites(anki_app)
    from anki.collection import Collection

    local_root.mkdir(parents=True, exist_ok=True)
    sandbox = Path(tempfile.mkdtemp(prefix="sandbox-", dir=local_root))
    collection_path = sandbox / "collection.anki2"
    col = Collection(str(collection_path))
    try:
        source = col.decks.add_normal_deck_with_name("Preview Sandbox::Source")
        target = col.decks.add_normal_deck_with_name("Preview Sandbox::Target")
        model = col.models.new("Headless_Preview_Fixture")
        for field_name in ("CustomID", "Text", "Extra"):
            col.models.add_field(model, col.models.new_field(field_name))
        primary = col.models.new_template("Primary")
        primary["qfmt"] = "{{Text}}"
        primary["afmt"] = "{{FrontSide}}<hr>{{Extra}}"
        col.models.add_template(model, primary)
        conditional = col.models.new_template("Conditional")
        conditional["qfmt"] = "{{#Extra}}{{Extra}}{{/Extra}}"
        conditional["afmt"] = "{{Text}}"
        col.models.add_template(model, conditional)
        created = col.models.add_dict(model)
        model = col.models.get(created.id)
        if model is None:
            raise ValueError("Created synthetic Note Type could not be retrieved.")

        managed = col.new_note(model)
        managed["CustomID"] = "001_0001"
        managed["Text"] = "Existing <b>synthetic</b> content"
        managed.tags = ["personal", "old_tag"]
        col.add_note(managed, source.id)
        card = col.get_card(col.card_ids_of_note(managed.id)[0])
        card.start_timer()
        col.sched.answerCard(card, 3)

        unrelated = col.new_note(model)
        unrelated["CustomID"] = "unmanaged_0001"
        unrelated["Text"] = "Unrelated synthetic Note: preserve me"
        col.add_note(unrelated, target.id)
        baseline = {
            "note_id": managed.id,
            "guid": managed.guid,
            "card_ids": list(col.card_ids_of_note(managed.id)),
            "tags": sorted(col.get_note(managed.id).tags),
            "review_history_rows": col.db.all("select * from revlog order by id"),
            "unrelated_note_id": unrelated.id,
        }
        report = {
            **versions,
            "collection": str(collection_path),
            "media_directory": col.media.dir(),
            "note_type": model["name"],
            "ordinary_fields": [field["name"] for field in model["flds"]],
            "deck_candidates": [
                {"name": col.decks.get(source.id)["name"], "id": source.id},
                {"name": col.decks.get(target.id)["name"], "id": target.id},
            ],
            "baseline": baseline,
            "desktop_profile_registered": False,
            "deck_links_approved": False,
        }
    finally:
        col.close()

    col = Collection(str(collection_path))
    try:
        note = col.get_note(baseline["note_id"])
        if (
            note.guid != baseline["guid"]
            or list(col.card_ids_of_note(note.id)) != baseline["card_ids"]
            or sorted(note.tags) != baseline["tags"]
            or col.db.all("select * from revlog order by id")
            != baseline["review_history_rows"]
        ):
            raise ValueError("Synthetic baseline did not persist after reopening.")
    finally:
        col.close()
    report["persistence_verified"] = True
    (sandbox / "manifest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--anki-app", type=Path, default=Path("/Applications/Anki.app"),
        help="Desktop app for version inspection only, not a Collection target.",
    )
    args = parser.parse_args()
    try:
        report = create_sandbox(Path(__file__).resolve().parent / ".local", args.anki_app)
    except Exception as exc:
        sys.exit(f"Sandbox creation stopped: {exc}")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
