#!/usr/bin/env python3
"""Offline provenance, dictionary, and overlay regression tests."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'tools/gboard-khmer'

spec = importlib.util.spec_from_file_location('khmer_dictionary', BASE / 'build_dictionary.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class DictionaryTests(unittest.TestCase):
    def test_reproducible_offline_dictionary(self):
        output, stats = builder.make_dictionary()
        self.assertEqual(output, builder.OUTPUT.read_bytes())
        self.assertEqual(stats['entries'], 24506)
        self.assertGreater(stats['excluded_ambiguous_keys'], 1000)
        self.assertIn(b'Chrea Chanchhunneng',
                      (BASE / 'overlay/patches/src/main/resources/gboard-khmer/LICENSE.txt').read_bytes())

    def test_examples_shortcuts_and_case_independent_keys(self):
        pairs = dict(line.split('\t') for line in builder.OUTPUT.read_text(encoding='utf-8').splitlines())
        for key, expected in {'nv': 'នៅ', 'na': 'ណា', 'kampuchea': 'កម្ពុជា',
                              'kampu': 'កម្ពុជា', 'nak': 'អ្នក', 'srey': 'ស្រី',
                              'sart': 'ស្អាត', 'nik': 'នឹក', 'o': 'អូន'}.items():
            self.assertEqual(pairs[key], expected)
        self.assertNotIn('som', pairs)  # Multiple different Khmer outputs, not reviewed.
        self.assertNotIn('a', pairs)
        self.assertNotIn('i', pairs)

    def test_preserves_upstream_and_direct_translate_with_settings_hook(self):
        with tempfile.TemporaryDirectory(prefix='gboard-khmer-overlay-') as tmp:
            dest = Path(tmp) / 'source'
            subprocess.run([sys.executable, str(BASE / 'apply_overlay.py'), str(dest)], check=True,
                           stdout=subprocess.DEVNULL)
            registry = (dest / 'patches/src/main/kotlin/dev/jason/gboardpatches/patches/gboard/registry/GboardPatchRegistry.kt').read_text()
            self.assertIn('gboardDirectGoogleTranslatePatch,', registry)
            self.assertIn('gboardKhmerlishPatch,', registry)
            self.assertIn('version = 4.0.0-khmerlish-dev.1', (dest / 'gradle.properties').read_text())
            group = (dest / 'extensions/extension/src/main/java/dev/jason/gboardpatches/extension/keyboard/GboardKeyboardToolsSettingsGroupFeature.java').read_text()
            self.assertIn('new GboardCalculatorSettingsFeature(context)', group)
            patch = (dest / 'patches/src/main/kotlin/dev/jason/gboardpatches/patches/gboard/features/khmerlish/GboardKhmerlishPatch.kt').read_text()
            self.assertIn('KHMERLISH_ADD_SETTINGS', patch)
            self.assertIn('GboardPatchesSettingsFeatureRegistry;', patch)
            ui = (dest / 'extensions/extension/src/main/java/dev/jason/gboardpatches/extension/khmerlish/KhmerlishSettingsFeature.java').read_text()
            self.assertIn('features.add(new KhmerlishSettingsFeature(context))', ui)
            runtime = (dest / 'extensions/extension/src/main/java/dev/jason/gboardpatches/extension/khmerlish/KhmerlishRuntime.java').read_text()
            for guard in ('TYPE_TEXT_VARIATION_PASSWORD', 'TYPE_TEXT_VARIATION_EMAIL_ADDRESS',
                          'TYPE_TEXT_VARIATION_URI', 'IME_FLAG_NO_PERSONALIZED_LEARNING',
                          'getSurroundingText', 'getCurrentInputConnection', 'getSelectedText'):
                self.assertIn(guard, runtime)
            for network in ('HttpURLConnection', 'OkHttp', 'java.net.', 'android.util.Log'):
                self.assertNotIn(network, runtime)
            self.assertTrue((dest / 'patches/src/main/resources/gboard-khmer/dictionary.tsv').exists())
            self.assertTrue((dest / 'extensions/extension/src/main/java/dev/jason/gboardpatches/extension/directtranslate/GtxClient.java').exists())


if __name__ == '__main__':
    unittest.main()
