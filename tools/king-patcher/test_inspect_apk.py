#!/usr/bin/env python3
"""Local guard tests for read-only King-Patcher inspection."""
from pathlib import Path
import tempfile
import unittest

import inspect_apk as inspection


class InspectionTests(unittest.TestCase):
    def test_filters_urls_and_credential_like_text(self):
        self.assertTrue(inspection.safe('APK without License Verification'))
        self.assertFalse(inspection.safe('https://example.org/license'))
        self.assertFalse(inspection.safe('license token value'))
        self.assertFalse(inspection.safe('A' * 60))
        self.assertFalse(inspection.safe('line\nbreak'))

    def test_resource_candidates_and_methods_are_bounded_and_linked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            values = root / 'res/values'
            values.mkdir(parents=True)
            (values / 'public.xml').write_text(
                '<resources><public type="string" name="license_menu" id="0x7f120001"/>'
                '<public type="string" name="ignored" id="0x7f120002"/></resources>')
            (values / 'strings.xml').write_text(
                '<resources><string name="license_menu">APK without License Verification</string>'
                '<string name="ignored">https://example.org/license</string></resources>')
            smali = root / 'smali/org/example/Menu.smali'
            smali.parent.mkdir(parents=True)
            smali.write_text('.class public Lorg/example/Menu;\n.method public show()V\n'
                             '    const v0, 0x7f120001\n.end method\n')
            result = inspection.resource_inventory(root)
            self.assertTrue(result['available'])
            self.assertEqual(1, result['matching_label_count'])
            self.assertEqual('license_menu', result['screen_candidates'][0]['name'])
            references = inspection.smali_references(root, result['screen_candidates'])
            self.assertEqual([{'class': 'Lorg/example/Menu;', 'method': 'show()V',
                               'resource': 'license_menu'}], references['references'])

    def test_missing_resources_and_wrong_asset_fail_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertFalse(inspection.resource_inventory(root)['available'])
            self.assertEqual([], inspection.smali_references(root, [])['references'])
            wrong = root / inspection.ASSET_NAME
            wrong.write_bytes(b'not the user-provided APK')
            with self.assertRaises(ValueError):
                inspection.check_asset(wrong)


if __name__ == '__main__':
    unittest.main(verbosity=2)
