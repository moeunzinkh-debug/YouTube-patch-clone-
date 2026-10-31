#!/usr/bin/env python3
"""Offline transaction and rollback tests; no GitHub requests or APK access."""
import copy
import tempfile
import unittest
from pathlib import Path

import publish_release as p

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / 'bundles/instant-translate/bundle.mpp'
CHECKSUM = ROOT / 'bundles/instant-translate/bundle.mpp.sha256'


class FakeGitHub:
    def __init__(self):
        self.state = {'id': p.RELEASE_ID, 'tag_name': p.TAG, 'draft': False, 'prerelease': True,
                      'body': 'Historical crash warning and old bundle description.\n', 'assets': []}
        self.contents = {}
        self.next_id = 1000000000
        self.fail_promote_after = None
        self.fail_notes_after = False
        self.concurrent_body = False
        self.concurrent_extra_asset = False
        self.uploads = 0
        for name, (digest, size) in p.OLD.items():
            self.state['assets'].append(self.asset(p.OLD_IDS[name], name, digest, size))
        for name, (asset_id, digest) in p.EXPECTED_APKS.items():
            self.state['assets'].append(self.asset(asset_id, name, digest, 1234))

    @staticmethod
    def asset(asset_id, name, digest, size):
        return {'id': asset_id, 'name': name, 'digest': 'sha256:' + digest, 'size': size, 'state': 'uploaded'}

    def release(self): return copy.deepcopy(self.state)

    def upload(self, files):
        self.uploads += 1
        for f in files:
            asset_id = self.next_id
            self.next_id += 1
            self.state['assets'].append(self.asset(asset_id, f.name, p.sha(f), f.stat().st_size))
            self.contents[asset_id] = f.read_bytes()
        if self.concurrent_body: self.state['body'] = 'Someone edited the notes during staging.'
        if self.concurrent_extra_asset:
            self.state['assets'].append(self.asset(self.next_id, 'user-asset.txt', 'a' * 64, 1))
            self.next_id += 1

    def rename(self, asset_id, name):
        asset = next(a for a in self.state['assets'] if a['id'] == asset_id)
        if any(a['name'] == name and a['id'] != asset_id for a in self.state['assets']):
            raise ValueError('duplicate name')
        asset['name'] = name
        if name == self.fail_promote_after and asset_id >= 1000000000:
            self.fail_promote_after = None
            raise RuntimeError('Simulated lost rename response')

    def delete(self, asset_id):
        self.state['assets'] = [a for a in self.state['assets'] if a['id'] != asset_id]

    def download(self, names, directory):
        directory.mkdir(parents=True, exist_ok=True)
        for name in names:
            asset = next(a for a in self.state['assets'] if a['name'] == name)
            (directory / name).write_bytes(self.contents[asset['id']])

    def update_body(self, body):
        self.state['body'] = body
        if self.fail_notes_after:
            self.fail_notes_after = False
            raise RuntimeError('Simulated lost update response')


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.github = FakeGitHub()
        self.original = self.github.release()
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.temp = Path(self.tempdir.name)

    def publish(self): return p.publish(self.github, BUNDLE, CHECKSUM, self.temp, '98765')

    def assert_original_bundles(self):
        original = p.assets_by_name(self.original)
        final = p.assets_by_name(self.github.release())
        for name in p.OLD:
            self.assertEqual(final[name], original[name])
        self.assertFalse(any(name.startswith(('stage-', 'backup-')) for name in final))
        for name in p.EXPECTED_APKS:
            self.assertEqual(final[name], original[name])

    def test_success_replaces_only_two_assets_and_preserves_history(self):
        result = self.publish()
        self.assertEqual(result['status'], 'published_and_verified')
        self.assertFalse(result['apk_assets_modified'])
        final = p.assets_by_name(self.github.release())
        for name, digest in p.NEW.items():
            self.assertEqual(final[name]['digest'], 'sha256:' + digest)
            self.assertNotEqual(final[name]['id'], p.OLD_IDS[name])
        for name in p.EXPECTED_APKS:
            self.assertEqual(final[name], p.assets_by_name(self.original)[name])
        self.assertEqual(len(final), len(self.original['assets']))
        self.assertIn(self.original['body'].strip(), self.github.release()['body'])
        self.assertIn('Google translation fallback ត្រូវបានដកចេញ', self.github.release()['body'])

    def test_lost_rename_response_rolls_back(self):
        self.github.fail_promote_after = 'bundle.mpp.sha256'
        with self.assertRaisesRegex(RuntimeError, 'rename'):
            self.publish()
        self.assert_original_bundles()
        self.assertEqual(self.github.release()['body'], self.original['body'])

    def test_lost_release_notes_response_rolls_back(self):
        self.github.fail_notes_after = True
        with self.assertRaisesRegex(RuntimeError, 'update'):
            self.publish()
        self.assert_original_bundles()
        self.assertEqual(self.github.release()['body'], self.original['body'])

    def test_concurrent_notes_change_is_preserved(self):
        self.github.concurrent_body = True
        with self.assertRaisesRegex(ValueError, 'notes changed'):
            self.publish()
        self.assert_original_bundles()
        self.assertEqual(self.github.release()['body'], 'Someone edited the notes during staging.')

    def test_concurrent_asset_addition_is_not_deleted(self):
        self.github.concurrent_extra_asset = True
        with self.assertRaisesRegex(ValueError, 'assets changed'):
            self.publish()
        self.assert_original_bundles()
        self.assertIn('user-asset.txt', p.assets_by_name(self.github.release()))

    def test_wrong_apk_metadata_aborts_before_upload(self):
        p.assets_by_name(self.github.state)['base.apk']['digest'] = 'sha256:' + '0' * 64
        with self.assertRaisesRegex(ValueError, 'APK metadata'):
            self.publish()
        self.assertEqual(self.github.uploads, 0)

    def test_wrong_original_bundle_id_aborts_before_upload(self):
        p.assets_by_name(self.github.state)['bundle.mpp']['id'] = 123
        with self.assertRaisesRegex(ValueError, 'asset ID'):
            self.publish()
        self.assertEqual(self.github.uploads, 0)


if __name__ == '__main__': unittest.main()
