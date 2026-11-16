import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

import test_apply_yaml


class GuardedCommandTests(unittest.TestCase):
    setUp = test_apply_yaml.ApplyCommandTests.setUp
    state = test_apply_yaml.ApplyCommandTests.state

    def command(self, *args, env=None):
        source = Path(__file__).parent / "update_collection.py"
        if source.exists():
            shutil.copy2(source, self.tool / source.name)
        return subprocess.run([
            sys.executable, str(self.tool / "update_collection.py"),
            "--sandbox", self.collection.parent.name,
            "--note-type", "Headless_Preview_Fixture", *args,
        ], capture_output=True, text=True, env=env)

    def test_rehearsal_approval_applies_persisted_changes_and_requires_fresh_preview(self):
        before = self.state()
        preview = self.command()
        self.assertEqual(preview.returncode, 0, preview.stderr)
        report = json.loads(preview.stdout)
        self.assertTrue(report["rehearsal_verified"])
        self.assertEqual(report["deck_links"], [self.sandbox["deck_candidates"][1]])
        self.assertEqual(self.state(), before)
        token = report["approval"]
        rejected = self.command("--approve", token)
        self.assertIn("--approve-deck-links", rejected.stderr)
        applied = self.command("--approve", token, "--approve-deck-links")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertTrue(json.loads(applied.stdout)["persistence_verified"])
        self.assertEqual(self.state()["notes"]["001_0001"]["fields"][1], "Changed")
        stale = self.command("--approve", token, "--approve-deck-links")
        self.assertNotEqual(stale.returncode, 0)
        self.assertIn("fresh preview", stale.stderr)

    def test_changed_sources_media_and_unrelated_history_invalidate_approval(self):
        media = self.collection.parent / "collection.media" / "fixture.mp3"
        media.write_bytes(b"first")
        self.entries.write_text(self.entries.read_text().replace(
            'Text: "Changed"', 'Text: "[sound:fixture.mp3]"'))
        for change in ("source", "media", "history"):
            with self.subTest(change=change):
                preview = self.command()
                self.assertEqual(preview.returncode, 0, preview.stderr)
                token = json.loads(preview.stdout)["approval"]
                if change == "source":
                    self.entries.write_text(self.entries.read_text() + "\n# changed source\n")
                elif change == "media":
                    media.write_bytes(b"second")
                else:
                    from anki.collection import Collection
                    col = Collection(str(self.collection))
                    try:
                        card = col.get_card(col.card_ids_of_note(self.sandbox["baseline"]["unrelated_note_id"])[0])
                        card.start_timer()
                        col.sched.answerCard(card, 3)
                    finally:
                        col.close()
                before = self.state()
                result = self.command("--approve", token, "--approve-deck-links")
                self.assertIn("Stale approval", result.stderr)
                self.assertEqual(self.state(), before)

    def test_wal_inclusive_rehearsal_never_changes_source_or_retains_artifacts(self):
        import sqlite3
        db = sqlite3.connect(self.collection)
        self.addCleanup(db.close)
        db.execute("pragma journal_mode=wal")
        db.execute("update notes set flds = replace(flds, ?, ?)",
                   ("Existing <b>synthetic</b> content", "Committed WAL content"))
        db.commit()
        wal = Path(str(self.collection) + "-wal")
        before = self.collection.read_bytes(), wal.read_bytes()
        temporary = self.root / "temporary"
        temporary.mkdir()
        result = self.command(env={**os.environ, "TMPDIR": str(temporary)})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["notes"][0]["fields"]["Text"]["before"], "Committed WAL content")
        self.assertEqual((self.collection.read_bytes(), wal.read_bytes()), before)
        self.assertEqual(list(temporary.iterdir()), [])
        self.assertFalse(list(self.collection.parent.glob("before-*")))

    def test_updater_and_native_lock_contention_release_resources(self):
        import fcntl
        from anki.collection import Collection
        token = json.loads(self.command().stdout)["approval"]
        with (self.collection.parent / ".import.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertIn("Another sandbox import", self.command().stderr)
        col = Collection(str(self.collection))
        try:
            result = self.command("--approve", token, "--approve-deck-links")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("lock", result.stderr.lower())
        finally:
            col.close()
        self.assertEqual(self.command().returncode, 0)

    def test_collection_selection_manifest_and_schema_guards(self):
        before = self.collection.read_bytes()
        for selection in ("Personal Profile", str(self.collection), "../sandbox-elsewhere"):
            result = self.command("--sandbox", selection)
            self.assertIn("not a Collection path", result.stderr)
        manifest_path = self.collection.parent / "manifest.json"
        original = manifest_path.read_text()
        manifest = json.loads(original)
        manifest["collection"] = str(self.root / "isolated-profile/collection.anki2")
        manifest_path.write_text(json.dumps(manifest))
        self.assertIn("does not identify", self.command().stderr)
        manifest["collection"] = str(self.collection)
        manifest["package_version"] = "2.1.0"
        manifest_path.write_text(json.dumps(manifest))
        self.assertIn("version mismatch", self.command().stderr)
        manifest_path.write_text(original)
        self.assertEqual(self.collection.read_bytes(), before)
        import sqlite3
        db = sqlite3.connect(self.collection)
        db.execute("update col set ver = 17")
        db.commit()
        db.close()
        before = self.collection.read_bytes()
        self.assertIn("schema version", self.command().stderr)
        self.assertEqual(self.collection.read_bytes(), before)

    def test_desktop_opening_during_rehearsal_blocks_application(self):
        token = json.loads(self.command().stdout)["approval"]
        injection = self.root / "injection"
        injection.mkdir()
        (injection / "sitecustomize.py").write_text(
            'import subprocess\noriginal = subprocess.run\nchecks = 0\n'
            'def run(command, *args, **kwargs):\n'
            '    global checks\n'
            '    if command[0] == "pgrep":\n'
            '        checks += 1\n'
            '        return subprocess.CompletedProcess(command, 1 if checks == 1 else 0, "", "")\n'
            '    return original(command, *args, **kwargs)\n'
            'subprocess.run = run\n')
        before = self.state()
        result = self.command("--approve", token, "--approve-deck-links",
                              env={**os.environ, "PYTHONPATH": str(injection)})
        self.assertIn("Quit Anki Desktop", result.stderr)
        self.assertEqual(self.state(), before)

    def test_source_change_during_rehearsal_requires_fresh_preview(self):
        injection = self.root / "injection"
        injection.mkdir()
        (injection / "sitecustomize.py").write_text(
            'import os\nfrom pathlib import Path\nfrom anki.collection import Collection\n'
            'original = Collection.close\n'
            'def close(self, *args, **kwargs):\n'
            '    result = original(self, *args, **kwargs)\n'
            '    path = Path(os.environ["CHANGE_SOURCE"])\n'
            '    if "anki-rehearsal-" in self.path and path.exists():\n'
            '        text = path.read_text()\n'
            '        if "# changed during rehearsal" not in text:\n'
            '            path.write_text(text + "\\n# changed during rehearsal\\n")\n'
            '    return result\n'
            'Collection.close = close\n')
        before = self.state()
        result = self.command(env={**os.environ, "PYTHONPATH": str(injection),
                                   "CHANGE_SOURCE": str(self.entries)})
        self.assertIn("changed during rehearsal", result.stderr)
        self.assertEqual(self.state(), before)

    def test_complete_workflow_smoke(self):
        """Documented sandbox-only smoke: retained Templates/CSS, YAML/tags/media."""
        (self.source / "card-types/Conditional/front.html").write_text("{{CustomID}}")
        (self.source / "card-types/Primary/back.html").write_text("{{FrontSide}}<hr>Smoke {{Text}}")
        css = self.source / "style.css"
        css.write_text(css.read_text() + "\n/* smoke styling */")
        media = self.collection.parent / "collection.media" / "fixture.mp3"
        media.write_bytes(b"synthetic smoke media")
        self.entries.write_text(self.entries.read_text().replace(
            'Text: "New"', 'Text: "[sound:fixture.mp3]"'))
        before = self.state()
        preview = self.command()
        self.assertEqual(preview.returncode, 0, preview.stderr)
        proposal = json.loads(preview.stdout)
        self.assertTrue(proposal["rehearsal_verified"])
        self.assertEqual(Path(proposal["collection"]).resolve(), self.collection.resolve())
        self.assertEqual(self.state(), before)
        approval = ["--approve", proposal["approval"], "--approve-deck-links", "--approve-note-types"]
        applied = self.command(*approval)
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertTrue(json.loads(applied.stdout)["persistence_verified"])
        after = self.state()  # Independently reopen the explicitly selected sandbox.
        self.assertEqual(after["history"], before["history"])
        for card in before["cards"]:
            self.assertIn(card, after["cards"])
        self.assertEqual(after["notes"]["001_0001"]["tags"], ["REPO_DELETE"])
        self.assertEqual(after["notes"]["001_0002"]["fields"][1], "[sound:fixture.mp3]")
        self.assertEqual(after["model"]["tmpls"][1]["qfmt"], "{{CustomID}}")
        self.assertIn("smoke styling", after["model"]["css"])
        for item in json.loads(applied.stdout)["notes"]:
            for card in item.get("new_cards", []):
                self.assertEqual(card["deck"]["id"], proposal["deck_links"][0]["id"])
        again = self.command()
        self.assertEqual(again.returncode, 0, again.stderr)
        token = json.loads(again.stdout)["approval"]
        noop = self.command("--approve", token, "--approve-deck-links")
        self.assertEqual(noop.returncode, 0, noop.stderr)
        self.assertTrue(all(item["action"] == "unchanged" for item in json.loads(noop.stdout)["notes"]))
        self.assertEqual(self.state(), after)
        self.assertEqual(media.read_bytes(), b"synthetic smoke media")
        self.assertFalse(list(self.collection.parent.glob("before-*")))
        self.assertFalse(list(self.root.rglob("*.zip")))
        if os.environ.get("HEADLESS_SMOKE_REPORT"):
            print(json.dumps({"sandbox": self.collection.parent.name,
                              "collection": str(self.collection), "deck_links": proposal["deck_links"],
                              "reopened_and_verified": True, "second_run": "no-op",
                              "temporary_fixture_disposed_on_exit": True}, indent=2))

    def test_scheduling_change_at_native_open_rejects_stale_approval(self):
        token = json.loads(self.command().stdout)["approval"]
        injection = self.root / "injection"
        injection.mkdir()
        (injection / "sitecustomize.py").write_text(
            'import os, sqlite3\nfrom anki.collection import Collection\n'
            'original = Collection.__init__\n'
            'def initialize(self, path, *args, **kwargs):\n'
            '    if os.path.realpath(path) == os.path.realpath(os.environ["CHANGE_TARGET"]):\n'
            '        db = sqlite3.connect(path)\n'
            '        db.execute("update cards set due = due + 100 where nid = ?", '
            '(int(os.environ["CHANGE_NOTE"]),))\n'
            '        db.commit()\n        db.close()\n'
            '    return original(self, path, *args, **kwargs)\n'
            'Collection.__init__ = initialize\n')
        before = self.state()
        result = self.command("--approve", token, "--approve-deck-links", env={
            **os.environ, "PYTHONPATH": str(injection), "CHANGE_TARGET": str(self.collection),
            "CHANGE_NOTE": str(self.sandbox["baseline"]["unrelated_note_id"]),
        })
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fresh preview", result.stderr)
        self.assertEqual(self.state()["notes"], before["notes"])

    def test_missing_inline_css_field_media_blocks_rehearsal(self):
        self.entries.write_text(self.entries.read_text().replace(
            'Text: "Changed"', 'Text: \'<div style="background:url(missing.png)">Changed</div>\''))
        before = self.state()
        result = self.command()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("media reference", result.stderr)
        self.assertEqual(self.state(), before)


class GuardedIntegratedTests(test_apply_yaml.ApplyCommandTests):
    command = GuardedCommandTests.command

    def run_apply(self, approve=True, env=None, approve_note_types=False):
        if not approve:
            return self.command("--approve", "", env=env)
        preview = self.command(env=env)
        if preview.returncode:
            return preview
        args = ["--approve", json.loads(preview.stdout)["approval"], "--approve-deck-links"]
        if approve_note_types:
            args.append("--approve-note-types")
        return self.command(*args, env=env)
