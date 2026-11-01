"""Regression tests for the scoped YouTube 21.30.216 update (no APK required)."""
import importlib.util
import json
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import verify_youtube_update as verify  # noqa: E402


class YouTubeUpdate(unittest.TestCase):
    def test_compiled_source_targets_keep_correct_stability_and_sdk(self):
        path = ROOT / 'patches/src/main/kotlin/app/morphe/patches/youtube/shared/Constants.kt'
        blocks = re.findall(r'AppTarget\((.*?)\n\s*\)', path.read_text(), flags=re.S)
        observed = []
        for block in blocks:
            version = re.search(r'version\s*=\s*"([^"]+)"', block).group(1)
            sdk = int(re.search(r'minSdk\s*=\s*(\d+)', block).group(1))
            flag = re.search(r'isExperimental\s*=\s*(true|false)', block)
            observed.append((version, sdk, flag is not None and flag.group(1) == 'true'))
        self.assertEqual(observed, verify.TARGETS)
        stable = [(v, sdk) for v, sdk, experimental in observed if not experimental]
        self.assertEqual(stable[0], ('21.30.216', 29))
        self.assertEqual(next(v for v, sdk in stable if sdk <= 28), '21.23.492')

    def test_all_four_new_upstream_selectors_have_real_source_and_dependencies(self):
        root = ROOT / 'patches/src/main/kotlin/app/morphe/patches/youtube'
        selectors = {
            'Download post images': 'interaction/postimages/PostImageDownloadPatch.kt',
            'Translate posts': 'interaction/posttranslate/PostTranslatePatch.kt',
            'Search comments': 'interaction/searchcomments/SearchCommentsPatch.kt',
            'Niconico comments': 'layout/niconicocomments/NiconicoCommentsPatch.kt',
        }
        for name, path in selectors.items():
            self.assertIn(f'name = "{name}"', (root / path).read_text(), name)
        java = ROOT / 'extensions/youtube/src/main/java/app/morphe/extension/youtube'
        for path in ('patches/PostImageDownloadPatch.java', 'patches/PostTranslatePatch.java',
                     'patches/components/CommentsSearchFilter.java',
                     'niconicocomments/NiconicoCommentsController.java'):
            self.assertTrue((java / path).is_file(), path)
        for path in ('niconicocommentsbutton', 'searchcomments'):
            self.assertTrue((ROOT / 'patches/src/main/resources' / path).is_dir(), path)

    def test_existing_khmer_strings_are_preserved(self):
        fixture = json.loads((ROOT / 'tools/tests/data/youtube-khmer-strings.json').read_text())
        root = ET.parse(ROOT / 'patches/src/main/resources/addresources/values-km-rKH/youtube/strings.xml').getroot()
        actual = {e.attrib['name']: ''.join(e.itertext()) for e in root if e.tag == 'string'}
        for name, value in fixture.items():
            self.assertEqual(actual.get(name), value, name)

    def test_translate_posts_backports_legacy_android_fix(self):
        base = ROOT / 'patches/src/main/kotlin/app/morphe/patches/youtube/interaction/posttranslate'
        kotlin = (base / 'PostTranslatePatch.kt').read_text()
        java = (ROOT / 'extensions/youtube/src/main/java/app/morphe/extension/youtube/patches/PostTranslatePatch.java').read_text()
        for injected in ('patch_getMountedContents', 'EXTENSION_COMPONENT_HOST_INTERFACE',
                         'EXTENSION_TEXT_DRAWABLE_INTERFACE'):
            self.assertIn(injected, kotlin)
        self.assertIn('getReference<FieldReference>()', kotlin)
        self.assertIn('getReference<MethodReference>()', kotlin)
        self.assertIn('interface ComponentHostInterface', java)
        self.assertIn('interface TextDrawableInterface', java)
        self.assertNotIn('getDeclaredFields()', java)

    def test_readme_catalog_groups_match_all_requested_selectors(self):
        spec = importlib.util.spec_from_file_location('patch_catalog', ROOT / 'tools/generate-patch-catalog.py')
        catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(catalog)
        grouped = [name for _, names in catalog.GROUPS for name in names]
        self.assertEqual(len(grouped), len(set(grouped)), 'duplicate group member')
        self.assertEqual(set(grouped), verify.expected_names())
        self.assertEqual(set(catalog.NEW_IN_V20), verify.NEW_PATCHES)

    def test_custom_voice_picker_uses_new_shared_slider_api(self):
        source = (ROOT / 'extensions/youtube/src/main/java/app/morphe/extension/youtube/patches/voiceovertranslation/VOTBottomSheet.java').read_text()
        self.assertIn('SheetBottomDialog.createSliderRow(context,\n                str("morphe_vot_voice_speed_title")', source)
        self.assertIn('SheetBottomDialog.createSliderRow(context,\n                str("morphe_vot_voice_pitch_title")', source)
        self.assertIn('KhmerTtsClient.VOICE_ID', source)
        self.assertNotIn('makeSliderRow(', source)
        self.assertNotIn('makeTitle(', source)


class CatalogValidator(unittest.TestCase):
    @staticmethod
    def catalog():
        generic = {'Change installer source', 'Clone app', 'Disable Play Store updates',
                   'Override certificate pinning', 'Spoof signature'}
        targets = [{'version': v, 'minSdk': sdk, 'isExperimental': experimental}
                   for v, sdk, experimental in verify.TARGETS]
        return {'version': verify.VERSION,
                'patches': [{'name': name, 'compatiblePackages': [] if name in generic else
                             [{'packageName': verify.PACKAGE, 'targets': targets.copy()}]}
                            for name in sorted(verify.expected_names())]}

    def test_accepts_expected_selector_set(self):
        verify.verify_catalog(self.catalog())

    def test_rejects_missing_requested_selector(self):
        data = self.catalog()
        data['patches'] = [p for p in data['patches'] if p['name'] != 'Search comments']
        with self.assertRaises(ValueError):
            verify.verify_catalog(data)

    def test_rejects_wrong_recommendation(self):
        data = self.catalog()
        target = data['patches'][0]['compatiblePackages'][0]['targets'][2]
        target['isExperimental'] = True
        with self.assertRaises(ValueError):
            verify.verify_catalog(data)

    def test_rejects_other_app(self):
        data = self.catalog()
        data['patches'][0]['compatiblePackages'][0]['packageName'] = 'com.google.android.apps.youtube.music'
        with self.assertRaises(ValueError):
            verify.verify_catalog(data)


if __name__ == '__main__':
    unittest.main()
