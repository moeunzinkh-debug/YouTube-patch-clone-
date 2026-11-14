#!/usr/bin/env python3
"""Offline checks for the temporary, non-distributable emulator hybrid."""
from pathlib import Path
import importlib.util
import tempfile
import struct
import unittest
from unittest.mock import patch
import zipfile

import make_emulator_fixture as fixture
from test_fixture import xml_with_pool

# Both the Translate and Khmerlish tools contain an emulator_smoke.py. Load
# this directory's file explicitly instead of relying on sys.path ordering.
_spec = importlib.util.spec_from_file_location('gboard_khmer_emulator_smoke',
                                               Path(__file__).with_name('emulator_smoke.py'))
smoke = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(smoke)


def resource_table(name: str) -> bytes:
    encoded = name.encode('utf-16le')
    package = struct.pack('<HHII', 0x0200, 288, 288, 0x7f)
    package += encoded + bytes(256 - len(encoded)) + bytes(20)
    return struct.pack('<HHII', 0x0002, 12, 12 + len(package), 1) + package


class EmulatorFixtureTests(unittest.TestCase):
    def test_patched_manifest_rewrites_package_and_provider_for_both_xml_encodings(self):
        for utf8 in (True, False):
            original = xml_with_pool(utf8, [fixture.binary_xml.NEW,
                                           fixture.binary_xml.NEW + fixture.PROVIDER_SUFFIX,
                                           fixture.CALCULATOR, fixture.KHMERLISH, fixture.GEMINI,
                                           fixture.DICTIONARY_ACTIVITY])
            changed = fixture.rewrite_test_manifest(original)
            encoding = 'utf-8' if utf8 else 'utf-16le'
            self.assertEqual(len(changed), struct.unpack_from('<I', changed, 4)[0])
            self.assertIn(fixture.binary_xml.OLD.encode(encoding), changed)
            self.assertIn((fixture.binary_xml.OLD + fixture.PROVIDER_SUFFIX).encode(encoding), changed)
            self.assertIn(fixture.KHMERLISH.encode(encoding), changed)
            self.assertIn(fixture.GEMINI.encode(encoding), changed)
            self.assertIn(fixture.CALCULATOR.encode(encoding), changed)
            self.assertIn(fixture.DICTIONARY_ACTIVITY.encode(encoding), changed)

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
                archive.writestr('AndroidManifest.xml', xml_with_pool(True, [
                    fixture.binary_xml.NEW, fixture.binary_xml.NEW + fixture.PROVIDER_SUFFIX,
                    fixture.CALCULATOR, fixture.KHMERLISH, fixture.GEMINI, fixture.DICTIONARY_ACTIVITY]))
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
                self.assertIn(fixture.GEMINI.encode(), archive.read('AndroidManifest.xml'))
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

    def test_missing_activity_or_provider_fails_closed(self):
        with self.assertRaises(ValueError):
            fixture.rewrite_test_manifest(xml_with_pool(True, ['unrelated']))
        with self.assertRaises(ValueError):
            fixture.rewrite_test_manifest(xml_with_pool(True, [fixture.binary_xml.NEW,
                fixture.CALCULATOR, fixture.KHMERLISH, fixture.GEMINI, fixture.DICTIONARY_ACTIVITY]))


class DocumentPickerTests(unittest.TestCase):
    def test_filename_tap_does_not_open_thumbnail_preview(self):
        name = 'khmerlish-smoke-valid.csv'
        xml = ('<hierarchy><node text="" content-desc="Preview the file ' + name
               + '" bounds="[248,232][296,280]"/><node text="' + name
               + '" content-desc="" bounds="[214,372][284,392]"/></hierarchy>')
        with patch.object(smoke.common, 'dump_ui', return_value=xml), \
                patch.object(smoke.common, 'run') as run, patch.object(smoke.time, 'sleep'):
            self.assertTrue(smoke.tap_synthetic_filename(name))
            run.assert_called_once_with('adb', 'shell', 'input', 'tap', '249', '382')


class WordEditIconTests(unittest.TestCase):
    def test_taps_the_actual_edit_icon_not_the_label(self):
        xml = ('<hierarchy><node class="android.widget.TextView" text="srey" '
               'content-desc="Edit word srey ស្រី" bounds="[10,20][200,70]"/>'
               '<node class="android.widget.ImageButton" text="" content-desc="Edit word srey" '
               'clickable="true" bounds="[220,20][268,68]"/></hierarchy>')
        with patch.object(smoke.common, 'dump_ui', return_value=xml), \
                patch.object(smoke.common, 'run') as run, patch.object(smoke.time, 'sleep'):
            smoke.tap_word_edit_icon('srey')
            run.assert_called_once_with('adb', 'shell', 'input', 'tap', '244', '44')


