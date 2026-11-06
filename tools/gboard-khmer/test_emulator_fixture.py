#!/usr/bin/env python3
"""Offline checks for the temporary, non-distributable emulator hybrid."""
from pathlib import Path
import tempfile
import struct
import unittest
import zipfile

import make_emulator_fixture as fixture
from test_fixture import xml_with_pool


def resource_table(name: str) -> bytes:
    encoded = name.encode('utf-16le')
    package = struct.pack('<HHII', 0x0200, 288, 288, 0x7f)
    package += encoded + bytes(256 - len(encoded)) + bytes(20)
    return struct.pack('<HHII', 0x0002, 12, 12 + len(package), 1) + package


class EmulatorFixtureTests(unittest.TestCase):
    def test_settings_marker_rewrite_for_both_xml_encodings(self):
        for utf8 in (True, False):
            original = xml_with_pool(utf8, ['dev.jason.com.google.android.inputmethod.latin', fixture.CALCULATOR])
            changed = fixture.rewrite_test_marker(original)
            encoding = 'utf-8' if utf8 else 'utf-16le'
            self.assertEqual(len(original), len(changed))
            self.assertIn(fixture.KHMERLISH.encode(encoding), changed)
            self.assertNotIn(fixture.CALCULATOR.encode(encoding), changed)

    def test_settings_xml_can_grow_without_changing_string_indices(self):
        for utf8 in (True, False):
            original = xml_with_pool(utf8, ['before', fixture.binary_xml.NEW, 'after'])
            changed = fixture.rewrite_pool_string(original, fixture.binary_xml.NEW, fixture.binary_xml.OLD)
            encoding = 'utf-8' if utf8 else 'utf-16le'
            self.assertGreater(len(changed), len(original))
            self.assertEqual(len(changed), struct.unpack_from('<I', changed, 4)[0])
            self.assertIn(fixture.binary_xml.OLD.encode(encoding), changed)
            self.assertIn('before'.encode(encoding), changed)
            self.assertIn('after'.encode(encoding), changed)
            with self.assertRaises(ValueError):
                fixture.rewrite_pool_string(original, 'not-present', 'other')

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
                archive.writestr('resources.arsc', resource_table(fixture.binary_xml.NEW))
                values = [fixture.binary_xml.NEW, 'gboard_patches_entry',
                          'dev.jason.gboardpatches.extension.settings.GboardPatchesSettingsActivity']
                archive.writestr('res/xml/settings.xml', xml_with_pool(True, values))
                archive.writestr('res/xml/settings_legacy.xml', xml_with_pool(False, values))
                for path in fixture.ASSETS:
                    archive.writestr(path, b'new asset')
            self.assertEqual(2, fixture.build(original, patched, output))
            with zipfile.ZipFile(output) as archive:
                self.assertIn(fixture.KHMERLISH.encode(), archive.read('AndroidManifest.xml'))
                self.assertIn(fixture.binary_xml.OLD.encode('utf-16le'), archive.read('resources.arsc'))
                for path, encoding in [('res/xml/settings.xml', 'utf-8'), ('res/xml/settings_legacy.xml', 'utf-16le')]:
                    settings = archive.read(path)
                    self.assertIn(fixture.binary_xml.OLD.encode(encoding), settings)
                    self.assertEqual(len(settings), struct.unpack_from('<I', settings, 4)[0])
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
