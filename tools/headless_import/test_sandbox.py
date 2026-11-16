import plistlib
import tempfile
import unittest
from pathlib import Path

from create_sandbox import create_sandbox


class SandboxTests(unittest.TestCase):
    def test_native_fixture_persists_and_each_run_is_fresh(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = create_sandbox(root, Path("/Applications/Anki.app"))
            second = create_sandbox(root, Path("/Applications/Anki.app"))
            self.assertNotEqual(first["collection"], second["collection"])
            self.assertTrue(first["persistence_verified"])
            self.assertFalse(first["desktop_profile_registered"])
            self.assertFalse(first["deck_links_approved"])
            self.assertEqual(first["ordinary_fields"], ["CustomID", "Text", "Extra"])
            self.assertEqual(len(first["baseline"]["card_ids"]), 1)
            self.assertEqual(len(first["baseline"]["review_history_rows"]), 1)
            self.assertTrue(Path(first["collection"]).is_file())
            self.assertTrue(Path(first["collection"]).with_name("manifest.json").is_file())

    def test_missing_app_stops_before_creating_sandbox(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "output"
            with self.assertRaisesRegex(ValueError, "cannot be inspected"):
                create_sandbox(output, root / "missing.app")
            self.assertFalse(output.exists())

    def test_mismatched_version_stops_before_creating_sandbox(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contents = root / "Anki.app" / "Contents"
            contents.mkdir(parents=True)
            with (contents / "Info.plist").open("wb") as handle:
                plistlib.dump({"CFBundleShortVersionString": "0.0.1"}, handle)
            output = root / "output"
            with self.assertRaisesRegex(ValueError, "version mismatch"):
                create_sandbox(output, root / "Anki.app")
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
