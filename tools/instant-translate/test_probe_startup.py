#!/usr/bin/env python3
"""Tests for sanitized, process-specific Android startup-crash analysis."""
import json
import unittest

from compare_startup import INTEGRITY_FRAME, compare
from probe_startup import foreground_activity, parse_crash_log


class CrashAnalysisTest(unittest.TestCase):
    def test_expected_app_crash_extracts_only_safe_metadata(self):
        log = '''E/AndroidRuntime( 77): FATAL EXCEPTION: main
E/AndroidRuntime( 77): Process: com.spaceship.screen.textcopy, PID: 77
E/AndroidRuntime( 77): java.lang.RuntimeException: Unable to start activity
E/AndroidRuntime( 77): Caused by: java.lang.SecurityException: signature mismatch SECRET_KEY
E/AndroidRuntime( 77):    at bin.edisaputra.protector.LicenseActivity.verifyIntegrity(Native Method)
E/AndroidRuntime( 77):    at com.spaceship.screen.translate.ui.MainActivity.onCreate(MainActivity.java:7)
'''
        result = parse_crash_log(log)
        self.assertTrue(result['app_fatal_exception'])
        self.assertIn('java.lang.SecurityException', result['exception_types'])
        self.assertIn('bin.edisaputra.protector.LicenseActivity.verifyIntegrity', result['stack_frames'])
        self.assertIn('signature', result['exception_message_keywords'])
        self.assertNotIn('SECRET_KEY', json.dumps(result))

    def test_unrelated_process_does_not_count_as_app_crash(self):
        log = '''E/AndroidRuntime: FATAL EXCEPTION: main
E/AndroidRuntime: Process: other.application, PID: 3
E/AndroidRuntime: java.lang.RuntimeException: secret
E/AndroidRuntime: FATAL EXCEPTION: main
E/AndroidRuntime: Process: com.spaceship.screen.textcopy.evil, PID: 4
E/AndroidRuntime: java.lang.RuntimeException: secret
'''
        self.assertFalse(parse_crash_log(log)['app_fatal_exception'])

    def test_secondary_app_process_is_identified(self):
        log = '''FATAL EXCEPTION: worker
Process: com.spaceship.screen.textcopy:remote, PID: 3
java.lang.IllegalStateException: stopped
'''
        self.assertTrue(parse_crash_log(log)['app_fatal_exception'])

    def test_comparison_requires_a_healthy_original_and_matching_integrity_crashes(self):
        healthy = {'install': 'Success', 'main_activity_reached': True}
        crash = {'install': 'Success', 'app_fatal_exception': True, 'stack_frames': [INTEGRITY_FRAME]}
        _, conclusion = compare(healthy, crash, crash)
        self.assertEqual(conclusion, 'same_integrity_stack_in_manager_and_unchanged_dex_resign_control')
        _, conclusion = compare(crash, crash, crash)
        self.assertEqual(conclusion, 'inconclusive_original_baseline')
        _, conclusion = compare(healthy, crash, {'install': 'Failure'})
        self.assertEqual(conclusion, 'inconclusive_install_failed')
        _, conclusion = compare(healthy, crash, healthy)
        self.assertEqual(conclusion, 'different_or_inconclusive_outcomes')

    def test_foreground_only_returns_component(self):
        content = ('other output with personal info\n'
                   '  topResumedActivity=ActivityRecord{xyz u0 '
                   'com.spaceship.screen.textcopy/com.spaceship.screen.translate.ui.MainActivity t3}\n')
        self.assertEqual(foreground_activity(content),
                         'com.spaceship.screen.textcopy/com.spaceship.screen.translate.ui.MainActivity')
        self.assertEqual(foreground_activity('no resumed activity'), '')


if __name__ == '__main__':
    unittest.main()
