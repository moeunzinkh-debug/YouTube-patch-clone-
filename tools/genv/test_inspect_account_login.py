#!/usr/bin/env python3
"""Offline tests for allowlisted, credential-free GenV account inspection."""
import unittest

from inspect_account_login import METHOD_LABELS, VALID_SITE, label_value


class AccountInspectionGuards(unittest.TestCase):
    def test_fixed_known_sdk_methods(self):
        for method, label in METHOD_LABELS.items():
            self.assertEqual(label_value(method), label)
            self.assertEqual(label_value('dev.flutter.pigeon.firebase_auth_platform_interface.AuthApi.' + method), label)

    def test_fixed_general_words_not_user_values(self):
        self.assertEqual(label_value('Username'), 'username_word')
        self.assertEqual(label_value('PASSWORD'), 'password_word')
        self.assertEqual(label_value('Sign Up'), 'sign_up_words')
        for value in ('password=secret', 'username@example.com', 'createUserWithEmailAndPassword:secret',
                      'dev.flutter.pigeon.other.AuthApi.updatePassword', 'com.google.android.c2dm.intent.REGISTER',
                      'https://example.invalid/auth/login?token=private'):
            self.assertIsNone(label_value(value))

    def test_method_identifiers_only(self):
        self.assertTrue(VALID_SITE.fullmatch('Lv6/a;->m(Ljava/lang/Object;Lf6/h;)V'))
        self.assertIsNone(VALID_SITE.fullmatch('user@example.com'))
        self.assertIsNone(VALID_SITE.fullmatch('Lexample/a;->method()V https://example.invalid'))


if __name__ == '__main__':
    unittest.main()
