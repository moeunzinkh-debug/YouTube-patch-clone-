"""Host-only checks of the sanitized manifest comparison, without APKs or a device."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

from lxml import etree

spec = importlib.util.spec_from_file_location('inspect_push', 'tools/simsimi/inspect_push_compat.py')
inspector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspector)


class FakeApk:
    def __init__(self, path):
        self.root = etree.fromstring(b'''<manifest xmlns:android="http://schemas.android.com/apk/res/android">
          <permission android:name="app.revanced.android.c2dm.permission.SEND" android:protectionLevel="signature"/>
          <permission android:name="irrelevant.permission"/>
          <application>
            <receiver android:name="org.microg.gms.gcm.PushRegisterReceiver" android:exported="true">
              <intent-filter><action android:name="app.revanced.iid.TOKEN_REQUEST"/></intent-filter>
            </receiver>
            <receiver android:name="example.Name" android:permission="com.google.android.c2dm.permission.SEND">
              <intent-filter><action android:name="com.google.android.c2dm.intent.RECEIVE"/></intent-filter>
            </receiver>
            <service android:name="irrelevant.Service"/>
          </application>
        </manifest>''')
    def get_package(self): return 'app.revanced.android.gms'
    def get_android_manifest_xml(self): return self.root
    def get_androidversion_name(self): return '7.3.0-dev.2'
    def get_androidversion_code(self): return '255070302'
    def get_target_sdk_version(self): return '34'
    def get_permissions(self):
        return ['android.permission.INTERNET', 'app.revanced.android.c2dm.permission.SEND']


class InspectPushCompatibilityTest(unittest.TestCase):
    @patch.object(inspector, 'APK', FakeApk)
    def test_relevant_actions_permissions_and_component_filter(self):
        result = inspector.manifest(Path('synthetic.apk'), 'app.revanced.android.gms')
        self.assertEqual(result['requested_permissions'], ['app.revanced.android.c2dm.permission.SEND'])
        self.assertEqual(result['declared_c2dm_permissions'], [
            {'name': 'app.revanced.android.c2dm.permission.SEND', 'protection_level': 'signature'}])
        self.assertEqual(len(result['messaging_components']), 2)
        self.assertEqual(result['messaging_components'][0]['actions'], ['app.revanced.iid.TOKEN_REQUEST'])
        self.assertEqual(result['messaging_components'][1]['permission'], 'com.google.android.c2dm.permission.SEND')

    @patch.object(inspector, 'APK', FakeApk)
    def test_wrong_package_is_rejected(self):
        with self.assertRaises(ValueError):
            inspector.manifest(Path('synthetic.apk'), 'com.google.android.gms')


if __name__ == '__main__':
    unittest.main()
