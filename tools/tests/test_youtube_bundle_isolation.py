"""Keep the YouTube bundle separate from retired standalone app patches."""
import importlib.util
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('verify_mpp', ROOT / '.github/scripts/verify-mpp.py')
verify_mpp = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_mpp)


class YouTubeBundleIsolation(unittest.TestCase):
    def test_detects_standalone_google_and_gemini_app_classes(self):
        google = 'app/morphe/patches/google/microg/GmsCoreSupportPatchKt.class'
        gemini = 'app/morphe/patches/gemini/GeminiPatchKt.class'
        youtube = 'app/morphe/patches/youtube/layout/HideAskGeminiButton.class'
        generic = 'app/morphe/patches/all/misc/CloneAppPatchKt.class'
        self.assertEqual(verify_mpp.standalone_google_app_patch_classes(
            [google, gemini, youtube, generic]), [google, gemini])

    def test_current_bundle_contains_no_standalone_google_app_patches(self):
        with zipfile.ZipFile(ROOT / 'patch.mpp') as archive:
            classes = [name for name in archive.namelist() if name.endswith('.class')]
        self.assertEqual(verify_mpp.standalone_google_app_patch_classes(classes), [])


if __name__ == '__main__':
    unittest.main()
