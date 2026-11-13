#!/usr/bin/env python3
"""Verify Anki's native API exclusively against a newly created Collection."""

import argparse
import importlib.metadata
import json
import plistlib
import sys
import tempfile
from pathlib import Path


FRONT = '<div class="front">{{Prompt}}</div>'
BACK = '{{FrontSide}}<hr>{{Extra}}'
CSS = '.card { color: navy; }'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def prerequisites(app):
    try:
        with (app / "Contents/Info.plist").open("rb") as info:
            desktop = plistlib.load(info)["CFBundleShortVersionString"]
    except (OSError, KeyError, plistlib.InvalidFileException) as exc:
        raise RuntimeError(f"Cannot determine Anki Desktop version from {app}; provide --anki-app pointing to the installed app: {exc}") from exc
    try:
        from packaging.version import Version
        package = importlib.metadata.version("anki")
        compatible = Version(package) == Version(desktop)
    except ImportError:
        # Both formats use numeric release components, optionally zero padded.
        try:
            package = importlib.metadata.version("anki")
            compatible = tuple(map(int, package.split('.'))) == tuple(map(int, desktop.split('.')))
        except (importlib.metadata.PackageNotFoundError, ValueError) as exc:
            raise RuntimeError("Install a matching Anki package in the repository virtual environment; cannot verify package version") from exc
    except importlib.metadata.PackageNotFoundError as exc:
        raise RuntimeError("Install a matching Anki package in the repository virtual environment") from exc
    require(compatible, f"Anki Desktop {desktop} does not match Python package {package}; install the matching package before opening a Collection")
    return desktop, package


def card_state(card):
    state = card.memory_state
    return {"id": card.id, "deck": card.did, "type": card.type,
            "queue": card.queue, "due": card.due, "interval": card.ivl,
            "remaining_steps": card.left, "reps": card.reps,
            "memory_state": None if state is None else {"stability": state.stability, "difficulty": state.difficulty},
            "desired_retention": card.desired_retention, "decay": card.decay}


def history(col):
    # Read only: preserve every native review-history row, not just its count.
    return col.db.all("select * from revlog order by id")


def reconcile(col, note_id, model_id, destination, learning_id):
    changes = []
    model = col.models.get(model_id)
    template = model["tmpls"][0]
    if (template["qfmt"], template["afmt"], model["css"]) != (FRONT, BACK, CSS):
        template["qfmt"], template["afmt"], model["css"] = FRONT, BACK, CSS
        col.models.update_dict(model)
        changes.append("templates_and_styling")
    note = col.get_note(note_id)
    if note["Prompt"] != "updated prompt" or note["Extra"] != "conditional answer":
        note["Prompt"] = "updated prompt"
        note["Extra"] = "conditional answer"
        col.update_note(note)
        changes.append("note")
    ids = list(col.card_ids_of_note(note_id)) + [learning_id]
    to_move = [cid for cid in ids if col.get_card(cid).did != destination]
    if to_move:
        col.set_deck(to_move, destination)
        changes.append("deck_placement")
    return changes


