"""Offline provider configuration/wiring checks. No credentials or network required."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
JAVA = ROOT / 'extensions/youtube/src/main/java/app/morphe/extension/youtube'


class SeaLionProvider(unittest.TestCase):
    def setUp(self):
        self.source = (JAVA / 'patches/voiceovertranslation/TranscriptTranslator.java').read_text()

    def test_provider_array_alignment(self):
        xml = ET.parse(ROOT / 'patches/src/main/resources/addresources/values/youtube/arrays.xml').getroot()
        entries = [x.text for x in xml.find("string-array[@name='morphe_vot_translation_service_entries']")]
        values = [x.text for x in xml.find("string-array[@name='morphe_vot_translation_service_entry_values']")]
        self.assertEqual(len(entries), len(values))
        self.assertEqual(len(values), len(set(values)))
        self.assertEqual(entries[values.index('sealion')], '@string/morphe_vot_service_sealion')
        self.assertTrue({'google', 'openrouter', 'mymemory', 'sealion'}.issubset(values))

    def test_exact_endpoint_model_and_separate_credentials(self):
        self.assertIn('"https://api.sea-lion.ai/v1/chat/completions"', self.source)
        self.assertIn('"aisingapore/Gemma-SEA-LION-v4-27B-IT"', self.source)
        self.assertIn('seaLion ? Settings.VOT_SEALION_API_KEY : Settings.VOT_OPENROUTER_API_KEY', self.source)
        self.assertIn('"Authorization", "Bearer " + apiKey', self.source)
        self.assertIn('conn.setInstanceFollowRedirects(false)', self.source)
        settings = (JAVA / 'settings/Settings.java').read_text()
        self.assertIn('new StringSetting("morphe_vot_sealion_api_key", "",', settings)

    def test_no_openrouter_routing_for_sealion(self):
        self.assertIn('} else {\n            body.put("provider", provider);', self.source)
        self.assertIn('body.put("messages", new JSONArray().put(new JSONObject()', self.source)
        self.assertIn('conn.disconnect()', self.source)

    def test_settings_and_bottom_sheet(self):
        patch = (ROOT / 'patches/src/main/kotlin/app/morphe/patches/youtube/video/voiceovertranslation/VoiceOverTranslationPatch.kt').read_text()
        self.assertIn('TextPreference("morphe_vot_sealion_api_key",', patch)
        self.assertIn('InputType.TEXT_PASSWORD', patch)
        sheet = (JAVA / 'patches/voiceovertranslation/VOTBottomSheet.java').read_text()
        self.assertIn('str("morphe_vot_service_sealion")', sheet)
        self.assertIn('Settings.VOT_SEALION_API_KEY.get().trim().isEmpty()', sheet)
        self.assertIn('morphe_vot_sealion_not_configured_message', sheet)

    def test_export_warning_includes_sealion(self):
        source = (JAVA / 'patches/voiceovertranslation/VoiceOverTranslationPatch.java').read_text()
        self.assertIn('&& Settings.VOT_SEALION_API_KEY.get().trim().isEmpty()', source)
        self.assertIn('str("morphe_vot_export_provider_key_warning")', source)

    def test_failed_and_empty_streams_do_not_succeed_silently(self):
        self.assertIn('SEA-LION translation failed (HTTP ', self.source)
        self.assertIn('seaLion && chunk.has("error")', self.source)
        self.assertIn('seaLion && matched[0] == 0', self.source)
        self.assertIn('SEA-LION translation exceeded its output token limit', self.source)


if __name__ == '__main__':
    unittest.main()