class NativeSymbolKeyboardTests(unittest.TestCase):
    def test_recognizes_native_keys_and_accessible_symbol_names(self):
        nodes = [
            {'text': 'p', 'bounds': '[0,0][10,10]'},
            {'description': 'Symbol keyboard', 'text': '?123', 'bounds': '[10,0][20,10]'},
            {'description': 'Apostrophe, more characters', 'bounds': '[20,0][30,10]'},
            {'description': 'Space, English', 'bounds': '[30,0][40,10]'},
            {'description': 'Alphabet keyboard', 'bounds': '[40,0][50,10]'},
        ]
        positions = smoke.native_keyboard_positions(nodes)
        self.assertEqual((5, 5), positions['p'])
        self.assertEqual((15, 5), positions['?123'])
        self.assertEqual((25, 5), positions["'"])
        self.assertEqual((35, 5), positions[' '])
        self.assertEqual((45, 5), positions['abc'])

    def test_types_with_real_page_switches(self):
        mode = ['letters']
        typed = []
        pages = {
            'letters': {'p': (1, 1), 'o': (2, 1), ' ': (3, 1), '?123': (99, 1)},
            'symbols': {"'": (4, 1), ' ': (3, 1), 'abc': (98, 1), 'more symbols': (97, 1)},
        }
        def tap(*args):
            point = (int(args[-2]), int(args[-1]))
            if point == (99, 1):
                mode[0] = 'symbols'
            elif point == (98, 1):
                mode[0] = 'letters'
            else:
                typed.append(point)
        with patch.object(smoke.common, 'inspect_ime_windows', return_value=[]), \
                patch.object(smoke, 'native_keyboard_positions', side_effect=lambda _: pages[mode[0]]), \
                patch.object(smoke, 'editor_text', return_value='synthetic'), \
                patch.object(smoke.common, 'run', side_effect=tap), patch.object(smoke.time, 'sleep'):
            smoke.enter_native_symbols("p'o", {})
        self.assertEqual([(1, 1), (4, 1), (2, 1), (3, 1)], typed)
        self.assertEqual('letters', mode[0])


class PanelLayoutTests(unittest.TestCase):
    def test_panel_smoke_switches_between_letters_and_both_symbol_pages(self):
        mode = ['letters']
        typed = []
        pages = {
            'letters': {'p': (1, 1), 'o': (2, 1), 'khmerlish shift': (90, 1),
                        'khmerlish symbols': (99, 1)},
            'symbols': {"'": (3, 1), '_': (4, 1), 'more khmerlish symbols': (98, 1),
                        'khmerlish symbols': (99, 1)},
            'more': {'[': (5, 1), 'more khmerlish symbols': (98, 1),
                     'khmerlish symbols': (99, 1)},
        }
        def tap(*args):
            point = (int(args[-2]), int(args[-1]))
            if point == (99, 1):
                mode[0] = 'symbols' if mode[0] == 'letters' else 'letters'
            elif point == (98, 1):
                mode[0] = 'more' if mode[0] == 'symbols' else 'symbols'
            else:
                typed.append(point)
        with patch.object(smoke.common, 'inspect_ime_windows', return_value=[]), \
                patch.object(smoke, 'panel_key_positions', side_effect=lambda _: pages[mode[0]]), \
                patch.object(smoke.common, 'run', side_effect=tap), patch.object(smoke.time, 'sleep'):
            smoke.panel_press("p'o_[")
        self.assertEqual([(1, 1), (3, 1), (2, 1), (4, 1), (5, 1)], typed)
        self.assertEqual('more', mode[0])

    def test_panel_must_remain_inside_native_keyboard_area(self):
        native = {'native_a': [{'id': 'dev.example:id/keyboard_holder', 'bounds': '[0,381][320,616]'}]}
        contained = {'panel': [{'bounds': '[0,381][320,616]'}]}
        whole_screen = {'panel': [{'bounds': '[0,24][320,640]'}]}
        self.assertTrue(smoke.panel_within_native_keyboard(native, contained))
        self.assertFalse(smoke.panel_within_native_keyboard(native, whole_screen))
        self.assertFalse(smoke.panel_within_native_keyboard({}, contained))
        self.assertFalse(smoke.panel_within_native_keyboard(native, {'panel': [{'bounds': 'bad'}]}))

    def test_layout_paths_find_only_known_nodes(self):
        nodes = [{'class': 'Frame', 'id': 'dev.example:id/keyboard_holder', 'bounds': '[0,381][320,616]',
                  'children': [{'class': 'Key', 'description': 'a', 'bounds': '[2,475][49,523]'}]},
                 {'class': 'Panel', 'description': 'Khmerlish offline panel', 'bounds': '[0,381][320,616]'}]
        paths = smoke.keyboard_layout_paths(nodes)
        self.assertEqual('dev.example:id/keyboard_holder', paths['native_a'][0]['id'])
        self.assertTrue(smoke.panel_within_native_keyboard(paths, paths))


if __name__ == '__main__':
    unittest.main(verbosity=2)
