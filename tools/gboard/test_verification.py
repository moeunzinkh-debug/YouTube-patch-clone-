#!/usr/bin/env python3
"""Regression tests for Gboard metadata and Morphe-list verification."""

import tempfile
import unittest
from pathlib import Path

import verify_bundle as verify


class GboardVerificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.names = verify.load_metadata()
        cls.listing = "\n\n".join(
            f"Name: {name}\nEnabled: true\nCompatible packages:\n"
            f"\tPackage name: {verify.EXPECTED_PACKAGE}\n\tCompatible versions:\n\t\t{verify.EXPECTED_TARGET}"
            for name in cls.names
        )

    def test_complete_listing_passes(self):
        verify.verify_cli_output(self.listing, self.names)

    def test_missing_patch_is_rejected(self):
        with self.assertRaises(ValueError):
            verify.verify_cli_output(self.listing.split("\n\n", 1)[1], self.names)

    def test_duplicate_patch_is_rejected(self):
        wrong = self.listing.replace("Name: " + self.names[1], "Name: " + self.names[0], 1)
        with self.assertRaises(ValueError):
            verify.verify_cli_output(wrong, self.names)

    def test_changed_default_is_rejected(self):
        with self.assertRaises(ValueError):
            verify.verify_cli_output(self.listing.replace("Enabled: true", "Enabled: false", 1), self.names)

    def test_wrong_package_or_version_is_rejected(self):
        for old, new in ((verify.EXPECTED_PACKAGE, "another.package"), (verify.EXPECTED_TARGET, "another.version")):
            with self.subTest(old=old), self.assertRaises(ValueError):
                verify.verify_cli_output(self.listing.replace(old, new, 1), self.names)

    def test_wrong_asset_is_rejected_even_if_size_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bundle.mpp"
            with path.open("wb") as handle:
                handle.truncate(verify.EXPECTED_SIZE)
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                verify.verify_asset(path)


if __name__ == "__main__":
    unittest.main()
