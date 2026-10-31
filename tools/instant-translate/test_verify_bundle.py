#!/usr/bin/env python3
"""Fast, offline checks for standalone-bundle validation; no app APK involved."""
import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

import verify_bundle as verifier


class VerifyBundleTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bundle = Path(self.temp.name) / 'bundle.mpp'
        self.entries = {
            'META-INF/MANIFEST.MF': ('Manifest-Version: 1.0\n'
                f'Version: {verifier.VERSION}\nPatcher-Version: 2.0.0\n'
                'Name: Instant Translate patches (experimental)\n').encode(),
            'classes.dex': b'dex',
            'extensions/instanttranslate.mpe': (b'dex SeaLionClient '
                b'https://api.sea-lion.ai/v1/ aisingapore/Gemma-SEA-LION-v4-27B-IT'),
        }
        for name, (filename, _) in verifier.PATCHES.items():
            self.entries['app/morphe/patches/instanttranslate/' + filename] = name.encode()

    def write_bundle(self):
        with zipfile.ZipFile(self.bundle, 'w') as out:
            for name, data in self.entries.items(): out.writestr(name, data)
        checksum = hashlib.sha256(self.bundle.read_bytes()).hexdigest()
        self.bundle.with_name('bundle.mpp.sha256').write_text(f'{checksum}  bundle.mpp\n')

    def test_rejects_old_google_client_endpoint_and_selector(self):
        for forbidden in (b'GtxClient', b'translate.googleapis.com', b'Google fallback'):
            with self.subTest(forbidden=forbidden):
                key = 'extensions/instanttranslate.mpe'
                old = self.entries[key]
                self.entries[key] = old + forbidden
                self.write_bundle()
                with self.assertRaises(ValueError): verifier.verify_bundle(self.bundle)
                self.entries[key] = old
        self.entries['classes.dex'] += b'Translation fallback (Google, experimental)'
        self.write_bundle()
        with self.assertRaises(ValueError): verifier.verify_bundle(self.bundle)

    def test_requires_sealion_defaults_and_valid_checksum(self):
        self.write_bundle()
        self.assertEqual(verifier.verify_bundle(self.bundle)['version'], verifier.VERSION)
        self.bundle.with_name('bundle.mpp.sha256').write_text('0' * 64 + '  bundle.mpp\n')
        with self.assertRaises(ValueError): verifier.verify_bundle(self.bundle)
        self.entries['extensions/instanttranslate.mpe'] = b'dex'
        self.write_bundle()
        with self.assertRaises(ValueError): verifier.verify_bundle(self.bundle)

    def test_rejects_unrelated_app_classes(self):
        self.entries['app/morphe/patches/unrelated/Patch.class'] = b'not instant translate'
        self.write_bundle()
        with self.assertRaises(ValueError): verifier.verify_bundle(self.bundle)

    def test_listing_is_opt_in_and_exactly_expected(self):
        def card(name, enabled='false', package=verifier.PACKAGE, versions=None):
            versions = versions or verifier.PATCHES.get(name, ('', (verifier.VERSION_NAME,)))[1]
            targets = ''.join(f'    {version}\n' for version in versions)
            return f'Name: {name}\nEnabled: {enabled}\n  Package name: {package}\n{targets}'
        listing = ''.join(card(name) for name in verifier.PATCHES)
        verifier.verify_listing(listing)
        for bad in (listing.replace('Enabled: false', 'Enabled: true', 1),
                    listing + card('Google fallback'),
                    listing.replace(verifier.PACKAGE, 'other.package', 1),
                    listing.replace(verifier.VERSION_NAME, 'v0', 1)):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError): verifier.verify_listing(bad)


if __name__ == '__main__': unittest.main()
