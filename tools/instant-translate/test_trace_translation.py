#!/usr/bin/env python3
"""Privacy and anchor tests for translation diagnostics."""
import unittest
import trace_translation as tracer


class FakeInstruction:
    def __init__(self, name, value):
        self.name, self.value = name, value

    def get_name(self):
        return self.name

    def get_output(self):
        return self.value


class TraceTests(unittest.TestCase):
    def test_hostname_only_from_translation_related_url(self):
        self.assertEqual(tracer.output_host('https://example.com/v1/translate?key=secret'), 'example.com')
        self.assertIsNone(tracer.output_host('https://example.com/no-keyword?foo=secret'))
        self.assertIsNone(tracer.output_host('https://127.0.0.1/translate'))
        self.assertIsNone(tracer.output_host('https://[invalid/translate'))
        self.assertIsNone(tracer.output_host('no endpoint'))

    def test_resource_lookup_initializes_lazy_resource_table(self):
        class FakeResources:
            ready = False
            def get_packages_names(self):
                return ['com.spaceship.screen.translate']
            def get_string_resources(self, package):
                self.ready = True
            def get_res_id_by_key(self, package, kind, name):
                return 0x7f120123 if self.ready and name == 'translate_failed' else None
        class FakeApk:
            def get_android_resources(self):
                return FakeResources()
        self.assertEqual(tracer.collect_resource_ids(FakeApk())['translate_failed'], 0x7f120123)

    def test_instruction_string_and_url_redacted(self):
        self.assertEqual(tracer.sanitize_instruction(FakeInstruction('const-string', 'v0, https://x.y/key?api=secret'))['value'], '<redacted>')
        self.assertEqual(tracer.sanitize_instruction(FakeInstruction('const-string', 'v0, Translation failed plus private'))['value'], 'Translation failed')
        self.assertEqual(tracer.sanitize_instruction(FakeInstruction('invoke-static', 'v1, Lx;->run()V'))['value'], 'v1,Lx;->run()V')
        self.assertEqual(tracer.sanitize_instruction(FakeInstruction('other', '"hidden"'))['value'], '<redacted>')


if __name__ == '__main__':
    unittest.main()
