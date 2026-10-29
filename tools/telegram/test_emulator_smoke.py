#!/usr/bin/env python3
import unittest

import emulator_smoke as smoke


class EmulatorSmokeTest(unittest.TestCase):
    def test_resolve_exact_package(self):
        output = ('priority=0 preferredOrder=0 match=0x108000 specificIndex=-1 isDefault=false\n'
                  'org.telegram.messenger.web/org.telegram.ui.LaunchActivity\n')
        self.assertEqual(smoke.parse_launcher(output),
                         'org.telegram.messenger.web/org.telegram.ui.LaunchActivity')
        with self.assertRaises(ValueError):
            smoke.parse_launcher('org.telegram.messenger/org.telegram.ui.LaunchActivity\n')

    def test_pid_check(self):
        self.assertTrue(smoke.parse_pid('1234\r\n'))
        self.assertFalse(smoke.parse_pid(''))
        self.assertFalse(smoke.parse_pid('pidof: not found'))

    def test_crash_filter(self):
        log = ('E AndroidRuntime: FATAL EXCEPTION: main\n'
               'E AndroidRuntime: Process: org.telegram.messenger.web, PID: 123\n'
               'E AndroidRuntime: java.lang.RuntimeException: fixture\n'
               'E AndroidRuntime:     at org.telegram.ui.LaunchActivity.onCreate()\n')
        self.assertIn('RuntimeException', smoke.relevant_crash(log))
        self.assertIsNone(smoke.relevant_crash(log.replace('messenger.web', 'other')))


if __name__ == '__main__':
    unittest.main()
