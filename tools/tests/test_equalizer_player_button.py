"""Static layout/wiring checks, not a replacement for device screenshot tests."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
ANDROID = '{http://schemas.android.com/apk/res/android}'


class EqualizerPlayerButton(unittest.TestCase):
    def test_button_participates_in_top_control_chain(self):
        path = ROOT / 'patches/src/main/resources/equalizer/host/layout/youtube_controls_layout.xml'
        children = list(ET.parse(path).getroot())
        self.assertEqual(len(children), 1)
        attrs = children[0].attrib
        self.assertEqual(attrs[ANDROID+'id'], '@+id/morphe_equalizer_button')
        self.assertEqual(attrs[ANDROID+'layout_toStartOf'], '@id/music_app_deeplink_button')
        self.assertEqual(attrs[ANDROID+'layout_width'], '@dimen/controls_overlay_action_button_size')
        self.assertEqual(attrs[ANDROID+'layout_height'], '@dimen/controls_overlay_action_button_size')
        self.assertEqual(attrs[ANDROID+'visibility'], 'gone')
        for key in ('translationX', 'translationY', 'layout_alignParentEnd', 'layout_alignParentRight'):
            self.assertNotIn(ANDROID+key, attrs)
        self.assertIn(ANDROID+'contentDescription', attrs)

    def test_preference_and_shortcut_share_one_dialog(self):
        files = [ROOT / 'extensions/youtube/src/main/java/app/morphe/extension/youtube' / name
                 for name in ('settings/preference/EqualizerPreference.java',
                              'videoplayer/EqualizerPlayerButton.java')]
        for path in files:
            self.assertIn('EqualizerDialog.show(', path.read_text())
        dialog = (ROOT / 'extensions/youtube/src/main/java/app/morphe/extension/youtube/patches/EqualizerDialog.java').read_text()
        self.assertIn('current != null && current.isShowing()', dialog)
        self.assertIn('WeakReference<AlertDialog>', dialog)

    def test_visibility_uses_native_controller_and_setting(self):
        source = (ROOT / 'extensions/youtube/src/main/java/app/morphe/extension/youtube/videoplayer/EqualizerPlayerButton.java').read_text()
        self.assertIn('new LegacyPlayerControlButton(', source)
        self.assertIn('incrementUpperButtonCount()', source)
        self.assertIn('Settings.EQUALIZER_PLAYER_BUTTON', source)
        patch = (ROOT / 'patches/src/main/kotlin/app/morphe/patches/youtube/video/audio/EqualizerPatch.kt').read_text()
        self.assertIn('initializeTopControl(', patch)
        self.assertIn('addTopControl("equalizer"', patch)
        self.assertIn('legacyPlayerControlsResourcePatch', patch)

    def test_required_icons_are_valid_vectors(self):
        for suffix in ('', '_bold'):
            p = ROOT / f'patches/src/main/resources/equalizer/drawable/morphe_equalizer_button{suffix}.xml'
            self.assertEqual(ET.parse(p).getroot().tag, 'vector')


if __name__ == '__main__':
    unittest.main()
