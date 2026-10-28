#!/usr/bin/env python3
"""Offline tests for the emulator UI helper; no Android device required."""
import unittest
from unittest.mock import patch
import emulator_smoke


class EmulatorSmokeTest(unittest.TestCase):
    def test_bounds_validation(self):
        self.assertEqual((25, 45), emulator_smoke.center("[10,20][40,70]"))
        self.assertIsNone(emulator_smoke.center("[10,20][10,70]"))
        self.assertIsNone(emulator_smoke.center("broken"))

    def test_search_click_uses_visible_accessibility_bounds(self):
        xml = '<hierarchy><node text="" content-desc="Search settings" bounds="[10,20][50,80]" /></hierarchy>'
        with patch.object(emulator_smoke, "run", return_value="") as command:
            self.assertTrue(emulator_smoke.tap_search(xml))
            command.assert_called_once_with("adb", "shell", "input", "tap", "30", "50")
        with patch.object(emulator_smoke, "run") as command:
            self.assertFalse(emulator_smoke.tap_search('<hierarchy><node text="Other" /></hierarchy>'))
            command.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
