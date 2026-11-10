#!/usr/bin/env python3
"""Offline checks for the credential-free emulator test's account guard."""
import unittest
from emulator_test import has_microg_account


class AccountGuardTest(unittest.TestCase):
    def test_detects_only_actual_microg_accounts(self):
        self.assertFalse(has_microg_account('Accounts: 0\nAuthenticatorDescription {type=app.revanced}'))
        self.assertFalse(has_microg_account('Account {name=fixture, type=app.revanced.work}'))
        self.assertTrue(has_microg_account('Account {name=fixture, type=app.revanced}'))
        self.assertTrue(has_microg_account('Account {type=app.revanced, name=fixture}'))


if __name__ == '__main__':
    unittest.main()
