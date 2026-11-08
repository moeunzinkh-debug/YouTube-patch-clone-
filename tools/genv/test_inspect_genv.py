import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import inspect_genv as inspection


class InspectionGuards(unittest.TestCase):
    def test_safe_identifiers_and_redaction(self):
        self.assertTrue(inspection.safe_identifier('Lcom/pairip/licensecheck/LicenseClient;'))
        for value in ('', 'https://example.org/license', 'password=abc', 'user@example.org', 'a'*60, 'x\ny'):
            self.assertFalse(inspection.safe_identifier(value), value)
        self.assertEqual('<redacted>', inspection.safe_operand('const-string', 'license'))
        self.assertEqual('<redacted>', inspection.safe_operand('invoke-static', 'https://example.org/secret'))

    def test_asset_pinned_by_name_size_and_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / 'GenV_3.7.2.apk'
            file.write_bytes(b'test')
            with self.assertRaises(ValueError): inspection.check_asset(file)
            with patch.object(inspection, 'ASSET_SIZE', 4), patch.object(inspection, 'ASSET_SHA256', inspection.sha256(file)):
                inspection.check_asset(file)
                other = file.with_name('other.apk'); other.write_bytes(b'test')
                with self.assertRaises(ValueError): inspection.check_asset(other)

    def test_dex_names(self):
        for name in ('classes.dex', 'classes2.dex', 'classes10.dex'):
            self.assertIsNotNone(inspection.DEX_NAME.fullmatch(name))
        for name in ('classes1.dex', '../classes.dex', 'classes0.dex', 'assets/classes2.dex'):
            self.assertIsNone(inspection.DEX_NAME.fullmatch(name))


if __name__ == '__main__': unittest.main()
