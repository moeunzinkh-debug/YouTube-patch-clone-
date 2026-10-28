import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]


class ProfileEvidence(unittest.TestCase):
    def test_profile_matches_inspected_input(self):
        evidence = json.loads((ROOT / 'docs/gemini-apk-inspection.json').read_text())
        profile = (ROOT / 'tools/gemini-apk/overlay/Gemini_1_0_995038376.kt').read_text()
        for value in (evidence['version'], evidence['version_code'], evidence['sha256']):
            self.assertIn(value, profile)
        self.assertIn(f"expectedMatches = {evidence['redirect_match_count']}", profile)
        self.assertEqual(evidence['redirect_match_count'], 4)

    def test_actual_patch_report(self):
        report = json.loads((ROOT / 'bundles/gemini/patch-result.json').read_text())
        self.assertEqual(report['failedPatches'], [])
        self.assertEqual(len(report['appliedPatches']), 2)
        self.assertTrue(all(step['success'] for step in report['patchingSteps']))

    def test_google_profile_uses_discovered_methods(self):
        evidence = (ROOT / 'docs/google-target-hooks.txt').read_text()
        profile = (ROOT / 'tools/gemini-apk/overlay/Google_17_6_59.kt').read_text()
        for signature in ('Laezk;->f(Leksz;Lfkya;)Ljava/lang/Object;',
                          'Lakpt;->k(Lfkya;)Ljava/lang/Object;',
                          'Ldgtr;->b()Ljava/lang/String;', 'Ldgtn;->b()Z',
                          'Lcdii;->b(Landroid/content/Context;I)I'):
            self.assertIn(signature, evidence)
        self.assertIn('301698282', profile)
        self.assertIn('17.6.59.ve.arm64', profile)
        self.assertIn('"observedRegisters" to 12', profile)

    def test_google_patch_execution_and_microg_permission(self):
        report = json.loads((ROOT / 'bundles/gemini/google-patch-result.json').read_text())
        self.assertEqual(report['failedPatches'], [])
        self.assertEqual(len(report['appliedPatches']), 9)
        self.assertTrue(all(step['success'] for step in report['patchingSteps']))
        result = json.loads((ROOT / 'bundles/gemini/google-validation.json').read_text())
        self.assertEqual(result['microg_permission'], 'app.revanced.android.gms.EXTENDED_ACCESS')
        self.assertFalse(result['device_runtime_tested'])

    def test_only_new_process_strategy_is_selected(self):
        report = json.loads((ROOT / 'bundles/gemini/google-patch-result.json').read_text())
        names = {p['name'] for p in report['appliedPatches']}
        self.assertIn('Google clone process identity (experimental)', names)
        self.assertNotIn('Process Name Spoofing for Clone Support', names)
        self.assertFalse((ROOT / 'tools/gemini-apk/overlay/ProcessNameSanitizePatch.kt').exists())
        prep = (ROOT / 'tools/gemini-apk/prepare_build.py').read_text()
        self.assertIn('legacy.unlink()', prep)
