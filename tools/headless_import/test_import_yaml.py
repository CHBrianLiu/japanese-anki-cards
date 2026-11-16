import shutil
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from anki.collection import Collection

from create_sandbox import create_sandbox
from import_yaml import NOTE_TYPE, NOTE_TYPES, import_yaml, load_source, sandbox_access


class ImportYamlTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.app = Path("/Applications/Anki.app")
        original = Path(__file__).resolve().parents[2] / "note-types" / NOTE_TYPE
        self.source = self.root / NOTE_TYPE
        shutil.copytree(original, self.source, ignore=shutil.ignore_patterns("*.csv"))

    def sandbox(self):
        report = create_sandbox(self.root / "local", self.app)
        path = Path(report["collection"])
        return path, path.parent.name

    def run_import(self, name):
        return import_yaml(self.root / "local", name, self.source, self.app)

    def test_full_import_and_second_run_no_op(self):
        path, name = self.sandbox()
        before_csv = sorted(self.source.rglob("*.csv"))
        first = self.run_import(name)
        self.assertEqual(first["notes_added"], 189)
        self.assertEqual(first["cards_verified"], 378)
        self.assertEqual(len(first["decks_created"]), 6)
        self.assertTrue(first["persistence_verified"])
        self.assertTrue(Path(first["backup"]).is_file())
        col = Collection(str(path))
        try:
            identities = col.db.all("select id, guid from notes order by id")
            cards = col.db.all("select * from cards order by id")
            model = col.models.by_name(NOTE_TYPE)
            self.assertEqual(len(model["flds"]), 7)
            self.assertEqual([t["name"] for t in model["tmpls"]], ["Comprehension", "Production"])
        finally:
            col.close()
        second = self.run_import(name)
        self.assertEqual(second["notes_added"], 0)
        self.assertEqual(second["notes_updated"], 0)
        self.assertEqual(second["cards_moved"], 0)
        self.assertEqual(second["decks_created"], [])
        self.assertFalse(second["note_type_created"])
        self.assertEqual(sorted(self.source.rglob("*.csv")), before_csv)
        col = Collection(str(path))
        try:
            self.assertEqual(col.db.all("select id, guid from notes order by id"), identities)
            self.assertEqual(col.db.all("select * from cards order by id"), cards)
        finally:
            col.close()

    def test_update_replaces_tags_normalizes_html_and_moves_cards(self):
        path, name = self.sandbox()
        self.run_import(name)
        col = Collection(str(path))
        try:
            model = col.models.by_name(NOTE_TYPE)
            nid = next(nid for nid in col.models.nids(model["id"]) if col.get_note(nid).fields[0] == "005_0001")
            note = col.get_note(nid)
            note.tags = ["personal"]
            col.update_note(note)
            identity = (note.id, note.guid, col.card_ids_of_note(nid))
        finally:
            col.close()
        source = self.source / "entries/005_private_lessons.yaml"
        text = source.read_text(encoding="utf-8")
        text = text.replace("deck: Japanese::Vocabulary", "deck: Japanese::Exploration New Deck", 1)
        text = text.replace('Notes: ""', 'Notes: |\n      first line\n      second <b>line</b>', 1)
        text = text.replace('Tags: ""', 'Tags: "REPO_DELETE"', 1)
        source.write_text(text, encoding="utf-8")
        report = self.run_import(name)
        self.assertEqual(report["notes_updated"], 1)
        self.assertGreater(report["cards_moved"], 0)
        col = Collection(str(path))
        try:
            note = col.get_note(nid)
            self.assertEqual(note.tags, ["REPO_DELETE"])
            self.assertEqual(note["Notes"], "first line<br>second <b>line</b>")
            self.assertEqual((note.id, note.guid, col.card_ids_of_note(nid)), identity)
        finally:
            col.close()
        source.write_text(text.replace('Tags: "REPO_DELETE"', 'Tags:', 1), encoding="utf-8")
        self.run_import(name)
        col = Collection(str(path))
        try:
            self.assertEqual(col.get_note(nid).tags, [])
        finally:
            col.close()

    def test_unquoted_unknown_and_duplicate_yaml_keys_rejected(self):
        path = self.source / "entries/005_private_lessons.yaml"
        original = path.read_text(encoding="utf-8")
        cases = [
            (original.replace('VocabID: "005_0001"', 'VocabID: unquoted_id', 1), "quoted"),
            (original.replace('Notes: ""', 'Unknown: value', 1), "unknown Fields"),
            (original.replace('Tags: ""', 'Tags: first\n    Tags: second', 1), "Duplicate YAML key"),
            (original.replace('VocabID: "005_0002"', 'VocabID: "005_0001"', 1), "duplicate stable ID"),
        ]
        for text, error in cases:
            with self.subTest(error=error):
                path.write_text(text, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, error):
                    load_source(self.source)

    def test_missing_media_rejected_before_import(self):
        path, name = self.sandbox()
        source = self.source / "entries/005_private_lessons.yaml"
        source.write_text(source.read_text(encoding="utf-8").replace('Notes: ""', 'Notes: "[sound:missing.mp3]"', 1), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "media reference"):
            self.run_import(name)
        col = Collection(str(path))
        try:
            self.assertIsNone(col.models.by_name(NOTE_TYPE))
        finally:
            col.close()

    def test_ambiguous_collection_identity_rejected(self):
        path, name = self.sandbox()
        self.run_import(name)
        col = Collection(str(path))
        try:
            model = col.models.by_name(NOTE_TYPE)
            note = col.new_note(model)
            note["VocabID"] = "005_0001"
            note["Sentence"] = "duplicate"
            col.add_note(note, 1)
        finally:
            col.close()
        with self.assertRaisesRegex(RuntimeError, "Ambiguous existing stable ID"):
            self.run_import(name)

    def test_cannot_select_arbitrary_path(self):
        with self.assertRaisesRegex(ValueError, "not a Collection path"):
            with sandbox_access(self.root, "../collection.anki2"):
                self.fail("should not access target")

    def test_other_note_types_through_cli_preserve_verified_vocabulary(self):
        repository = self.root / "repository"
        tool = repository / "tools/headless_import"
        tool.mkdir(parents=True)
        original_tool = Path(__file__).resolve().parent
        for filename in ("import_yaml.py", "create_sandbox.py"):
            shutil.copy2(original_tool / filename, tool / filename)
        for name in NOTE_TYPES:
            shutil.copytree(
                original_tool.parents[1] / "note-types" / name,
                repository / "note-types" / name,
                ignore=shutil.ignore_patterns("*.csv"),
            )
        sandbox = create_sandbox(tool / ".local", self.app)
        path = Path(sandbox["collection"])
        name = path.parent.name
        import_yaml(tool / ".local", name, repository / "note-types" / NOTE_TYPE, self.app)
        col = Collection(str(path))
        try:
            model = col.models.by_name(NOTE_TYPE)
            card = col.get_card(col.card_ids_of_note(col.models.nids(model["id"])[0])[0])
            card.start_timer()
            col.sched.answerCard(card, 3)
            existing_notes = col.db.all("select * from notes order by id")
            existing_cards = col.db.all("select * from cards order by id")
            revlog = col.db.all("select * from revlog order by id")
        finally:
            col.close()
        command = [sys.executable, str(tool / "import_yaml.py"), "--sandbox", name, "--other-note-types"]
        expected = {
            "Japanese_Familiarity_Vocab": (8, ["Familiarity"], 0, 0),
            "Japanese_Listening": (6, ["ListeningComprehension"], 0, 0),
            "Japanese_Mined_Grammar": (7, ["Comprehension", "Production"], 30, 60),
            "Japanese_Sentence_Production": (4, ["Production"], 50, 50),
        }
        first = subprocess.run(command, capture_output=True, text=True, check=True)
        reports = json.loads(first.stdout)
        self.assertEqual({report["note_type"] for report in reports}, set(expected))
        for report in reports:
            with self.subTest(note_type=report["note_type"]):
                fields, templates, notes, cards = expected[report["note_type"]]
                self.assertTrue(report["note_type_created"])
                self.assertEqual(report["notes_added"], notes)
                self.assertEqual(report["cards_verified"], cards)
                self.assertTrue(report["other_note_types_preserved"])
        col = Collection(str(path))
        try:
            all_notes = col.db.all("select * from notes order by id")
            all_cards = col.db.all("select * from cards order by id")
            self.assertEqual([row for row in all_notes if row[0] in {n[0] for n in existing_notes}], existing_notes)
            self.assertEqual([row for row in all_cards if row[0] in {c[0] for c in existing_cards}], existing_cards)
            self.assertEqual(col.db.all("select * from revlog order by id"), revlog)
            for name, (fields, templates, notes, cards) in expected.items():
                model = col.models.by_name(name)
                self.assertEqual(len(model["flds"]), fields)
                self.assertEqual([t["name"] for t in model["tmpls"]], templates)
                self.assertNotIn("Tags", [f["name"] for f in model["flds"]])
                self.assertEqual(len(col.models.nids(model["id"])), notes)
        finally:
            col.close()
        second = subprocess.run(command, capture_output=True, text=True, check=True)
        for report in json.loads(second.stdout):
            self.assertFalse(report["note_type_created"])
            self.assertEqual(report["notes_added"], 0)
            self.assertEqual(report["notes_updated"], 0)
            self.assertEqual(report["cards_moved"], 0)
            self.assertEqual(report["decks_created"], [])
        col = Collection(str(path))
        try:
            self.assertEqual(col.db.all("select * from notes order by id"), all_notes)
            self.assertEqual(col.db.all("select * from cards order by id"), all_cards)
        finally:
            col.close()
        self.assertEqual(list((repository / "note-types").rglob("*.csv")), [])


if __name__ == "__main__":
    unittest.main()
