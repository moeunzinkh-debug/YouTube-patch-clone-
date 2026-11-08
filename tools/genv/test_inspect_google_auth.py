import unittest
from inspect_google_auth import extract_route, identifier, route_literal, JS_INDICATORS

class AuthInspectionGuards(unittest.TestCase):
    def test_only_fixed_routing_literals(self):
        for value in ('com.google', 'com.google.android.gms', 'com.google.android.gms.auth.api.signin.service.START',
                      'com.google.android.c2dm.intent.REGISTER', 'content://com.google.android.gms.phenotype'):
            self.assertTrue(route_literal(value), value)
        for value in ('', 'https://example.org', 'com.google.android.gms?token=abc',
                      'com.google.android.gms/user@example.com', 'com.google.android.gms";password=abc',
                      'app.revanced.android.gms', 'com.google.android.gms.' + 'x' * 200):
            self.assertFalse(route_literal(value), value)

    def test_operand_and_identifiers_are_bounded(self):
        self.assertEqual(extract_route('v0, "com.google.android.gms"'), 'com.google.android.gms')
        self.assertIsNone(extract_route('v0, "password=secret"'))
        self.assertIsNone(extract_route('v0, "com.google.android.gms?token=abc"'))
        self.assertTrue(identifier('Lcom/google/example;->call(Landroid/content/Context;)V'))
        self.assertFalse(identifier('Lcom/google/example;->call(https://s.example?secret=1)V'))
        self.assertFalse(identifier('x' * 261))

    def test_js_evidence_is_fixed_counts_only(self):
        self.assertTrue(all(isinstance(needle, bytes) and len(needle) >= 6 for needle in JS_INDICATORS.values()))
        sample = b'my-token-and-password-but-rngooglesignin'
        counts = {key: sample.count(needle) for key, needle in JS_INDICATORS.items()}
        self.assertEqual(counts['native_google_signin'], 1)
        self.assertTrue(all(isinstance(value, int) for value in counts.values()))

if __name__ == '__main__': unittest.main()
