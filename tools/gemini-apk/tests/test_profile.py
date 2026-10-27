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
