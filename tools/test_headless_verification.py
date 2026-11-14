import json
import os
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


COMMAND = Path(__file__).with_name("verify_headless_api.py")


class HeadlessVerificationTest(unittest.TestCase):
    def run_command(self, *args):
        return subprocess.run(
            [sys.executable, str(COMMAND), *args],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            timeout=120,
        )

    def test_disposable_verification_reports_persisted_and_idempotent_results(self):
        result = self.run_command()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["persistence_verified"])
        self.assertGreater(report["review_history_rows"], 0)
        self.assertGreater(report["new_cards"], 0)
        self.assertEqual(report["second_run_mutations"], [])
        self.assertTrue(report["lock_failure_verified"])
        self.assertTrue(report["connections_released"])
        self.assertIn("before", report["learning_move"])
        self.assertIn("after", report["learning_move"])
        self.assertIn("before", report["fsrs_move"])
        self.assertIn("after", report["fsrs_move"])
        self.assertIsNone(report["destination_side_effect"]["before"]["memory_state"])
        self.assertIsNotNone(report["destination_side_effect"]["after"]["memory_state"])

    def test_missing_desktop_stops_before_backend_access(self):
        result = self.run_command("--anki-app", "/nonexistent/Anki.app")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Anki Desktop", result.stderr)

    def test_incompatible_desktop_version_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=COMMAND.parent) as directory:
            app = Path(directory) / "Anki.app"
            (app / "Contents").mkdir(parents=True)
            with (app / "Contents/Info.plist").open("wb") as file:
                plistlib.dump({"CFBundleShortVersionString": "1.2.3"}, file)
            result = self.run_command("--anki-app", str(app))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not match", result.stderr)

    def test_missing_package_reports_prerequisite(self):
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        result = subprocess.run(
            [sys.executable, "-S", str(COMMAND)],
            capture_output=True, text=True, env=env, timeout=30,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("matching Anki package", result.stderr)


if __name__ == "__main__":
    unittest.main()
