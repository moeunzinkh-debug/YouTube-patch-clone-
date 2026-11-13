#!/usr/bin/env python3
import tempfile, unittest
from pathlib import Path
from prepare_build import prepare
from verify_bundle import verify_listing
from verify_patched import verify

class PingoToolsTest(unittest.TestCase):
    def test_isolated_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'build'
            prepare(dest)
            files = list((dest / 'patches/src/main/kotlin').rglob('*.kt'))
            self.assertEqual([p.name for p in files], ['PingoPatches.kt'])
            self.assertIn('pingo-patches', (dest / 'settings.gradle.kts').read_text())
            with self.assertRaises(ValueError): prepare(dest)

    def test_listing_is_exact_and_disabled_by_default(self):
        text = ''.join(
            f'Name: {name}\nEnabled: false\nCompatible packages:\n  Package name: com.picoai.languageapp.android\n  Compatible versions:\n    5.4.8\n'
            for name in ('Remove license check', 'Unlock all feature')
        )
        verify_listing(text)
        for bad in (text.replace('Enabled: false', 'Enabled: true', 1), text + 'Name: Extra\nEnabled: false\n',
                    text.replace('com.picoai.languageapp.android', 'com.example.bad', 1)):
            with self.assertRaises(ValueError): verify_listing(bad)

    def test_independent_injection_shapes(self):
        base = {
            'check': [('const-string', 'v0,x')] + [('nop', '')] * 15,
            'initialize': [('sget-object', 'v0,x')] + [('nop', '')] * 28,
            'status': [('instance-of', 'v0,v1,Lcom/superwall/sdk/models/entitlements/SubscriptionStatus$Active;'), ('return', 'v0')],
            'entitlement': [('iget-boolean', 'v0,v1,x'), ('return', 'v0')],
        }
        for modes in (['license'], ['unlock'], ['license', 'unlock']):
            patched = {key: list(value) for key, value in base.items()}
            if 'license' in modes:
                for key in ('check', 'initialize'): patched[key] = [('return-void', '')] + patched[key]
            if 'unlock' in modes:
                for key in ('status', 'entitlement'): patched[key] = [('const/4', 'v0,1'), ('return', 'v0')] + patched[key]
            verify(base, patched, modes)
        bad = {key: list(value) for key, value in base.items()}
        bad['status'] = [('const/4', 'v0,1'), ('return', 'v0')]
        with self.assertRaises(ValueError): verify(base, bad, ['license'])

if __name__ == '__main__': unittest.main()
