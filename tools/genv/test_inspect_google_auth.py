import unittest
from inspect_google_auth import extract_route, identifier, route_literal, JS_INDICATORS
from trace_google_auth import parse_certificate_digests, sanitized_flow

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

    def test_signer_digests_only_not_certificate_subjects(self):
        text = ('Signer #1 certificate DN: CN=do-not-report@example.com\n'
                'Signer #1 certificate SHA-1 digest: ' + 'a' * 40 + '\n'
                'Source Stamp Signer certificate SHA-256 digest: ' + 'b' * 64 + '\n')
        values = parse_certificate_digests(text)
        self.assertEqual([v['algorithm'] for v in values], ['sha1', 'sha256'])
        self.assertEqual(values[0]['label'], 'Signer #1')
        self.assertNotIn('example.com', str(values))
        tagged = parse_certificate_digests('Signer (minSdkVersion=24, maxSdkVersion=32) #1: certificate SHA-1 digest: ' + 'c' * 40)
        self.assertNotEqual(tagged[0]['label'], 'other')

    def test_js_evidence_is_fixed_counts_only(self):
        self.assertTrue(all(isinstance(needle, bytes) and len(needle) >= 6 for needle in JS_INDICATORS.values()))
        sample = b'my-token-and-password-but-rngooglesignin'
        counts = {key: sample.count(needle) for key, needle in JS_INDICATORS.items()}
        self.assertEqual(counts['native_google_signin'], 1)
        self.assertTrue(all(isinstance(value, int) for value in counts.values()))

    def test_control_flow_never_emits_raw_values(self):
        class Instruction:
            def __init__(self, name, output, length=2, branch=0):
                self.name, self.output, self.length, self.branch = name, output, length, branch
            def get_name(self): return self.name
            def get_output(self): return self.output
            def get_length(self): return self.length
            def get_ref_off(self): return self.branch

        rows = sanitized_flow([
            Instruction('const-string', 'v0, "password=private@example.org"'),
            Instruction('const-string', 'v0, "com.google.android.gms"'),
            Instruction('const/4', 'v1, 3'),
            Instruction('if-eqz', 'v1, +2h', branch=2),
            Instruction('const/16', 'v2, 100000'),
            Instruction('return', 'v1'),
            Instruction('add-int/lit8', 'v1, v0, -1'),
        ])
        self.assertNotIn('password', str(rows))
        self.assertNotIn('example.org', str(rows))
        self.assertEqual(rows[1]['route'], 'com.google.android.gms')
        self.assertEqual(rows[2]['small_integer'], 3)
        self.assertEqual(rows[3]['target_index'], 5)
        self.assertNotIn('small_integer', rows[4])
        self.assertEqual(rows[6]['small_integer'], -1)

if __name__ == '__main__': unittest.main()
