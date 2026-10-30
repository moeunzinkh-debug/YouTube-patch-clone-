#!/usr/bin/env python3
"""Evaluate a disposable emulator's synthetic Spanish-to-English fixture."""
import hashlib
import json
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit('usage: check_runtime.py PRODUCT.json FORCED.json OUT.json')
    product, forced = (json.loads(Path(path).read_text()) for path in sys.argv[1:3])
    for name, report in [('product', product), ('forced', forced)]:
        stages = {str(screen['stage']): screen for screen in report.get('screens', [])}
        if not report.get('process_alive') or report.get('app_fatal_exception') or report.get('crash_dialog_seen'):
            raise ValueError(name + ' app failed to stay running or crashed')
        if not report.get('fixture_submitted') or 'fixture_submitted' not in stages:
            raise ValueError(name + ' did not submit the synthetic fixture')
        selected = stages.get('source_selected', {})
        if selected.get('routine_button_clicked') != 'Spanish':
            raise ValueError(name + ' did not select the fixed source language')
    final = next(screen for screen in forced['screens'] if screen['stage'] == 'fixture_submitted')
    labels = [(node.get('label') or '').strip() for node in final.get('nodes', [])
              if node.get('class') != 'android.widget.EditText']
    matched = [label for label in labels if label.lower().strip(' .!?') in {'hello', 'hi'}]
    if not matched:
        print('Forced-failure fixture labels:', ' | '.join(label for label in labels if label)[:1500])
        raise ValueError('Forced original failure did not yield the expected Google fallback translation')
    bundle = Path(__file__).resolve().parents[2] / 'bundles/instant-translate/bundle.mpp'
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    if digest != bundle.with_name('bundle.mpp.sha256').read_text().split()[0]:
        raise ValueError('Bundle checksum changed during runtime testing')
    result = {
        'scope': 'Disposable Android 15 google_apis x86_64 with ARM64 native bridge; synthetic Spanish hola to English only',
        'bundle_sha256': digest,
        'product_apk_launch_and_fixture': 'passed',
        'ci_only_forced_original_failure': True,
        'fallback_translated_fixture': True,
        'matched_translation': matched[0],
        'no_user_text_or_account': True,
        'original_model_and_offline_repair': 'not tested or claimed',
        'other_sections_languages_and_devices': 'not tested',
    }
    Path(sys.argv[3]).write_text(json.dumps(result, indent=2) + '\n')
    print('Forced native failure produced a synthetic Google fallback translation')


if __name__ == '__main__':
    main()
