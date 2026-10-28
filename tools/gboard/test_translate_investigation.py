#!/usr/bin/env python3
"""Tests for the privacy-conscious Translate diagnostics (no network access)."""

import io
import json
import re
import unittest
from pathlib import Path
from urllib.error import HTTPError
from zipfile import ZipFile

import investigate_translate as inventory
import probe_google_translate as probe


class Response(io.BytesIO):
    status = 200


class Opener:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.request = None

    def open(self, request, timeout):
        self.request = request
        if self.error:
            raise self.error
        return Response(self.response)


class TranslateInvestigationTest(unittest.TestCase):
    def test_probe_uses_fixed_languages_and_google_host(self):
        opener = Opener(json.dumps([[['សួស្តី', 'Hello world']]]).encode())
        result = probe.run_case(opener, probe.CASES[0])
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['sample_translation'], 'សួស្តី')
        self.assertTrue(opener.request.full_url.startswith('https://translate.googleapis.com/translate_a/single?'))
        self.assertEqual([(s['source'], s['target']) for s in probe.CASES], [('en', 'km'), ('km', 'en')])

    def test_http_failure_is_reported_not_silently_marked_success(self):
        error = HTTPError(probe.ENDPOINT, 429, 'Too Many Requests', {}, None)
        result = probe.run_case(Opener(error=error), probe.CASES[0])
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['http_status'], 429)

    def test_invalid_json_and_empty_response_are_errors(self):
        for content in (b'not json', b'[]', b'[[[""]]]'):
            self.assertEqual(probe.run_case(Opener(content), probe.CASES[0])['status'], 'error')

    def test_report_does_not_emit_secret_or_url_query(self):
        self.assertIsNone(inventory.safe_string('translate api_key=secret'))
        self.assertEqual(inventory.safe_string('https://translate.googleapis.com/a?key=secret'),
                         'https://translate.googleapis.com/a?[redacted]')
        self.assertIsNone(inventory.safe_string('not relevant'))
        self.assertIsNone(inventory.safe_string('translate\nprivate'))

    def test_dex_file_names(self):
        for name in ('classes.dex', 'classes2.dex', 'classes10.dex', 'classes100.dex'):
            self.assertIsNotNone(inventory.DEX_NAME.fullmatch(name))
        for name in ('classes1.dex', 'classes0.dex', 'some/classes.dex', 'classes.dex.txt'):
            self.assertIsNone(inventory.DEX_NAME.fullmatch(name))

    def test_real_dex_const_string_reference(self):
        root = Path(__file__).resolve().parents[2]
        with ZipFile(root / 'bundles/gboard/gboard-patches-4.0.0.mpp') as archive:
            data = archive.read('classes.dex')
        old_terms = inventory.TERMS
        old_focus = inventory.FOCUS_CLASSES
        try:
            inventory.TERMS = re.compile('IDENTITY', re.I)
            inventory.FOCUS_CLASSES = {'Lcom/google/gson/FieldNamingPolicy;'}
            result = inventory.inspect_dex(data, 'classes.dex')
        finally:
            inventory.TERMS = old_terms
            inventory.FOCUS_CLASSES = old_focus
        entry = next(item for item in result['strings'] if item['value'] == 'IDENTITY')
        self.assertGreater(entry['reference_count'], 0)
        self.assertTrue(any('FieldNamingPolicy' in ref['method'] for ref in entry['references']))
        focused = result['focused_types']
        self.assertEqual(len(focused), 1)
        self.assertTrue(any(method['invokes'] for method in focused[0]['methods'] if 'invokes' in method))


if __name__ == '__main__':
    unittest.main()
