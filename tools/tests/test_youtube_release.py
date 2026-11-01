"""Checks for the YouTube development release metadata; no network required."""
import datetime
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION = '2.0.0-dev.1'
BASE = 'https://github.com/moeunzinkh-debug/YouTube-patch-clone-'


class YouTubeDevelopmentRelease(unittest.TestCase):
    def test_release_metadata_describes_the_compiled_bundle(self):
        meta = json.loads((ROOT / f'docs/releases/v{VERSION}/patches-bundle.json').read_text())
        self.assertEqual(meta['version'], VERSION)
        self.assertEqual(meta['download_url'], f'{BASE}/releases/download/v{VERSION}/patch.mpp')
        self.assertEqual(meta['page_url'], f'{BASE}/releases/tag/v{VERSION}')
        datetime.datetime.fromisoformat(meta['created_at'].replace('Z', '+00:00'))
        self.assertEqual((ROOT / 'patch.mpp.sha256').read_text().split()[0],
                         hashlib.sha256((ROOT / 'patch.mpp').read_bytes()).hexdigest())
        self.assertEqual(json.loads((ROOT / 'patches-list.json').read_text())['version'], VERSION)

    def test_release_notes_explain_targets_privacy_and_limitations(self):
        notes = (ROOT / f'docs/releases/v{VERSION}.md').read_text()
        for text in ('21.30.216', '21.23.492', 'Android 9', 'Google Translate',
                     'not installed or launched', 'stable v1.49.0'):
            self.assertIn(text, notes)
        for patch in ('Download post images', 'Search comments', 'Translate posts', 'Niconico comments'):
            self.assertIn(patch, notes)

    def test_publication_workflow_preserves_the_previous_release(self):
        workflow = (ROOT / '.github/workflows/publish-youtube-200-dev1.yml').read_text()
        self.assertIn('--draft --prerelease', workflow)
        self.assertIn('refusing to overwrite', workflow)
        self.assertIn('youtube-stable-before.json', workflow)
        self.assertIn('youtube-stable-after.json', workflow)
        self.assertNotIn('--clobber', workflow)
        self.assertNotIn('--latest', workflow)


if __name__ == '__main__':
    unittest.main()
