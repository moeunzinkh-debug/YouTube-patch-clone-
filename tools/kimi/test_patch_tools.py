#!/usr/bin/env python3
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from prepare_build import prepare
from verify_bundle import NAME, verify_listing
from verify_patched import ATTACH, CHECK, INITIALIZE, PROVIDER, TENCENT, verify_methods, verify_report


class KimiToolTests(unittest.TestCase):
    def test_prepare_isolated_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'project'
            prepare(dest)
            patch_dir = dest / 'patches/src/main/kotlin/app/morphe/patches/kimi'
            self.assertEqual([p.name for p in patch_dir.glob('*.kt')], ['RemoveLicenseCheckPatch.kt'])
            self.assertFalse((dest / 'patches/src/main/kotlin/app/morphe/patches/youtube').exists())
            self.assertIn('kimi-patches', (dest / 'settings.gradle.kts').read_text())
            with self.assertRaises(ValueError):
                prepare(dest)

    def test_exact_listing(self):
        text = ('Name: Remove license check\nEnabled: true\nCompatible packages:\n'
                '  Package name: com.moonshot.kimichat\n  Compatible versions:\n    3.1.5\n')
        verify_listing(text)
        for altered in (text.replace('Enabled: true', 'Enabled: false'),
                        text.replace('com.moonshot.kimichat', 'com.example.bad'),
                        text + '\nName: Extra\nEnabled: true\n'):
            with self.assertRaises(ValueError):
                verify_listing(altered)

    def test_patch_report_cannot_hide_failed_steps(self):
        with tempfile.TemporaryDirectory() as tmp:
            output, report = Path(tmp) / 'out.apk', Path(tmp) / 'result.json'
            with zipfile.ZipFile(output, 'w') as archive:
                archive.writestr('classes.dex', b'fixture')
            data = {'packageName': 'com.moonshot.kimichat', 'packageVersion': '3.1.5', 'success': True,
                    'failedPatches': [], 'appliedPatches': [NAME], 'outputPath': str(output),
                    'stepResults': [{'step': 'PATCHING', 'success': True}, {'step': 'REBUILDING', 'success': True}]}
            report.write_text(json.dumps(data))
            verify_report(report, output)
            for changed in ({'failedPatches': [{'name': NAME}]}, {'appliedPatches': []}, {'success': False},
                            {'stepResults': [{'step': 'PATCHING', 'success': True}]}):
                report.write_text(json.dumps(data | changed))
                with self.assertRaises(ValueError):
                    verify_report(report, output)

    def test_exact_two_early_returns_and_untouched_other_methods(self):
        original = {
            CHECK: [('const-string', 'v0')] + [('nop', '')] * 15,
            INITIALIZE: [('sget-object', 'v0')] + [('nop', '')] * 28,
            ATTACH: [('invoke-static', 'Lcom/pairip/licensecheck/LicenseClient;->checkLicense(Landroid/content/Context;)V')],
            PROVIDER: [('return', 'v0')], TENCENT: [('return', 'v0')],
        }
        patched = {key: list(value) for key, value in original.items()}
        for key in (CHECK, INITIALIZE):
            patched[key].insert(0, ('return-void', ''))
        verify_methods(original, patched)
        for key in (CHECK, INITIALIZE, ATTACH, PROVIDER, TENCENT):
            altered = {k: list(value) for k, value in patched.items()}
            altered[key][0] = ('nop', '')
            with self.assertRaises(ValueError):
                verify_methods(original, altered)


if __name__ == '__main__':
    unittest.main()
