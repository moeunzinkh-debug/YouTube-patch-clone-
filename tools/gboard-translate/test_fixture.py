#!/usr/bin/env python3
"""Offline tests for the temporary binary-manifest-only fixture."""
import struct
import unittest
import make_manifest_fixture as fixture


def xml_with_pool(utf8: bool, values: list[str]) -> bytes:
    offsets, strings = [], bytearray()
    for text in values:
        offsets.append(len(strings))
        if utf8:
            raw = text.encode("utf-8")
            units = len(text.encode("utf-16le")) // 2
            strings.extend(bytes([units, len(raw)]) + raw + b"\0")
        else:
            raw = text.encode("utf-16le")
            strings.extend(struct.pack("<H", len(raw) // 2) + raw + b"\0\0")
    while len(strings) % 4:
        strings.append(0)
    start = 28 + len(values) * 4
    pool = struct.pack("<HHIIIIII", 1, 28, start + len(strings), len(values), 0,
                       0x100 if utf8 else 0, start, 0)
    pool += b"".join(struct.pack("<I", offset) for offset in offsets) + strings
    return struct.pack("<HHI", 3, 8, len(pool) + 8) + pool


class ManifestFixtureTest(unittest.TestCase):
    def test_utf8_and_utf16_rewrite_in_place(self):
        for utf8 in (True, False):
            with self.subTest(utf8=utf8):
                original = xml_with_pool(utf8, ["unrelated", fixture.OLD, "last"])
                changed = fixture.replace_manifest_package(original)
                self.assertEqual(len(changed), len(original))
                encoding = "utf-8" if utf8 else "utf-16le"
                self.assertIn(fixture.NEW.encode(encoding), changed)
                self.assertNotIn(fixture.OLD.encode(encoding), changed)
                self.assertIn("last".encode(encoding), changed)
                self.assertEqual(changed[:8], original[:8])

    def test_fails_closed_on_missing_duplicate_or_bad_header(self):
        for values in (["not-the-package"], [fixture.OLD, fixture.OLD]):
            with self.assertRaises(ValueError):
                fixture.replace_manifest_package(xml_with_pool(True, values))
        with self.assertRaises(ValueError):
            fixture.replace_manifest_package(b"not an apk")


if __name__ == "__main__":
    unittest.main(verbosity=2)
