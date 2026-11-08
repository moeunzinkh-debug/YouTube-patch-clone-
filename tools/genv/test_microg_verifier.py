#!/usr/bin/env python3
import copy
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from verify_microg_patched import ANDROID, EXPECTED_METADATA, GUARD, ROUTES, verify_availability, verify_manifest


class MicroGVerifierTests(unittest.TestCase):
    def test_verifier_and_patch_have_identical_narrow_route_counts(self):
        source = (Path(__file__).parent / 'project/patches/src/main/kotlin/app/morphe/patches/genv/MorpheMicroGSupportPatch.kt').read_text()
        part = source.split('private val routeCounts = linkedMapOf(', 1)[1].split('\n)', 1)[0]
        entries = re.findall(r'"([^"]+)" to (\d+)', part)
        self.assertEqual(dict((k, int(v)) for k, v in entries), ROUTES)
        self.assertNotIn('com.google.android.gms.auth.api.signin.internal.ISignInService', ROUTES)

    def test_availability_guard_falls_back_to_original(self):
        original = [('sget-object', '', 2, None)] * 284
        prefix = [('invoke-static/range', 'v10, ' + GUARD + '->isAvailable(Landroid/content/Context;)Z', 6, None),
                  ('move-result', 'v0', 2, None), ('if-eqz', 'v0, +4', 4, 4),
                  ('const/4', 'v0, 0', 2, None), ('return', 'v0', 2, None), ('nop', '', 2, None)]
        verify_availability(original, prefix + original)
        for bad in (prefix[:2] + [('if-eqz', 'v0, +3', 4, 3)] + prefix[3:],
                    prefix[:3] + [('const/4', 'v0, 1', 2, None)] + prefix[4:]):
            with self.assertRaises(ValueError): verify_availability(original, bad + original)

    def test_manifest_only_expected_changes(self):
        base = ET.fromstring('''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.ainate.ai.video.generate">
            <uses-permission android:name="com.google.android.c2dm.permission.RECEIVE"/>
            <application android:name="com.google.android.gms.SomeClass"/>
        </manifest>''')
        modified = copy.deepcopy(base)
        modified.find('uses-permission').set(ANDROID + 'name', 'app.revanced.android.c2dm.permission.RECEIVE')
        query = ET.Element('queries')
        ET.SubElement(query, 'package', {ANDROID + 'name': 'app.revanced.android.gms'})
        modified.insert(1, query)
        app = modified.find('application')
        for key, value in EXPECTED_METADATA.items():
            ET.SubElement(app, 'meta-data', {ANDROID + 'name': key, ANDROID + 'value': value})
        verify_manifest(base, modified)
        altered = copy.deepcopy(modified)
        altered.find('application').set(ANDROID + 'name', 'different')
        with self.assertRaises(ValueError): verify_manifest(base, altered)
        altered = copy.deepcopy(modified)
        altered.find('application/meta-data').set(ANDROID + 'value', 'bad')
        with self.assertRaises(ValueError): verify_manifest(base, altered)
        altered = copy.deepcopy(modified)
        altered.find('queries').clear()
        with self.assertRaises(ValueError): verify_manifest(base, altered)


if __name__ == '__main__': unittest.main()
