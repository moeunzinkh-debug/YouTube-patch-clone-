#!/usr/bin/env python3
"""Test that the emulator-only hybrid retains resources and replaces every DEX."""
import tempfile
from pathlib import Path
import unittest
import zipfile
import make_emulator_fixture as fixture


class EmulatorFixtureTest(unittest.TestCase):
    def test_hybrid_copies_patched_dex_and_original_resources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original, patched, output = root / "old.apk", root / "patched.apk", root / "hybrid.apk"
            with zipfile.ZipFile(original, "w") as archive:
                archive.writestr("AndroidManifest.xml", b"renamed manifest")
                archive.writestr("resources.arsc", b"original resources")
                archive.writestr("classes.dex", b"old dex")
                archive.writestr("META-INF/CERT.RSA", b"old signature")
            with zipfile.ZipFile(patched, "w") as archive:
                archive.writestr("AndroidManifest.xml", b"test-only stock package")
                archive.writestr("classes.dex", b"patched dex")
                archive.writestr("classes2.dex", b"extension dex")
            self.assertEqual(2, fixture.build(original, patched, output))
            with zipfile.ZipFile(output) as archive:
                self.assertEqual(b"renamed manifest", archive.read("AndroidManifest.xml"))
                self.assertEqual(b"original resources", archive.read("resources.arsc"))
                self.assertEqual(b"patched dex", archive.read("classes.dex"))
                self.assertEqual(b"extension dex", archive.read("classes2.dex"))
                self.assertNotIn("META-INF/CERT.RSA", archive.namelist())
            with self.assertRaises(ValueError):
                fixture.build(original, patched, output)

    def test_rejects_missing_dex(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original, patched, output = root / "old.apk", root / "patched.apk", root / "hybrid.apk"
            for path in (original, patched):
                with zipfile.ZipFile(path, "w") as archive:
                    archive.writestr("AndroidManifest.xml", b"test")
            with self.assertRaises(ValueError):
                fixture.build(original, patched, output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
