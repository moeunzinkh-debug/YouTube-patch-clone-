#!/usr/bin/env python3
"""Offline tests for the read-only release scanner's redaction and asset pin."""
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import trace_current_release as scanner


class Instruction:
    def __init__(self, name, output):
        self.name, self.output = name, output
    def get_name(self): return self.name
    def get_output(self): return self.output


class ScanTests(unittest.TestCase):
    def test_redacts_strings_except_exact_safe_anchors(self):
        self.assertEqual(scanner.sanitize(Instruction('const-string', 'v2, "is_premium"'))['value'], 'v2,is_premium')
        for value in ('secret_password', 'https://private.example/premium', 'premiumWithPrivateSuffix'):
            with self.subTest(value=value):
                self.assertEqual(scanner.sanitize(Instruction('const-string', f'v4, "{value}"'))['value'], 'v4,<redacted>')
        self.assertEqual(scanner.sanitize(Instruction('invoke-static', 'v0, Lfoo;->getPremium()Z'))['value'], 'v0,Lfoo;->getPremium()Z')

    def test_owner_scope_excludes_google_library(self):
        self.assertTrue(scanner.candidate_owner('Lcom/spaceship/screen/translate/Main;'))
        self.assertTrue(scanner.candidate_owner('Lxyz12;'))
        self.assertFalse(scanner.candidate_owner('Lcom/google/android/gms/Foo;'))

    def test_asset_must_match_exact_size_hash_and_zip(self):
        with tempfile.TemporaryDirectory() as folder:
            fake = Path(folder, 'fixture.bin')
            with zipfile.ZipFile(fake, 'w') as z: z.writestr('not-an-apk.txt', 'synthetic')
            h = hashlib.sha256(fake.read_bytes()).hexdigest()
            with patch.object(scanner, 'SIZE', fake.stat().st_size), patch.object(scanner, 'SHA256', h):
                scanner.verify(fake)
                fake.write_bytes(fake.read_bytes() + b'changed')
                with self.assertRaises(ValueError): scanner.verify(fake)


if __name__ == '__main__': unittest.main()
