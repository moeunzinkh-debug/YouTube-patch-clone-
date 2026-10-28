#!/usr/bin/env python3
"""Offline tests for the emulator UI helper; no Android device required."""
import base64
import gzip
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import emulator_smoke


class EmulatorSmokeTest(unittest.TestCase):
    def test_bounds_validation(self):
        self.assertEqual((25, 45), emulator_smoke.center("[10,20][40,70]"))
        self.assertIsNone(emulator_smoke.center("[10,20][10,70]"))
        self.assertIsNone(emulator_smoke.center("broken"))

    def test_error_reports_only_safe_install_code(self):
        result = SimpleNamespace(returncode=1, stdout="private text Failure [INSTALL_FAILED_UPDATE_INCOMPATIBLE]")
        with patch.object(emulator_smoke.subprocess, "run", return_value=result):
            with self.assertRaises(RuntimeError) as raised:
                emulator_smoke.run("adb", "install", "some.apk")
        self.assertIn("INSTALL_FAILED_UPDATE_INCOMPATIBLE", str(raised.exception))
        self.assertNotIn("private text", str(raised.exception))

    def test_visibility_flags_exclude_arbitrary_dumpsys_text(self):
        dump = "mShowRequested=true mInputShown=false text=private isInputViewShown=true"
        self.assertEqual({"mShowRequested": True, "mInputShown": False, "isInputViewShown": True},
                         emulator_smoke.ime_visibility_flags(dump))
        self.assertEqual({}, emulator_smoke.ime_visibility_flags("private text and unknownFlag=true"))

    def test_taps_only_the_synthetic_editor(self):
        xml = ('<hierarchy><node package="other" class="android.widget.EditText" bounds="[1,1][4,4]" />'
               '<node package="dev.arena.gboardprobe" class="android.widget.EditText" '
               'bounds="[10,20][50,80]" /></hierarchy>')
        with patch.object(emulator_smoke, "run", return_value="") as command:
            self.assertTrue(emulator_smoke.tap_synthetic_editor(xml))
            command.assert_called_once_with("adb", "shell", "input", "tap", "30", "50")

    def test_crash_diagnostics_exclude_messages_and_other_processes(self):
        log = ("FATAL EXCEPTION: main\n Process: other.app, PID: 1\n"
               "java.lang.IllegalStateException: other\n"
               "FATAL EXCEPTION: main\n Process: dev.jason.com.google.android.inputmethod.latin, PID: 2\n"
               "java.lang.VerifyError: private user content\nCaused by: java.lang.IllegalAccessError: private\n")
        self.assertEqual(["java.lang.IllegalAccessError", "java.lang.VerifyError"],
                         emulator_smoke.gboard_crash_types(log))

    def test_ime_inspector_reads_only_encoded_instrumentation_result(self):
        windows = [{"text": "", "children": [{"description": "Translate", "bounds": "[1,2][3,4]"}]}]
        payload = base64.b64encode(gzip.compress(json.dumps(windows).encode())).decode()
        output = "INSTRUMENTATION_RESULT: ime_windows=" + payload + "\nINSTRUMENTATION_CODE: -1"
        with patch.object(emulator_smoke, "run", return_value=output):
            self.assertEqual(windows, emulator_smoke.inspect_ime_windows())
        self.assertEqual(2, len(list(emulator_smoke.flatten_window_nodes(windows))))
        with patch.object(emulator_smoke, "run", return_value="") as command:
            self.assertTrue(emulator_smoke.tap_ime_label(windows, "translate"))
            command.assert_called_once_with("adb", "shell", "input", "tap", "2", "3")
        with patch.object(emulator_smoke, "run") as command:
            self.assertFalse(emulator_smoke.tap_ime_label(windows, "missing"))
            command.assert_not_called()
        with patch.object(emulator_smoke, "run", return_value="INSTRUMENTATION_FAILED: private"):
            with self.assertRaisesRegex(RuntimeError, "did not return"):
                emulator_smoke.inspect_ime_windows()

    def test_consent_is_tapped_only_for_the_synthetic_gboard_dialog(self):
        xml = ('<hierarchy><node package="dev.jason.com.google.android.inputmethod.latin" '
               'text="Using Google Translate" /><node package="dev.jason.com.google.android.inputmethod.latin" '
               'class="android.widget.Button" text="OK" clickable="true" bounds="[10,20][50,80]" /></hierarchy>')
        with patch.object(emulator_smoke, "run", return_value="") as command:
            self.assertTrue(emulator_smoke.accept_synthetic_translate_consent(xml))
            command.assert_called_once_with("adb", "shell", "input", "tap", "30", "50")
        with patch.object(emulator_smoke, "run") as command:
            self.assertFalse(emulator_smoke.accept_synthetic_translate_consent(xml.replace("Using Google Translate", "Other dialog")))
            command.assert_not_called()

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
