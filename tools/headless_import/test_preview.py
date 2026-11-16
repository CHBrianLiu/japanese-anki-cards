import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from anki.collection import Collection

from create_sandbox import create_sandbox


class PreviewCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.tool = self.root / "tools/headless_import"
        self.tool.mkdir(parents=True)
        original = Path(__file__).resolve().parent
        for name in ("create_sandbox.py", "import_yaml.py"):
            shutil.copy2(original / name, self.tool / name)
        shutil.copy2(original / "preview.py", self.tool / "preview.py")
        self.source = self.root / "note-types/Headless_Preview_Fixture"
        entries = self.source / "entries"
        entries.mkdir(parents=True)
        (entries / "entries-config.yaml").write_text(
            'notetype: Headless_Preview_Fixture\nfields:\n'
            '  - {name: CustomID, required: true}\n'
            '  - {name: Text, required: true}\n'
            '  - {name: Extra, required: false}\n'
            '  - {name: Tags, required: false}\n', encoding="utf-8")
        (self.source / "note-type.md").write_text(
            '# Fixture\n\n## Fields\n\n| 1 | `CustomID` | id |\n'
            '| 2 | `Text` | text |\n| 3 | `Extra` | extra |\n\n'
            '## Card Types\n\n1. **Primary**\n2. **Conditional**\n', encoding="utf-8")
        (self.source / "style.css").write_text('', encoding="utf-8")
        for name, front, back in (
            ("Primary", "{{Text}}", "{{FrontSide}}<hr>{{Extra}}"),
            ("Conditional", "{{#Extra}}{{Extra}}{{/Extra}}", "{{Text}}"),
        ):
            directory = self.source / "card-types" / name
            directory.mkdir(parents=True)
            (directory / "front.html").write_text(front, encoding="utf-8")
            (directory / "back.html").write_text(back, encoding="utf-8")
        self.entries = entries / "fixture.yaml"
        self.entries.write_text(
            'notetype: Headless_Preview_Fixture\ndeck: Preview Sandbox::Target\nentries:\n'
            '  - CustomID: "001_0001"\n    Text: "Changed"\n    Extra: ""\n    Tags: REPO_DELETE\n'
            '  - CustomID: "001_0002"\n    Text: "New"\n', encoding="utf-8")
        self.sandbox = create_sandbox(self.tool / ".local", Path("/Applications/Anki.app"))
        self.collection = Path(self.sandbox["collection"])

    def run_preview(self):
        return subprocess.run(
            [sys.executable, str(self.tool / "preview.py"), "--sandbox", self.collection.parent.name,
              "--note-type", "Headless_Preview_Fixture"],
            capture_output=True, text=True,
        )

    def test_preview_reports_changes_without_mutating_collection(self):
        before = self.collection.read_bytes()
        result = self.run_preview()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["notes"], [
            {"note_type": "Headless_Preview_Fixture", "id": "001_0001", "action": "update",
             "fields": {"Text": {"before": "Existing <b>synthetic</b> content", "after": "Changed"}},
             "tags_added": ["REPO_DELETE"], "tags_removed": ["old_tag", "personal"]},
            {"note_type": "Headless_Preview_Fixture", "id": "001_0002", "action": "add",
             "fields": {"CustomID": {"before": "", "after": "001_0002"},
                        "Text": {"before": "", "after": "New"}},
             "tags_added": [], "tags_removed": [],
             "new_cards_deck": {"requested": "Preview Sandbox::Target", "resolved": "Preview Sandbox::Target", "id": self.sandbox["deck_candidates"][1]["id"]}},
        ])
        self.assertEqual(self.collection.read_bytes(), before)
        self.assertEqual(json.loads(self.run_preview().stdout), report)
        self.assertFalse(list(self.root.rglob("*.csv")))

    def test_invalid_entry_sources_are_rejected_through_command(self):
        original = self.entries.read_text(encoding="utf-8")
        cases = [
            (original.replace('CustomID: "001_0001"', 'CustomID: plain', 1), "quoted"),
            (original.replace('CustomID: "001_0001"', 'CustomID: ""', 1), "quoted"),
            (original.replace('Text: "Changed"', 'Unknown: x', 1), "unknown Fields"),
            (original.replace('Text: "Changed"', 'Text: ""', 1), "required Text"),
            (original.replace('CustomID: "001_0002"', 'CustomID: "001_0001"'), "duplicate stable ID"),
            (original.replace('deck: Preview Sandbox::Target', 'deck: ""'), "target Deck"),
            (original.replace('deck: Preview Sandbox::Target', 'deck: Preview Sandbox::::Target'), "hierarchical Deck"),
            (original.replace('notetype: Headless_Preview_Fixture', 'notetype: Wrong'), "Note Type"),
            (original.replace('Text: "Changed"', 'Text: "[sound:missing.mp3]"'), "media reference"),
            (original.replace('Text: "Changed"', 'Text: "<img src=missing.png>"'), "media reference"),
            (original.replace('Tags: REPO_DELETE', 'Tags: [one, two]'), "Tags must be"),
            ('notetype: Headless_Preview_Fixture\ndeck: Preview Sandbox::Target\nentries: []\n', "nonempty entries"),
            (original.replace('    Extra: ""', '    Text: duplicate\n    Extra: ""'), "Duplicate YAML key"),
        ]
        before = self.collection.read_bytes()
        for text, message in cases:
            with self.subTest(message=message):
                self.entries.write_text(text, encoding="utf-8")
                result = self.run_preview()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)
                self.assertEqual(self.collection.read_bytes(), before)
        self.entries.write_text(original, encoding="utf-8")

    def test_yaml_deck_resolves_without_approval_file_and_missing_decks_fail(self):
        self.assertEqual(self.run_preview().returncode, 0)
        self.entries.write_text(self.entries.read_text(encoding="utf-8").replace(
            "Preview Sandbox::Target", "Missing::Deck"), encoding="utf-8")
        result = self.run_preview()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing, ambiguous or filtered Deck target", result.stderr)

    def test_preview_includes_committed_wal_without_checkpointing_source(self):
        import sqlite3

        source = sqlite3.connect(self.collection)
        self.addCleanup(source.close)
        self.assertEqual(source.execute("pragma journal_mode=wal").fetchone()[0], "wal")
        source.execute("update notes set flds = replace(flds, ?, ?) where id = ?",
                       ("Existing <b>synthetic</b> content", "WAL-only content", self.sandbox["baseline"]["note_id"]))
        source.commit()
        wal = Path(str(self.collection) + "-wal")
        before = self.collection.read_bytes(), wal.read_bytes()
        result = self.run_preview()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["notes"][0]["fields"]["Text"]["before"], "WAL-only content")
        self.assertEqual((self.collection.read_bytes(), wal.read_bytes()), before)

    def test_duplicate_ids_across_entry_files_are_rejected(self):
        second = self.entries.with_name("second.yaml")
        second.write_text(self.entries.read_text(encoding="utf-8"), encoding="utf-8")
        result = self.run_preview()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate stable ID", result.stderr)

    def test_ambiguous_matching_notes_and_schema_mismatch_are_rejected(self):
        col = Collection(str(self.collection))
        try:
            model = col.models.by_name("Headless_Preview_Fixture")
            note = col.new_note(model)
            note["CustomID"] = "001_0001"
            note["Text"] = "Duplicate"
            col.add_note(note, self.sandbox["deck_candidates"][1]["id"])
        finally:
            col.close()
        result = self.run_preview()
        self.assertIn("Ambiguous existing stable ID", result.stderr)
        schema = self.source / "note-type.md"
        schema.write_text(schema.read_text(encoding="utf-8").replace('`Extra`', '`Wrong`'), encoding="utf-8")
        config = self.source / "entries/entries-config.yaml"
        config.write_text(config.read_text(encoding="utf-8").replace('name: Extra', 'name: Wrong'), encoding="utf-8")
        template = self.source / "card-types/Primary/back.html"
        template.write_text(template.read_text(encoding="utf-8").replace('Extra', 'Wrong'), encoding="utf-8")
        template = self.source / "card-types/Conditional/front.html"
        template.write_text(template.read_text(encoding="utf-8").replace('Extra', 'Wrong'), encoding="utf-8")
        self.entries.write_text(self.entries.read_text(encoding="utf-8").replace('Extra:', 'Wrong:'), encoding="utf-8")
        result = self.run_preview()
        self.assertIn("schema mismatch", result.stderr)

    def test_propose_decks_does_not_approve_or_create_them(self):
        command = [sys.executable, str(self.tool / "preview.py"), "--sandbox", self.collection.parent.name,
                   "--note-type", "Headless_Preview_Fixture", "--propose-decks"]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        target = self.sandbox["deck_candidates"][1]
        self.assertEqual(json.loads(result.stdout), {"proposals": [{"requested": target["name"], "candidates": [target]}]})
        self.entries.write_text(self.entries.read_text(encoding="utf-8").replace(target["name"], "Missing::Deck"), encoding="utf-8")
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout), {"proposals": [{"requested": "Missing::Deck", "candidates": []}]})

    def test_tag_clearing_normalization_and_new_conditional_card(self):
        self.entries.write_text(
            'notetype: Headless_Preview_Fixture\ndeck: Preview Sandbox::Target\nentries:\n'
            '  - CustomID: "001_0001"\n    Text: "Existing <b>synthetic</b> content"\n'
            '    Extra: |\n      first line\n      second line\n    Tags:\n', encoding="utf-8")
        result = self.run_preview()
        self.assertEqual(result.returncode, 0, result.stderr)
        note = json.loads(result.stdout)["notes"][0]
        self.assertEqual(note["fields"], {"Extra": {"before": "", "after": "first line<br>second line"}})
        self.assertEqual(note["tags_removed"], ["old_tag", "personal"])
        self.assertEqual(note["new_cards_deck"]["resolved"], "Preview Sandbox::Target")

    def test_filtered_deck_target_and_source_are_rejected(self):
        col = Collection(str(self.collection))
        try:
            filtered_id = col.decks.new_filtered("Fixture Filtered")
        finally:
            col.close()
        original = self.entries.read_text(encoding="utf-8")
        self.entries.write_text(original.replace("Preview Sandbox::Target", "Fixture Filtered"), encoding="utf-8")
        self.assertIn("filtered Deck target", self.run_preview().stderr)
        self.entries.write_text(original, encoding="utf-8")
        col = Collection(str(self.collection))
        try:
            card = col.get_card(self.sandbox["baseline"]["card_ids"][0])
            card.odid = card.did
            card.did = filtered_id
            col.update_card(card)
        finally:
            col.close()
        self.assertIn("Filtered source Card", self.run_preview().stderr)

    def test_media_is_read_only_and_disposable_copies_are_removed_on_success_and_failure(self):
        tempdir = self.root / "temporary"
        tempdir.mkdir()
        media = self.collection.parent / "collection.media" / "fixture.mp3"
        media.write_bytes(b"synthetic media")
        self.entries.write_text(self.entries.read_text(encoding="utf-8").replace('Text: "Changed"', 'Text: "[sound:fixture.mp3]"'), encoding="utf-8")
        command = [sys.executable, str(self.tool / "preview.py"), "--sandbox", self.collection.parent.name,
                   "--note-type", "Headless_Preview_Fixture"]
        env = {**os.environ, "TMPDIR": str(tempdir)}
        before = self.collection.read_bytes(), media.read_bytes()
        result = subprocess.run(command, capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(tempdir.iterdir()), [])
        self.assertEqual((self.collection.read_bytes(), media.read_bytes()), before)
        self.entries.write_text(self.entries.read_text(encoding="utf-8").replace(
            "Preview Sandbox::Target", "Missing::Deck"), encoding="utf-8")
        result = subprocess.run(command, capture_output=True, text=True, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(list(tempdir.iterdir()), [])
        self.assertEqual((self.collection.read_bytes(), media.read_bytes()), before)

    def test_unchanged_note_ignores_existing_card_deck_and_other_note_types(self):
        self.entries.write_text(
            'notetype: Headless_Preview_Fixture\ndeck: Preview Sandbox::Target\nentries:\n'
            '  - CustomID: "001_0001"\n    Text: "Existing <b>synthetic</b> content"\n'
            '    Tags: "personal old_tag"\n', encoding="utf-8")
        col = Collection(str(self.collection))
        try:
            model = col.models.new("Other_Fixture")
            col.models.add_field(model, col.models.new_field("CustomID"))
            template = col.models.new_template("Card")
            template["qfmt"] = "{{CustomID}}"
            template["afmt"] = "{{FrontSide}}"
            col.models.add_template(model, template)
            model = col.models.get(col.models.add_dict(model).id)
            note = col.new_note(model)
            note["CustomID"] = "001_0001"
            col.add_note(note, self.sandbox["deck_candidates"][1]["id"])
        finally:
            col.close()
        result = self.run_preview()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["notes"], [{
            "note_type": "Headless_Preview_Fixture", "id": "001_0001", "action": "unchanged",
            "fields": {}, "tags_added": [], "tags_removed": [],
        }])

    def test_conflicting_template_deck_override_is_rejected(self):
        col = Collection(str(self.collection))
        try:
            model = col.models.by_name("Headless_Preview_Fixture")
            model["tmpls"][0]["did"] = self.sandbox["deck_candidates"][0]["id"]
            col.models.update_dict(model)
        finally:
            col.close()
        result = self.run_preview()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Conflicting Template Deck override", result.stderr)

    def test_legacy_tags_column_may_be_absent_or_reordered(self):
        config = self.source / "entries/entries-config.yaml"
        original = config.read_text(encoding="utf-8")
        tags = '  - {name: Tags, required: false}\n'
        for content in (original.replace(tags, ''),
                        original.replace(tags, '').replace('  - {name: Text, required: true}\n', tags + '  - {name: Text, required: true}\n')):
            with self.subTest(content=content):
                config.write_text(content, encoding="utf-8")
                result = self.run_preview()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["notes"][0]["tags_added"], ["REPO_DELETE"])

    def test_override_does_not_block_unchanged_note_without_new_cards(self):
        self.entries.write_text(
            'notetype: Headless_Preview_Fixture\ndeck: Preview Sandbox::Target\nentries:\n'
            '  - CustomID: "001_0001"\n    Text: "Existing <b>synthetic</b> content"\n'
            '    Tags: "personal old_tag"\n', encoding="utf-8")
        col = Collection(str(self.collection))
        try:
            model = col.models.by_name("Headless_Preview_Fixture")
            model["tmpls"][0]["did"] = self.sandbox["deck_candidates"][0]["id"]
            col.models.update_dict(model)
        finally:
            col.close()
        result = self.run_preview()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["notes"][0]["action"], "unchanged")

    def test_decks_are_resolved_in_explicitly_selected_sandbox(self):
        other = create_sandbox(self.tool / ".local", Path("/Applications/Anki.app"))
        command = [sys.executable, str(self.tool / "preview.py"), "--sandbox", Path(other["collection"]).parent.name,
                   "--note-type", "Headless_Preview_Fixture"]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["notes"][1]["new_cards_deck"]["id"], other["deck_candidates"][1]["id"])


if __name__ == "__main__":
    unittest.main()
