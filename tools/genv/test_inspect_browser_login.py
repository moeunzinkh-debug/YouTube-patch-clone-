#!/usr/bin/env python3
"""Tests for bounded, credential-free browser login feasibility reporting."""
import json
import unittest
import xml.etree.ElementTree as ET

from inspect_browser_login import indicator, scheme_type, summarize_browsable


class BrowserLoginInspectionTest(unittest.TestCase):
    def test_scheme_types_never_return_identifier(self):
        ids = {'123-demo.apps.googleusercontent.com'}
        self.assertEqual(scheme_type('com.googleusercontent.apps.123-demo', ids), 'google_reversed_known_client')
        self.assertEqual(scheme_type('com.googleusercontent.apps.other', ids), 'google_reversed_other')
        self.assertEqual(scheme_type('https', ids), 'https')
        self.assertEqual(scheme_type('arbitrary.private', ids), 'other_custom_scheme')
        self.assertEqual(scheme_type('@string/scheme', ids), 'resource_reference')

    def test_only_browsable_view_and_no_host_path_or_client_value(self):
        root = ET.fromstring('''<manifest xmlns:android="http://schemas.android.com/apk/res/android"><application>
          <activity android:name="example.BrowserReturn" android:exported="true">
            <intent-filter android:autoVerify="true">
              <action android:name="android.intent.action.VIEW"/>
              <category android:name="android.intent.category.BROWSABLE"/>
              <data android:scheme="https" android:host="private-host.example" android:path="/oauth/callback"/>
              <data android:scheme="com.googleusercontent.apps.123-demo"/>
            </intent-filter>
          </activity>
          <activity android:name="example.Internal"><intent-filter>
            <action android:name="android.intent.action.VIEW"/>
          </intent-filter></activity>
        </application></manifest>''')
        result = summarize_browsable(root, {'123-demo.apps.googleusercontent.com'})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['scheme_types'], ['google_reversed_known_client', 'https'])
        self.assertTrue(result[0]['oauth_like_path_present'])
        self.assertEqual(result[0]['auto_verify'], 'true')
        text = json.dumps(result)
        for secret in ('private-host.example', '/oauth/callback', '123-demo'):
            self.assertNotIn(secret, text)

    def test_only_fixed_sdk_labels(self):
        self.assertEqual(indicator('plugins.flutter.io/google_sign_in'), 'flutter_google_signin_channel')
        self.assertEqual(indicator('dev.flutter.pigeon.google_sign_in_android.Api.signIn'),
                         'flutter_google_signin_pigeon_channel')
        self.assertEqual(indicator('idToken'), 'field_id_token')
        self.assertIsNone(indicator('private-account-or-token'))


if __name__ == '__main__':
    unittest.main()
