import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('advisor', Path(__file__).resolve().parents[1] / 'update.py')
advisor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(advisor)


class Recommendations(unittest.TestCase):
    def test_requested_versions_not_assumed_supported(self):
        data = advisor.build()
        self.assertFalse(data['compiled_gemini_support'])
        self.assertEqual([a['requested_status'] for a in data['apps']], ['unverified'] * 3)
        self.assertEqual([a['recommended_for_reference'] for a in data['apps']],
                         ['17.54.18.ve.arm64', '1.0.958859967', '7.0.0'])

    def test_upstream_discovery_does_not_promote(self):
        remote = {'commit': 'test', 'profile_versions': {'gemini': ['1.0.995038376']}}
        data = advisor.build(remote)
        self.assertEqual(data['apps'][1]['requested_status'], 'unverified')
        self.assertEqual(data['apps'][1]['upstream_profile_versions'], ['1.0.995038376'])

    def test_truncated_tree_rejected(self):
        with patch.object(advisor, 'api', side_effect=[{'sha': 'test'}, {'truncated': True}]):
            with self.assertRaises(ValueError):
                advisor.discover()

    def test_offline_render(self):
        self.assertIn('Offline generation', advisor.markdown(advisor.build()))

    def test_network_failure_propagates(self):
        with patch.object(advisor, 'api', side_effect=OSError('offline')):
            with self.assertRaises(OSError):
                advisor.discover()
