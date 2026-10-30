#!/usr/bin/env python3
"""Tests for the translation APK inspector's safety and pinning guards."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import inspect_apk as inspector


class InspectorTests(unittest.TestCase):
    def test_no_urls_or_secrets_in_sample(self):
        self.assertTrue(inspector.safe_sample('Translation failed. Try again.'))
        for value in ('https://example.com/?key=secret', 'api_key is 123', 'user@example.com',
                      'access_token: private', 'x' * 100, 'line\nbreak'):
            self.assertFalse(inspector.safe_sample(value), value)

    def test_host_allowlist_never_returns_urls_paths_or_credentials(self):
        self.assertEqual(inspector.allowed_host('https://translate.googleapis.com/path?key=secret'), 'translate.googleapis.com')
        for url in ('https://untrusted.example/translate', 'https://translate.googleapis.com.evil.example/',
                    'ftp://translate.googleapis.com/', 'not a url', 'https://[bad'):
            self.assertIsNone(inspector.allowed_host(url))

    def test_asset_pin_checks_size_hash_and_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / 'fake.apk'
            file.write_bytes(b'not-an-apk')
            with self.assertRaises(ValueError):
                inspector.verify_asset(file)
            with patch.object(inspector, 'EXPECTED_SIZE', file.stat().st_size), patch.object(inspector, 'EXPECTED_SHA256', inspector.digest_file(file)):
                with self.assertRaisesRegex(ValueError, 'not an APK'):
                    inspector.verify_asset(file)

    def test_feature_patterns_distinguish_failure_from_names(self):
        self.assertTrue(inspector.CATEGORIES['translation'].search('TranslationEngine'))
        self.assertTrue(inspector.CATEGORIES['translation_errors'].search('Translation failed'))
        self.assertFalse(inspector.CATEGORIES['translation_errors'].search('TranslationEngine'))
        self.assertTrue(inspector.CATEGORIES['network_errors'].search('Network connection error'))


if __name__ == '__main__':
    unittest.main()
