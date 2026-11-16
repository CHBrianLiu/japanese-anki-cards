import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

from anki.collection import Collection

import test_preview


class ApplyCommandTests(unittest.TestCase):
    def setUp(self):
        test_preview.PreviewCommandTests.setUp(self)
        command = Path(__file__).parent / "apply_yaml.py"
        if command.exists():
            shutil.copy2(command, self.tool / command.name)

    def run_apply(self, approve=True, env=None):
        command = [sys.executable, str(self.tool / "apply_yaml.py"),
                   "--sandbox", self.collection.parent.name,
                   "--note-type", "Headless_Preview_Fixture"]
        if approve:
            command.append("--approve")
        return subprocess.run(command, capture_output=True, text=True, env=env)

    def state(self):
        col = Collection(str(self.collection))
        try:
            model = col.models.by_name("Headless_Preview_Fixture")
            return {
                "notes": {col.get_note(nid).fields[0]: {
                    "id": nid, "guid": col.get_note(nid).guid,
                    "fields": col.get_note(nid).fields, "tags": col.get_note(nid).tags,
                } for nid in col.models.nids(model["id"])},
                "cards": col.db.all("select * from cards order by id"),
                "history": col.db.all("select * from revlog order by id"),
                "decks": sorted(col.decks.all(), key=lambda deck: deck["id"]), "model": model,
            }
        finally:
            col.close()

    def test_apply_persists_updates_and_additions_and_second_run_is_noop(self):
        before = self.state()
        result = self.run_apply()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["persistence_verified"])
        self.assertEqual([note["action"] for note in report["notes"]], ["update", "add"])
        after = self.state()
        old = before["notes"]["001_0001"]
        updated = after["notes"]["001_0001"]
        self.assertEqual((updated["id"], updated["guid"]), (old["id"], old["guid"]))
        self.assertEqual(updated["fields"], ["001_0001", "Changed", ""])
        self.assertEqual(updated["tags"], ["REPO_DELETE"])
        self.assertEqual(after["history"], before["history"])
        self.assertEqual(after["cards"][:len(before["cards"])], before["cards"])
        self.assertEqual(after["decks"], before["decks"])
        self.assertEqual(after["model"], before["model"])
        for key in before["notes"].keys() - {"001_0001"}:
            self.assertEqual(after["notes"][key], before["notes"][key])
        second = self.run_apply()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual([note["action"] for note in json.loads(second.stdout)["notes"]], ["unchanged", "unchanged"])
        self.assertEqual(self.state(), after)
        self.assertFalse(list(self.collection.parent.glob("before-*")))
        self.assertFalse(list(self.root.rglob("*.csv")))

    def test_conditional_cards_use_yaml_deck_and_existing_review_cards_stay_put(self):
        col = Collection(str(self.collection))
        try:
            card = col.get_card(self.sandbox["baseline"]["card_ids"][0])
            card.type = 2
            card.queue = 2
            card.due = 75
            card.ivl = 21
            card.factor = 2500
            col.update_card(card)
        finally:
            col.close()
        before = self.state()
        self.entries.write_text(
            'notetype: Headless_Preview_Fixture\ndeck: Preview Sandbox::Target\nentries:\n'
            '  - CustomID: "001_0001"\n    Text: "Changed"\n'
            '    Extra: |\n      first line\n      second line\n    Tags:\n', encoding="utf-8")
        result = self.run_apply()
        self.assertEqual(result.returncode, 0, result.stderr)
        item = json.loads(result.stdout)["notes"][0]
        self.assertEqual(item["tags_removed"], ["old_tag", "personal"])
        self.assertEqual(len(item["new_card_ids"]), 1)
        after = self.state()
        self.assertEqual(after["notes"]["001_0001"]["fields"][2], "first line<br>second line")
        self.assertEqual(after["notes"]["001_0001"]["tags"], [])
        old_card = next(row for row in after["cards"] if row[0] == card.id)
        self.assertEqual(old_card, next(row for row in before["cards"] if row[0] == card.id))
        new_card = next(row for row in after["cards"] if row[0] == item["new_card_ids"][0])
        self.assertEqual(new_card[2], self.sandbox["deck_candidates"][1]["id"])
        self.assertEqual(after["history"], before["history"])
        self.assertEqual(json.loads(self.run_apply().stdout)["notes"][0]["action"], "unchanged")
        self.assertEqual(self.state(), after)

    def test_approval_and_invalid_sources_fail_before_writes(self):
        before = self.collection.read_bytes()
        result = self.run_apply(approve=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--approve", result.stderr)
        self.assertEqual(self.collection.read_bytes(), before)
        original = self.entries.read_text(encoding="utf-8")
        for text, message in (
            (original.replace('CustomID: "001_0001"', 'CustomID: plain'), "quoted"),
            (original.replace('CustomID: "001_0002"', 'CustomID: "001_0001"'), "duplicate stable ID"),
            (original.replace('Text: "New"', 'Unknown: x'), "unknown Fields"),
            (original.replace('Text: "New"', 'Text: ""'), "required Text"),
            (original.replace('Text: "New"', 'Text: "[sound:missing.mp3]"'), "media reference"),
            (original.replace("Preview Sandbox::Target", "Missing::Deck"), "Deck target"),
        ):
            with self.subTest(message=message):
                self.entries.write_text(text, encoding="utf-8")
                result = self.run_apply()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertEqual(self.collection.read_bytes(), before)
        self.entries.write_text(original, encoding="utf-8")
        self.assertEqual(self.run_apply().returncode, 0)

    def test_incompatible_missing_and_ambiguous_note_types_fail_before_writes(self):
        col = Collection(str(self.collection))
        try:
            model = col.models.by_name("Headless_Preview_Fixture")
            duplicate = col.new_note(model)
            duplicate["CustomID"] = "001_0001"
            duplicate["Text"] = "Unrelated duplicate"
            col.add_note(duplicate, self.sandbox["deck_candidates"][1]["id"])
        finally:
            col.close()
        before = self.collection.read_bytes()
        self.assertIn("Ambiguous existing stable ID", self.run_apply().stderr)
        self.assertEqual(self.collection.read_bytes(), before)
        col = Collection(str(self.collection))
        try:
            model = col.models.by_name("Headless_Preview_Fixture")
            model["flds"][2]["name"] = "Wrong"
            col.models.update_dict(model)
        finally:
            col.close()
        before = self.collection.read_bytes()
        self.assertIn("schema mismatch", self.run_apply().stderr)
        self.assertEqual(self.collection.read_bytes(), before)
        col = Collection(str(self.collection))
        try:
            model = col.models.by_name("Headless_Preview_Fixture")
            model["name"] = "Different_Note_Type"
            col.models.update_dict(model)
        finally:
            col.close()
        before = self.collection.read_bytes()
        self.assertIn("Missing compatible existing Note Type", self.run_apply().stderr)
        self.assertEqual(self.collection.read_bytes(), before)

    def test_template_override_conflict_is_rejected_during_disposable_rehearsal(self):
        col = Collection(str(self.collection))
        try:
            model = col.models.by_name("Headless_Preview_Fixture")
            model["tmpls"][0]["did"] = self.sandbox["deck_candidates"][0]["id"]
            col.models.update_dict(model)
        finally:
            col.close()
        before = self.collection.read_bytes()
        result = self.run_apply()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Conflicting Template Deck override", result.stderr)
        self.assertEqual(self.collection.read_bytes(), before)

    def test_partial_failure_reports_committed_progress_and_releases_target(self):
        # Test-only fault at the native API boundary, never a production CLI flag.
        injection = self.root / "injection"
        injection.mkdir()
        (injection / "sitecustomize.py").write_text(
            'import os\nfrom anki.collection import Collection\n'
            'original = Collection.add_note\n'
            'def fail(self, note, deck_id):\n'
            '    if os.path.realpath(self.path) == os.path.realpath(os.environ["FAIL_COLLECTION"]):\n'
            '        raise RuntimeError("injected native addition failure")\n'
            '    return original(self, note, deck_id)\n'
            'Collection.add_note = fail\n', encoding="utf-8")
        tempdir = self.root / "disposable"
        tempdir.mkdir()
        env = {**os.environ, "PYTHONPATH": str(injection),
               "FAIL_COLLECTION": str(self.collection), "TMPDIR": str(tempdir)}
        result = self.run_apply(env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("injected native addition failure", result.stderr)
        self.assertIn('"action": "update"', result.stderr)
        self.assertIn("fresh preview and approval", result.stderr)
        self.assertIn("No rollback or restoration", result.stderr)
        after = self.state()
        self.assertEqual(after["notes"]["001_0001"]["fields"][1], "Changed")
        self.assertNotIn("001_0002", after["notes"])
        self.assertEqual(list(tempdir.iterdir()), [])
        self.assertFalse(list(self.collection.parent.glob("before-*")))
        result = self.run_apply()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([note["action"] for note in json.loads(result.stdout)["notes"]], ["unchanged", "add"])

    def test_absent_notes_empty_conditional_cards_and_other_note_types_are_retained(self):
        col = Collection(str(self.collection))
        try:
            model = col.models.by_name("Headless_Preview_Fixture")
            note = col.get_note(self.sandbox["baseline"]["note_id"])
            note["Extra"] = "Previously generated"
            col.update_note(note)
            other = col.models.new("Other_Fixture")
            col.models.add_field(other, col.models.new_field("CustomID"))
            template = col.models.new_template("Card")
            template["qfmt"] = "{{CustomID}}"
            template["afmt"] = "{{FrontSide}}"
            col.models.add_template(other, template)
            other = col.models.get(col.models.add_dict(other).id)
            unrelated = col.new_note(other)
            unrelated["CustomID"] = "001_0001"
            unrelated.tags = ["personal"]
            col.add_note(unrelated, self.sandbox["deck_candidates"][0]["id"])
            unrelated_id = unrelated.id
        finally:
            col.close()
        before = self.state()
        result = self.run_apply()
        self.assertEqual(result.returncode, 0, result.stderr)
        after = self.state()
        self.assertEqual(after["cards"][:len(before["cards"])], before["cards"])
        col = Collection(str(self.collection))
        try:
            self.assertEqual(col.get_note(unrelated_id).fields, ["001_0001"])
            self.assertEqual(col.get_note(unrelated_id).tags, ["personal"])
        finally:
            col.close()

    def test_filtered_targets_and_source_cards_fail_without_writes(self):
        col = Collection(str(self.collection))
        try:
            filtered_id = col.decks.new_filtered("Fixture Filtered")
        finally:
            col.close()
        original = self.entries.read_text(encoding="utf-8")
        self.entries.write_text(original.replace("Preview Sandbox::Target", "Fixture Filtered"), encoding="utf-8")
        before = self.collection.read_bytes()
        self.assertIn("filtered Deck target", self.run_apply().stderr)
        self.assertEqual(self.collection.read_bytes(), before)
        self.entries.write_text(original, encoding="utf-8")
        col = Collection(str(self.collection))
        try:
            card = col.get_card(self.sandbox["baseline"]["card_ids"][0])
            card.odid = card.did
            card.did = filtered_id
            col.update_card(card)
        finally:
            col.close()
        before = self.collection.read_bytes()
        self.assertIn("Filtered source Card", self.run_apply().stderr)
        self.assertEqual(self.collection.read_bytes(), before)

    def test_media_is_validated_without_modification_or_retained_copies(self):
        media = self.collection.parent / "collection.media" / "fixture.mp3"
        media.write_bytes(b"synthetic media")
        self.entries.write_text(self.entries.read_text(encoding="utf-8").replace(
            'Text: "Changed"', 'Text: "[sound:fixture.mp3]"'), encoding="utf-8")
        tempdir = self.root / "disposable"
        tempdir.mkdir()
        result = self.run_apply(env={**os.environ, "TMPDIR": str(tempdir)})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(media.read_bytes(), b"synthetic media")
        self.assertEqual(list(tempdir.iterdir()), [])
        self.assertFalse(list(self.collection.parent.glob("before-*")))

    def test_unicode_normalization_respects_collection_setting_and_converges(self):
        original = self.entries.read_text(encoding="utf-8")
        for enabled, expected in ((True, "が"), (False, "か\u3099")):
            with self.subTest(normalization=enabled):
                col = Collection(str(self.collection))
                try:
                    col.conf["normalize_note_text"] = enabled
                finally:
                    col.close()
                self.entries.write_text(original.replace('Text: "Changed"', 'Text: "か\u3099"').replace(
                    'Tags: REPO_DELETE', 'Tags: か\u3099'), encoding="utf-8")
                preview = test_preview.PreviewCommandTests.run_preview(self)
                self.assertEqual(preview.returncode, 0, preview.stderr)
                result = self.run_apply()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.state()["notes"]["001_0001"]["fields"][1], expected)
                self.assertEqual(self.state()["notes"]["001_0001"]["tags"], ["が"])
                second = self.run_apply()
                self.assertEqual(second.returncode, 0, second.stderr)
                self.assertEqual(json.loads(second.stdout)["notes"][0]["action"], "unchanged")

    def test_interruption_reports_committed_progress_and_releases_target(self):
        injection = self.root / "injection"
        injection.mkdir()
        (injection / "sitecustomize.py").write_text(
            'import os\nfrom anki.collection import Collection\n'
            'original = Collection.add_note\n'
            'def interrupt(self, note, deck_id):\n'
            '    if os.path.realpath(self.path) == os.path.realpath(os.environ["INTERRUPT_COLLECTION"]):\n'
            '        raise KeyboardInterrupt("injected interrupt")\n'
            '    return original(self, note, deck_id)\n'
            'Collection.add_note = interrupt\n', encoding="utf-8")
        result = self.run_apply(env={**os.environ, "PYTHONPATH": str(injection),
                                     "INTERRUPT_COLLECTION": str(self.collection)})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('"action": "update"', result.stderr)
        self.assertIn("fresh preview and approval", result.stderr)
        self.assertEqual(self.state()["notes"]["001_0001"]["fields"][1], "Changed")
        self.assertEqual(self.run_apply().returncode, 0)

    def test_normalized_stable_ids_match_and_collisions_fail_before_writes(self):
        original = self.entries.read_text(encoding="utf-8")
        self.entries.write_text(original.replace('CustomID: "001_0002"', 'CustomID: "か\u3099"'), encoding="utf-8")
        result = self.run_apply()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("が", self.state()["notes"])
        self.assertEqual([note["action"] for note in json.loads(self.run_apply().stdout)["notes"]], ["unchanged", "unchanged"])
        self.entries.write_text(original.replace('CustomID: "001_0001"', 'CustomID: "が"').replace(
            'CustomID: "001_0002"', 'CustomID: "か\u3099"'), encoding="utf-8")
        before = self.collection.read_bytes()
        result = self.run_apply()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Duplicate stable ID after native normalization", result.stderr)
        self.assertEqual(self.collection.read_bytes(), before)

    def test_existing_decomposed_ids_are_updated_and_canonical_ambiguity_is_rejected(self):
        col = Collection(str(self.collection))
        try:
            col.conf["normalize_note_text"] = False
            note = col.get_note(self.sandbox["baseline"]["note_id"])
            note["CustomID"] = "か\u3099"
            col.update_note(note)
            col.conf["normalize_note_text"] = True
        finally:
            col.close()
        self.entries.write_text(self.entries.read_text(encoding="utf-8").replace(
            'CustomID: "001_0001"', 'CustomID: "か\u3099"'), encoding="utf-8")
        result = self.run_apply()
        self.assertEqual(result.returncode, 0, result.stderr)
        item = next(item for item in json.loads(result.stdout)["notes"] if item["id"] == "か\u3099")
        self.assertEqual(item["action"], "update")
        self.assertEqual(self.state()["notes"]["が"]["id"], note.id)
        col = Collection(str(self.collection))
        try:
            col.conf["normalize_note_text"] = False
            duplicate = col.new_note(col.models.by_name("Headless_Preview_Fixture"))
            duplicate["CustomID"] = "か\u3099"
            duplicate["Text"] = "Canonical duplicate"
            col.add_note(duplicate, self.sandbox["deck_candidates"][1]["id"])
            col.conf["normalize_note_text"] = True
        finally:
            col.close()
        before = self.collection.read_bytes()
        self.assertIn("Ambiguous existing stable ID", self.run_apply().stderr)
        self.assertEqual(self.collection.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
