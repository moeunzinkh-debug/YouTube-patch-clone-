#!/usr/bin/env python3
import unittest

from inspect_license import ENTRYPOINTS, redact_instruction


class LicenseInspectionTest(unittest.TestCase):
    def test_redacts_string_constants_and_secrets(self):
        self.assertEqual(redact_instruction('const-string', 'v0, "secret value"'), '<redacted>')
        self.assertEqual(redact_instruction('invoke-static', 'https://example.com/token'), '<redacted>')
        self.assertEqual(redact_instruction('return-void', ''), '')
        self.assertEqual(redact_instruction('const/4', 'v0, 1'), 'v0, 1')

    def test_entrypoint_match_is_specific(self):
        self.assertIsNotNone(ENTRYPOINTS.search('v0, Lcom/pairip/licensecheck/LicenseClient;->checkLicense(Landroid/content/Context;)V'))
        self.assertIsNotNone(ENTRYPOINTS.search('v0, Lcom/pairip/licensecheck/LicenseClient;->initializeLicenseCheck()V'))
        self.assertIsNone(ENTRYPOINTS.search('Lcom/tencent/liteav/sdk/common/LicenseChecker;->checkLicense()V'))
        self.assertIsNone(ENTRYPOINTS.search('Lcom/pairip/licensecheck/LicenseClient;->checkLicenseInternal()V'))


if __name__ == '__main__':
    unittest.main()
