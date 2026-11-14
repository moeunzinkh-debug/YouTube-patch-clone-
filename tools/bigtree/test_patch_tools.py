#!/usr/bin/env python3
import tempfile, unittest
from pathlib import Path
from prepare_build import prepare
from verify_bundle import verify_listing
from verify_patched import MARKERS, verify_injection

class BigTreeToolsTest(unittest.TestCase):
    def test_isolated_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'build'
            prepare(dest)
            files = list((dest / 'patches/src/main/kotlin').rglob('*.kt'))
            self.assertEqual([p.name for p in files], ['BigTreePatches.kt'])
            self.assertIn('bigtree-patches', (dest / 'settings.gradle.kts').read_text())
            with self.assertRaises(ValueError): prepare(dest)

    def test_listing_is_exact_and_disabled_by_default(self):
        text = ''.join(
            f'Name: {name}\nEnabled: false\nCompatible packages:\n  Package name: com.app.bigtree\n  Compatible versions:\n    1.14\n'
            for name in ('Snap Media', 'Translation to English')
        )
        verify_listing(text)
        for bad in (text.replace('Enabled: false', 'Enabled: true', 1), text + 'Name: Extra\nEnabled: false\n',
                    text.replace('com.app.bigtree', 'com.example.bad', 1)):
            with self.assertRaises(ValueError): verify_listing(bad)

    def test_snap_uses_layered_capture_without_page_control_clicks(self):
        source = (Path(__file__).parent / 'project/patches/src/main/kotlin/app/morphe/patches/bigtree/BigTreePatches.kt').read_text()
        for evidence in ('XMLHttpRequest.prototype.open', 'PerformanceObserver', 'iframe,frame',
                         'shouldInterceptRequest', 'morphe-snap-media-url', 'nativePlayerOpen',
                         'morphe-snap-player-json', 'Android.saveFile', 'Video found',
                         'raw saving would corrupt it', 'data.clearKeys', 'data.bbtsKey',
                         "walk(data.backup,'backup','')", "nativeOnly=/\\/vplay\\//",
                         "true,'native-player'", 'playerTitle', 'morpheSnapSpin',
                         "heading.textContent='Video found'", "download.textContent='Download'",
                         "if(snappedUrl){showReadyCard();return;}startSnap()", 'finishBlocked(playerBlockReason)',
                         "heading.textContent='Direct download unavailable'", "retry.textContent='Retry'"):
            self.assertIn(evidence, source)
        for unsafe in ('geometricDownloadControl', 'downloadControl()', 'control.click()',
                       'openAppDownload', 'morphe-snap-manifest-url'):
            self.assertNotIn(unsafe, source)

    def test_independent_injection_shapes(self):
        original = [('invoke-super', 'v0'), *([('nop', '')] * 20), ('return-void', '')]
        def block(marker):
            return [('const-string', 'v0, "'+marker+'"'), ('const/4', 'v1, 0x0'),
                    ('invoke-virtual', '{p1,v0,v1}, Landroid/webkit/WebView;->evaluateJavascript(Ljava/lang/String;Landroid/webkit/ValueCallback;)V')]
        for modes in (['snap'], ['translation'], ['snap', 'translation']):
            patched = original[:1]
            # addInstructions at index 1 means the last applied patch is first.
            for mode in modes: patched[1:1] = block(MARKERS[mode])
            patched += original[1:]
            verify_injection(original, patched, modes)
        bad = original[:1] + block(MARKERS['snap']) + [('nop', 'changed')] + original[2:]
        with self.assertRaises(ValueError): verify_injection(original, bad, ['snap'])

if __name__ == '__main__': unittest.main()
