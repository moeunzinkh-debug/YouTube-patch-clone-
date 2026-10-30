#!/usr/bin/env python3
import io
import unittest
import zipfile

from inspect_apks import DEX_NAME, apk_entries, safe_string


def archive(entries):
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w') as output:
        for name, content in entries:
            output.writestr(name, content)
    data.seek(0)
    return zipfile.ZipFile(data)


class InventoryTest(unittest.TestCase):
    def test_finds_base_and_split_without_extracting_untrusted_paths(self):
        with archive([('base.apk', b'base'), ('splits/config.arm64.apk', b'split'), ('icon.png', b'i')]) as z:
            self.assertEqual([i.filename for i in apk_entries(z)], ['base.apk', 'splits/config.arm64.apk'])

    def test_rejects_traversal_absolute_backslash_and_duplicates(self):
        for name in ('../base.apk', '/base.apk', 'nested\\base.apk'):
            with self.subTest(name=name), archive([(name, b'x')]) as z:
                with self.assertRaises(ValueError):
                    apk_entries(z)
        with self.assertWarns(UserWarning), archive([('base.apk', b'a'), ('base.apk', b'b')]) as z:
            with self.assertRaises(ValueError):
                apk_entries(z)

    def test_requires_apk_and_nonempty_data(self):
        for entries in ([('info.json', b'{}')], [('base.apk', b'')]):
            with self.subTest(entries=entries), archive(entries) as z:
                with self.assertRaises(ValueError):
                    apk_entries(z)

    def test_excludes_urls_and_secrets_from_sample(self):
        self.assertTrue(safe_string('License check failed'))
        for value in ('https://example.com/license', 'user@example.com license',
                      'License token=abc', 'password license', 'a' * 48, 'line\nbreak'):
            self.assertFalse(safe_string(value), value)

    def test_dex_names(self):
        for value in ('classes.dex', 'classes2.dex', 'classes10.dex', 'classes100.dex'):
            self.assertIsNotNone(DEX_NAME.fullmatch(value), value)
        for value in ('classes1.dex', 'classes0.dex', 'classes01.dex', 'nested/classes2.dex'):
            self.assertIsNone(DEX_NAME.fullmatch(value), value)


if __name__ == '__main__':
    unittest.main()