def verify(path):
    from anki.collection import Collection
    from anki.errors import DBError

    col = Collection(str(path))
    try:
        source = col.decks.add_normal_deck_with_name("Verification Source").id
        destination = col.decks.add_normal_deck_with_name("Verification Destination").id
        config = col.decks.add_config("Verification longer steps")
        config["new"]["delays"] = [1, 10, 100]
        col.decks.update_config(config)
        col.decks.set_config_id_for_deck_dict(col.decks.get(destination), config["id"])
        model = col.models.new("Verification Note Type")
        for field in ("Prompt", "Extra"):
            col.models.add_field(model, col.models.new_field(field))
        first = col.models.new_template("Primary")
        first["qfmt"], first["afmt"] = "{{Prompt}}", "{{Prompt}}"
        second = col.models.new_template("Conditional")
        second["qfmt"], second["afmt"] = "{{#Extra}}{{Extra}}{{/Extra}}", "{{Extra}}"
        col.models.add_template(model, first)
        col.models.add_template(model, second)
        model_id = col.models.add_dict(model).id
        model = col.models.get(model_id)
        template_identity = [(t["name"], t["ord"]) for t in model["tmpls"]]
        note = col.new_note(model)
        note["Prompt"] = "original prompt"
        col.add_note(note, source)
        review_id = col.card_ids_of_note(note.id)[0]
        review = col.get_card(review_id)
        review.start_timer()
        col.sched.answerCard(review, 4)
        learner = col.new_note(model)
        learner["Prompt"] = "learning prompt"
        col.add_note(learner, source)
        learning_id = col.card_ids_of_note(learner.id)[0]
        learning = col.get_card(learning_id)
        learning.start_timer()
        col.sched.answerCard(learning, 3)
        target_note = col.new_note(model)
        target_note["Prompt"] = "existing destination review"
        col.add_note(target_note, destination)
        target_id = col.card_ids_of_note(target_note.id)[0]
        target_card = col.get_card(target_id)
        target_card.start_timer()
        col.sched.answerCard(target_card, 4)
        require(review.queue == 2 and learning.queue == 1, "Failed to create ordinary review and learning Cards")
        baseline_history = history(col)
        require(len(baseline_history) >= 2, "Native reviews did not produce history")
        before_review = card_state(col.get_card(review_id))
        before_learning = card_state(col.get_card(learning_id))
        before_destination = card_state(col.get_card(target_id))
        old_cards = set(col.card_ids_of_note(note.id))
        guid = note.guid
        col.set_config("fsrs", True)
        first_changes = reconcile(col, note.id, model_id, destination, learning_id)
        after_review = card_state(col.get_card(review_id))
        after_learning = card_state(col.get_card(learning_id))
        after_destination = card_state(col.get_card(target_id))
        new_cards = set(col.card_ids_of_note(note.id)) - old_cards
        require(new_cards, "Conditional Card was not generated")
        require(after_review["memory_state"] is not None, "FSRS move did not compute memory state")
        require(before_destination["memory_state"] is None and after_destination["memory_state"] is not None, "Expected FSRS destination Deck recalculation did not occur")
        require(before_learning["remaining_steps"] != after_learning["remaining_steps"], "Different learning steps did not affect the moved Card")
        require(history(col) == baseline_history, "Review history changed")
        require((before_review["due"], before_review["interval"]) == (after_review["due"], after_review["interval"]), "Review scheduling changed")
        require(first_changes == ["templates_and_styling", "note", "deck_placement"], "Expected native operations were not performed")
        try:
            competing = Collection(str(path))
        except DBError as exc:
            require(any(text in str(exc).lower() for text in ("lock", "already open")), f"Opening the locked Collection failed for an unexpected reason: {exc}")
        else:
            competing.close()
            raise RuntimeError("A second backend unexpectedly opened the locked Collection")
    finally:
        col.close()

    col = Collection(str(path))
    try:
        saved = col.get_note(note.id)
        model = col.models.get(model_id)
        require(saved.id == note.id and saved.guid == guid, "Note identity changed")
        require(saved["Prompt"] == "updated prompt" and saved["Extra"] == "conditional answer", "Note content did not persist")
        require((model["tmpls"][0]["qfmt"], model["tmpls"][0]["afmt"], model["css"]) == (FRONT, BACK, CSS), "Templates or styling did not persist")
        require([(t["name"], t["ord"]) for t in model["tmpls"]] == template_identity, "Card Types changed identity or order")
        require(set(col.card_ids_of_note(note.id)) == old_cards | new_cards, "Card identities changed")
        require(all(col.get_card(cid).did == destination for cid in old_cards | new_cards | {learning_id}), "Card placement did not persist")
        require(history(col) == baseline_history, "Review history changed after reopening")
        require(card_state(col.get_card(review_id)) == after_review, "Review Card did not persist")
        require(card_state(col.get_card(learning_id)) == after_learning, "Learning Card did not persist")
        require(card_state(col.get_card(target_id)) == after_destination, "Destination Card did not persist")
        before_noop = (col.db.all("select * from notes order by id"),
                       col.db.all("select * from cards order by id"), history(col),
                       col.db.scalar("select count(*) from notetypes"),
                       col.db.scalar("select count(*) from decks"))
        second = reconcile(col, note.id, model_id, destination, learning_id)
        require(not second, "Second run performed unnecessary operations")
        require(history(col) == baseline_history and set(col.card_ids_of_note(note.id)) == old_cards | new_cards, "Second run changed history or Card identities")
        after_noop = (col.db.all("select * from notes order by id"),
                      col.db.all("select * from cards order by id"), history(col),
                      col.db.scalar("select count(*) from notetypes"),
                      col.db.scalar("select count(*) from decks"))
        require(before_noop == after_noop, "Second run changed existing rows or object counts")
    finally:
        col.close()
    # Exercise cleanup after a failure inside an already-open backend as well.
    col = Collection(str(path))
    try:
        try:
            raise RuntimeError("synthetic failure")
        finally:
            col.close()
    except RuntimeError as exc:
        require(str(exc) == "synthetic failure", "Unexpected cleanup failure")
    # A final reopen verifies release and persistence after the no-op and failure.
    col = Collection(str(path))
    try:
        require(history(col) == baseline_history, "History changed after the no-op")
        require(set(col.card_ids_of_note(note.id)) == old_cards | new_cards, "Cards changed after the no-op")
        require(card_state(col.get_card(review_id)) == after_review, "Review scheduling changed after the no-op")
        require(card_state(col.get_card(target_id)) == after_destination, "Destination Card changed after the no-op")
    finally:
        col.close()
    return {"persistence_verified": True, "review_history_rows": len(baseline_history),
            "new_cards": len(new_cards), "second_run_mutations": second,
            "lock_failure_verified": True, "connections_released": True,
            "learning_move": {"before": before_learning, "after": after_learning},
            "fsrs_move": {"before": before_review, "after": after_review},
            "destination_side_effect": {"before": before_destination, "after": after_destination},
            "warning": "Native API operations save individually; this multi-operation run is not atomic. FSRS moves may recompute memory state for other Cards in the destination Deck."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--anki-app", type=Path, default=Path("/Applications/Anki.app"), help="Installed macOS Anki Desktop app (version inspection only)")
    args = parser.parse_args()
    try:
        desktop, package = prerequisites(args.anki_app)
        # No path to an existing Collection can be supplied to this command.
        with tempfile.TemporaryDirectory(prefix="anki-verification-", dir=Path(__file__).resolve().parent) as directory:
            report = verify(Path(directory) / "collection.anki2")
        report.update(desktop_version=desktop, package_version=package)
        print(json.dumps(report, indent=2))
    except Exception as exc:
        print(f"Verification stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
