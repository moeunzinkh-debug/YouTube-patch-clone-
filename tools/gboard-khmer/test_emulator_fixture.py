#!/usr/bin/env python3
"""Offline checks for the temporary, non-distributable emulator hybrid."""
from pathlib import Path
import tempfile
import unittest
import zipfile

import make_emulator_fixture as fixture
from test_fixture import xml_with_pool


class EmulatorFixtureTests(unittest.TestCase):
    def test_settings_marker_rewrite_for_both_xml_encodings(self):
        for utf8 in (True, False):
            original = xml_with_pool(utf8, ['dev.jason.com.google.android.inputmethod.latin', fixture.CALCULATOR])
            changed = fixture.rewrite_test_marker(original)
            encoding = 'utf-8' if utf8 else 'utf-16le'
            self.assertEqual(len(original), len(changed))
            self.assertIn(fixture.KHMERLISH.encode(encoding), changed)
            self.assertNotIn(fixture.CALCULATOR.encode(encoding), changed)

    def test_hybrid_copies_patched_dex_and_assets_but_not_signatures(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original, patched, output = [root / x for x in ('old.apk', 'patched.apk', 'hybrid.apk')]
            manifest = xml_with_pool(True, ['dev.jason.com.google.android.inputmethod.latin', fixture.CALCULATOR])
            with zipfile.ZipFile(original, 'w') as archive:
                archive.writestr('AndroidManifest.xml', manifest)
                archive.writestr('resources.arsc', b'original resources')
                archive.writestr('classes.dex', b'old dex')
                archive.writestr('META-INF/CERT.RSA', b'old signature')
            with zipfile.ZipFile(patched, 'w') as archive:
                archive.writestr('classes.dex', b'patched dex')
                archive.writestr('classes2.dex', b'extension dex')
                for path in fixture.ASSETS:
                    archive.writestr(path, b'new asset')
            self.assertEqual(2, fixture.build(original, patched, output))
            with zipfile.ZipFile(output) as archive:
                self.assertIn(fixture.KHMERLISH.encode(), archive.read('AndroidManifest.xml'))
                self.assertEqual(b'original resources', archive.read('resources.arsc'))
                self.assertEqual(b'patched dex', archive.read('classes.dex'))
                self.assertEqual(b'new asset', archive.read(fixture.ASSETS[0]))
                self.assertNotIn('META-INF/CERT.RSA', archive.namelist())
            with self.assertRaises(ValueError):
                fixture.build(original, patched, output)

    def test_missing_marker_fails_closed(self):
        with self.assertRaises(ValueError):
            fixture.rewrite_test_marker(xml_with_pool(True, ['unrelated']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
