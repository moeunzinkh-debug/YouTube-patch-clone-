#!/usr/bin/env python3
"""Regression tests for the Settings row's live DEX register preservation."""
import unittest

from verify_patched import SETTINGS_CLICK, verify_settings_row


class SettingsRowVerificationTest(unittest.TestCase):
    def setUp(self):
        self.original = [('nop', '')] * 177
        self.original[19] = ('const/4', 'v7,0')
        self.original[63] = ('move', 'v0,v7')
        self.injected = [
            ('move-object/from16', 'v16,v9'), ('const/4', 'v4,0'),
            ('const-string', 'v5,SettingsPatch'), ('const/4', 'v6,0'),
            ('const-string', 'v7,Translationproviders'), ('const/4', 'v8,0'),
            ('new-instance', 'v9,' + SETTINGS_CLICK),
            ('invoke-direct', 'v9,' + SETTINGS_CLICK + '-><init>()V'),
            ('const-wide/16', 'v10,0'), ('const/4', 'v12,0'),
            ('invoke-static', 'Laa4;->G()Lc64;'), ('move-result-object', 'v13'),
            ('const-wide/16', 'v14,0'), ('const/16', 'v17,0'), ('const/16', 'v18,1493'),
            ('invoke-static/range', 'v4...v18,Lu44;->v('),
            ('move-object/from16', 'v9,v16'), ('const/4', 'v7,0'),
        ]

    def patched(self, injected=None):
        return self.original[:28] + (self.injected if injected is None else injected) + self.original[28:]

    def test_preserving_composer_and_live_zero_passes(self):
        verify_settings_row(self.original, self.patched())

    def test_missing_zero_restoration_is_rejected(self):
        bad = self.injected.copy()
        bad[-1] = ('nop', '')
        with self.assertRaisesRegex(ValueError, 'restore the live composer and zero'):
            verify_settings_row(self.original, self.patched(bad))

    def test_missing_composer_restoration_is_rejected(self):
        bad = self.injected.copy()
        bad[-2] = ('nop', '')
        with self.assertRaisesRegex(ValueError, 'restore the live composer and zero'):
            verify_settings_row(self.original, self.patched(bad))

    def test_unrelated_original_instruction_change_is_rejected(self):
        modified = self.patched()
        modified[-1] = ('return-void', '')
        with self.assertRaisesRegex(ValueError, 'Original Settings rows changed'):
            verify_settings_row(self.original, modified)


if __name__ == '__main__':
    unittest.main()
