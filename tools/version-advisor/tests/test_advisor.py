"""Unit tests: python3 -m unittest discover -s tools/version-advisor/tests -v"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_DIR))

from advisor import catalog as cat  # noqa: E402
from advisor import devices as dev  # noqa: E402
from advisor import recommend as rec  # noqa: E402
from advisor import server as srv  # noqa: E402

SAMPLE_MANIFEST = {
    "version": "9.9.9",
    "patches": [
        {
            "name": "Patch A",
            "compatiblePackages": [
                {
                    "packageName": "com.google.android.youtube",
                    "targets": [
                        {"version": "21.20.405", "minSdk": 28, "isExperimental": False},
                        {"version": "21.40.161", "minSdk": 29, "isExperimental": True},
                    ],
                },
                {"packageName": "com.google.android.apps.youtube.music", "targets": [{"version": "1.1.1", "minSdk": 24}]},
            ],
        },
        {
            "name": "Patch B",
            "compatiblePackages": [
                {
                    "packageName": "com.google.android.youtube",
                    "targets": [
                        {"version": "21.20.405", "minSdk": 28, "isExperimental": False},
                        {"version": "21.40.161", "minSdk": 30, "isExperimental": True},
                        {"version": "20.21.37", "minSdk": 26, "isExperimental": False},
                    ],
                }
            ],
        },
    ],
}


class CatalogTests(unittest.TestCase):
    def test_version_key(self):
        self.assertLess(cat.version_key("21.9.3"), cat.version_key("21.40.161"))
        self.assertLess(cat.version_key("20.51.39"), cat.version_key("21.20.405"))

    def test_extract_versions_ignores_other_packages(self):
        versions = cat.extract_versions(SAMPLE_MANIFEST)
        self.assertEqual([v["version"] for v in versions], ["21.40.161", "21.20.405", "20.21.37"])
        by_version = {v["version"]: v for v in versions}
        self.assertEqual(by_version["21.40.161"]["minSdk"], 30)  # strictest wins
        self.assertTrue(by_version["21.40.161"]["experimental"])
        self.assertEqual(by_version["21.40.161"]["patchCount"], 2)
        self.assertFalse(by_version["21.20.405"]["experimental"])
        self.assertEqual(by_version["20.21.37"]["androidMin"], "8.0")

    def test_compare_channels(self):
        local = cat.extract_versions(SAMPLE_MANIFEST)
        upstream_manifest = json.loads(json.dumps(SAMPLE_MANIFEST))
        for patch in upstream_manifest["patches"]:
            for package in patch["compatiblePackages"]:
                if package["packageName"] == cat.YOUTUBE_PACKAGE:
                    for target in package["targets"]:
                        if target["version"] == "20.21.37":
                            target["version"] = "20.99.99"
        diff = cat.compare_channels(local, cat.extract_versions(upstream_manifest))
        self.assertEqual([v["version"] for v in diff["added"]], ["20.99.99"])
        self.assertEqual([v["version"] for v in diff["removed"]], ["20.21.37"])

    def test_offline_sync_writes_catalog_and_docs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            manifest = root / "patches-list.json"
            manifest.write_text(json.dumps(SAMPLE_MANIFEST), encoding="utf-8")
            target = root / "supported-versions.json"
            result = cat.sync_catalog(target, manifest, online=False, write=True)
            self.assertTrue(target.is_file())
            self.assertEqual(result["catalog"]["local"]["patchVersion"], "9.9.9")
            self.assertEqual(result["catalog"]["changes"]["added"], [])
            self.assertIn("Offline", result["error"])
            docs = root / "versions.md"
            cat.write_docs(result["catalog"], docs)
            self.assertIn("21.40.161", docs.read_text(encoding="utf-8"))


class DeviceTests(unittest.TestCase):
    def test_resolve_by_model_code(self):
        device, match = dev.resolve_device("SM-A546B")
        self.assertIsNotNone(device)
        self.assertEqual(device["id"], "samsung-a54")
        self.assertTrue(match["exact"])
        self.assertEqual(device["sdk"], 33)

    def test_resolve_by_marketing_name(self):
        device, _ = dev.resolve_device("Galaxy A54 5G")
        self.assertIsNotNone(device)
        self.assertEqual(device["id"], "samsung-a54")

    def test_parse_android_user_agent(self):
        ua = "Mozilla/5.0 (Linux; Android 13; SM-A546B Build/TP1A.220624.014; wv) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
        info = dev.parse_user_agent(ua)
        self.assertEqual(info["model"], "SM-A546B")
        self.assertEqual(info["android"], "13")
        self.assertEqual(info["sdk"], 33)

    def test_desktop_user_agent_is_not_a_phone(self):
        ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
        info = dev.parse_user_agent(ua)
        self.assertIsNone(info["model"])
        self.assertIsNone(info["sdk"])

    def test_sdk_conversion(self):
        self.assertEqual(dev.sdk_from_android("8.1"), 27)
        self.assertEqual(dev.sdk_from_android("13.0.0"), 33)
        self.assertEqual(dev.sdk_from_android(14), 34)
        self.assertEqual(dev.sdk_from_android("15"), 35)
        self.assertIsNone(dev.sdk_from_android("banana"))

    def test_density_and_abi(self):
        self.assertEqual(dev.dpi_bucket(450), "xxhdpi")
        self.assertEqual(dev.dpi_bucket(560), "xxxhdpi")
        self.assertEqual(dev.dpi_bucket(None), "nodpi")
        self.assertEqual(dev.primary_abi(["armeabi-v7a", "arm64-v8a"]), "arm64-v8a")
        self.assertEqual(dev.primary_abi(["armeabi-v7a"]), "armeabi-v7a")

    def test_manual_override_wins(self):
        profile = dev.profile_from_payload({"model": "SM-A546B", "sdk": 26, "abi": "armeabi-v7a", "density": "hdpi"})
        self.assertEqual(profile["sdk"], 26)
        self.assertEqual(profile["primaryAbi"], "armeabi-v7a")
        self.assertEqual(profile["density"], "hdpi")
        self.assertEqual(profile["deviceId"], "samsung-a54")

    def test_android_go_keeps_32bit_abi(self):
        profile = dev.profile_from_payload({"model": "Redmi 9A"})
        self.assertEqual(profile["primaryAbi"], "armeabi-v7a")
        self.assertIn("go32", profile["tags"])

    def test_no_gms_device_is_flagged(self):
        profile = dev.profile_from_payload({"model": "VOG-L29"})
        self.assertIn("no-gms", profile["tags"])

    def test_missing_sdk_raises(self):
        with self.assertRaises(dev.DeviceDetectionError):
            dev.profile_from_payload({})


class RecommendationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = cat.load_catalog()

    def analyze(self, sdk, **kwargs):
        profile = dev.profile_from_payload({"model": "Test phone", "sdk": sdk, "abi": "arm64-v8a", "density": "xxhdpi", **kwargs})
        return rec.analyze(profile, self.catalog, "local")

    def test_new_phone_prefers_stable_but_reports_newest(self):
        result = self.analyze(33)
        self.assertFalse(result["recommendation"]["experimental"])
        self.assertEqual(result["recommendation"]["version"], "21.20.405")
        self.assertTrue(result["newestCompatible"]["experimental"])
        self.assertEqual(result["compatibleCount"], len(result["options"]))
        top_score = max(option["score"] for option in result["options"])
        self.assertEqual(result["recommendation"]["score"], top_score, "recommended build must also have the highest score")

    def test_android_9_phone_cannot_run_sdk_29_builds(self):
        result = self.analyze(28)
        self.assertEqual(result["compatibleCount"], 5)
        self.assertFalse(result["recommendation"]["experimental"])
        for option in result["options"]:
            if option["minSdk"] == 29:
                self.assertFalse(option["compatible"])
                self.assertTrue(any(r["code"] == "sdk_fail" for r in option["reasons"]))

    def test_old_android_only_one_build(self):
        result = self.analyze(26)
        self.assertEqual(result["compatibleCount"], 1)
        self.assertEqual(result["recommendation"]["version"], "20.21.37")

    def test_unsupported_phone(self):
        result = self.analyze(23)
        self.assertIsNone(result["recommendation"])
        self.assertEqual(result["noCompatibleReason"]["code"], "no_compatible")

    def test_reasons_are_bilingual(self):
        result = self.analyze(33)
        for option in result["options"]:
            for reason in option["reasons"]:
                self.assertTrue(reason["en"].strip())
                self.assertTrue(reason["km"].strip())
        self.assertEqual(result["apk"]["variant"], "nodpi")
        self.assertEqual(result["apk"]["abi"], "arm64-v8a")
        # A catalog that is fully synced with upstream reports "no_update"
        # instead of "update_available"; both are valid update-status notes.
        self.assertTrue(any(note["code"] in {"update_available", "no_update"}
                            for note in result["notes"]))

    def test_upstream_channel(self):
        profile = dev.profile_from_payload({"model": "SM-A546B", "sdk": 34})
        result = rec.analyze(profile, self.catalog, "upstream")
        self.assertEqual(result["channel"], "upstream")
        self.assertEqual(result["newestCompatible"]["version"], self.catalog["upstream"]["versions"][0]["version"])


class ServerTests(unittest.TestCase):
    def test_http_api(self):
        original = {key: srv.STATE[key] for key in ("catalog", "devices", "online", "refreshing", "refreshError", "lastRefresh")}
        srv.STATE["catalog"] = cat.load_catalog()
        srv.STATE["devices"] = dev.load_devices()
        srv.STATE["online"] = False
        srv.STATE["refreshing"] = False
        srv.STATE["refreshError"] = None
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), srv.Handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{httpd.server_port}"
        try:
            with urllib.request.urlopen(base + "/api/state", timeout=10) as response:
                state = json.loads(response.read())
            self.assertIn("local", state["catalog"])
            self.assertTrue(state["devices"])
            with urllib.request.urlopen(base + "/", timeout=10) as response:
                self.assertIn(b"YouTube Version Advisor", response.read())

            request = urllib.request.Request(
                base + "/api/recommend",
                data=json.dumps({"model": "SM-A546B", "channel": "local"}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                result = json.loads(response.read())
            self.assertEqual(result["device"]["sdk"], 33)
            self.assertFalse(result["recommendation"]["experimental"])
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=5)
            srv.STATE.update(original)


if __name__ == "__main__":
    unittest.main(verbosity=2)
