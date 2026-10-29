#!/usr/bin/env python3
"""Offline preparation, selector and report checks for the email experiment."""
import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prepare = load('email_prepare', ROOT / 'tools/telegram-email/prepare_build.py')
verify = load('email_verify', ROOT / 'tools/telegram-email/verify_bundle.py')
stable = verify.stable


def fixture_listing() -> str:
    blocks = []
    for entry in stable.metadata()['patches']:
        block = ['Name: ' + entry['name'], 'Description: fixture', 'Enabled: true', 'Compatible packages:']
        for package in entry['compatiblePackages']:
            name = package['packageName']
            version, code = stable.TARGETS[name]
            block += ['\tPackage name: ' + name, '\tCompatible versions:', '\t\t' + version,
                      '\tVersion codes:', f'\t\t{version}: ARM64_V8A={code}']
        blocks.append('\n'.join(block))
    new = ['Name: ' + verify.SELECTOR, 'Description: Server chooses the next method', 'Enabled: false',
           'Compatible packages:']
    for package in sorted(verify.PACKAGES):
        version, code = stable.TARGETS[package]
        new += ['\tPackage name: ' + package, '\tCompatible versions:', '\t\t' + version,
                '\tVersion codes:', f'\t\t{version}: ARM64_V8A={code}']
    blocks.insert(4, '\n'.join(new))
    return '\n\n'.join(blocks)


class ExperimentTest(unittest.TestCase):
    def test_isolated_overlay_and_original_integrity(self):
        with tempfile.TemporaryDirectory(prefix='tg-email-build-') as tmp:
            project = Path(tmp) / 'project'
            prepare.prepare(project)
            vendor = prepare.stable.VENDOR
            path = 'patches/src/main/kotlin/app/template/patches/telegram'
            upstream = list((vendor / path).rglob('*.kt'))
            self.assertEqual(len(upstream), 17)
            for source in upstream:
                relative = source.relative_to(vendor)
                self.assertEqual(source.read_bytes(), (project / relative).read_bytes(), str(relative))
            for source in (vendor / 'extensions/extension/src/main/java').rglob('*.java'):
                self.assertEqual(source.read_bytes(), (project / source.relative_to(vendor)).read_bytes())
            for part in ('patches', 'extensions'):
                for source in (prepare.OVERLAY / part).rglob('*'):
                    if source.is_file():
                        self.assertEqual(source.read_bytes(), (project / source.relative_to(prepare.OVERLAY)).read_bytes())
            self.assertIn('version = ' + prepare.VERSION, (project / 'gradle.properties').read_text())
            self.assertEqual(prepare.stable.verify_vendor()['commit'], stable.COMMIT)

    def test_listing_defaults_and_exact_targets(self):
        listing = fixture_listing()
        verify.verify_listing(listing)
        with self.assertRaises(ValueError):
            verify.verify_listing(listing.replace('Enabled: false', 'Enabled: true'))
        with self.assertRaises(ValueError):
            verify.verify_listing(listing.replace('Name: ' + verify.SELECTOR, 'Name: Not our experiment'))
        with self.assertRaises(ValueError):
            verify.verify_listing(listing.replace('org.telegram.messenger.web', 'example.invalid', 1))
        with self.assertRaises(ValueError):
            verify.verify_listing(listing + '\nName: Additional selector\nEnabled: false')

    def test_runtime_has_no_account_reset_or_external_endpoint(self):
        runtime = (ROOT / 'extras/telegram-email-experiment/extensions/extension/src/main/java/'
                   'app/template/extension/telegram/EmailAlternative.java').read_text(encoding='utf-8')
        self.assertNotIn('resetLoginEmail', runtime)
        self.assertNotIn('http://', runtime)
        self.assertNotIn('https://', runtime)
        self.assertNotIn('Log.', runtime)
        self.assertIn('TL_auth_sentCodeTypeSetUpEmailRequired', runtime)
        self.assertIn('(flags & 2) == 0', runtime)
        self.assertIn('ATTEMPTED', runtime)
        self.assertIn('REQUEST_LIMIT_MS', runtime)

    def test_refuses_partial_desktop_patch_report(self):
        import sys
        sys.path.insert(0, str(ROOT / 'tools/telegram'))
        import verify_patching
        with tempfile.TemporaryDirectory(prefix='tg-email-report-') as tmp:
            apk = Path(tmp) / 'rebuilt.apk'
            with zipfile.ZipFile(apk, 'w') as archive:
                archive.writestr('classes.dex', b'fixture')
            report = Path(tmp) / 'report.json'
            data = {'success': True, 'outputPath': str(apk), 'packageName': 'org.telegram.messenger.web',
                    'packageVersion': '12.10.1', 'failedPatches': [], 'appliedPatches': [verify.SELECTOR],
                    'stepResults': [{'step': 'PATCHING', 'success': True}, {'step': 'REBUILDING', 'success': True}]}
            report.write_text(json.dumps(data))
            verify_patching.verify_report(report, {verify.SELECTOR}, 'org.telegram.messenger.web')
            data['failedPatches'] = [{'name': verify.SELECTOR}]
            report.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                verify_patching.verify_report(report, {verify.SELECTOR}, 'org.telegram.messenger.web')


if __name__ == '__main__':
    unittest.main()
