#!/usr/bin/env python3
"""Offline tests for the upstream subset preparation and selector verification."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import prepare_build
import verify_bundle
import verify_patching


class TelegramSubsetTest(unittest.TestCase):
    def test_verbatim_upstream_and_metadata(self):
        manifest = prepare_build.verify_vendor()
        self.assertEqual(len(manifest['files']), 36)
        info = verify_bundle.metadata()
        self.assertEqual(len(info['patches']), 15)

    def test_source_preparation_is_isolated_and_preserves_patch_files(self):
        with tempfile.TemporaryDirectory(prefix='telegram-subset-test-') as tmp:
            dest = Path(tmp) / 'project'
            prepare_build.prepare(dest)
            vendor = prepare_build.VENDOR
            root = 'patches/src/main/kotlin/app/template/patches/telegram'
            originals = {p.relative_to(vendor) for p in (vendor / root).rglob('*.kt')}
            self.assertEqual(len(originals), 17)
            for rel in originals:
                self.assertEqual((dest / rel).read_bytes(), (vendor / rel).read_bytes(), str(rel))
            constants = (dest / 'patches/src/main/kotlin/app/template/patches/shared/Constants.kt').read_text()
            self.assertIn('org.telegram.messenger', constants)
            self.assertNotIn('THE_ATHLETIC_COMPATIBILITY', constants)
            for rel, (symbol, kind) in prepare_build.DEPENDENCY_HEADERS.items():
                source = (vendor / rel).read_text()
                generated = (dest / rel).read_text()
                self.assertEqual(generated, prepare_build.hide_generic_selector(source, symbol, kind))
                self.assertIn(f'val {symbol} = {kind}(default = false) {{', generated)
            self.assertEqual(len(list((dest / 'extensions/extension/src/main/java').rglob('*.java'))), 2)
            with self.assertRaises(ValueError):
                prepare_build.prepare(dest)

    def test_dependency_header_rejects_changed_source(self):
        with self.assertRaises(ValueError):
            prepare_build.hide_generic_selector('not upstream Kotlin', 'missingPatch', 'bytecodePatch')

    def test_patch_report_rejects_partial_success(self):
        with tempfile.TemporaryDirectory(prefix='telegram-report-test-') as tmp:
            path = Path(tmp) / 'report.json'
            report = {'packageName': 'org.telegram.messenger', 'packageVersion': '12.10.1',
                      'patchingSteps': [{'step': 'PATCHING', 'success': True}],
                      'appliedPatches': [{'name': 'Remove ads'}], 'failedPatches': []}
            path.write_text(json.dumps(report))
            verify_patching.verify_report(path, {'Remove ads'})
            report['failedPatches'] = [{'name': 'Remove ads'}]
            path.write_text(json.dumps(report))
            with self.assertRaises(ValueError):
                verify_patching.verify_report(path, {'Remove ads'})

    def test_listing_accepts_telegram_only_and_rejects_extra(self):
        source = verify_bundle.metadata()
        blocks = []
        for patch_data in source['patches']:
            block = ['Name: ' + patch_data['name'], 'Description: fixture', 'Enabled: true', 'Compatible packages:']
            for compatible in patch_data['compatiblePackages']:
                version, code = verify_bundle.TARGETS[compatible['packageName']]
                block += ['\tPackage name: ' + compatible['packageName'], '\tCompatible versions:',
                          '\t\t' + version, '\tVersion codes:', f'\t\t{version}: ARM64_V8A={code}']
            blocks.append('\n'.join(block))
        listing = '\n\n'.join(blocks)
        verify_bundle.verify_listing(listing, source)
        with self.assertRaises(ValueError):
            verify_bundle.verify_listing(listing + '\n\nName: Unrelated\nEnabled: true', source)
        with self.assertRaises(ValueError):
            verify_bundle.verify_listing(listing.replace('Enabled: true', 'Enabled: false', 1), source)
        with self.assertRaises(ValueError):
            verify_bundle.verify_listing(listing.replace('org.telegram.messenger.web', 'com.example.bad', 1), source)


if __name__ == '__main__':
    unittest.main()
