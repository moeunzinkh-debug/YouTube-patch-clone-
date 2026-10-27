#!/usr/bin/env python3
"""Read-only upstream discovery; recommend only the pinned source's profiles.

No APKs, profiles, source files or compiled bundles are updated by this tool.
Network failures abort before either generated output is written.
"""
import argparse
import json
import os
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
VENDOR = ROOT / 'extras/gemini-microg-patches'
REPO = 'ryuya0124/gemini-microg-patches'


def api(path):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'gemini-version-advisor'}
    if os.environ.get('GITHUB_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['GITHUB_TOKEN']
    req = urllib.request.Request('https://api.github.com/' + path, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def discover():
    # Pin every request to the same immutable upstream commit.
    commit = api(f'repos/{REPO}/commits/HEAD')['sha']
    tree = api(f'repos/{REPO}/git/trees/{commit}?recursive=1')
    if tree.get('truncated'):
        raise ValueError('Incomplete upstream tree; refusing partial catalog')
    targets = json.loads((HERE / 'targets.json').read_text())
    profiles = {}
    for key, target in targets.items():
        prefix = f"docs/versions/{target['package']}/"
        profiles[key] = sorted(item['path'][len(prefix):-5] for item in tree['tree']
                               if item['path'].startswith(prefix) and item['path'].endswith('.json'))
    return {'commit': commit, 'profile_versions': profiles}


def build(remote=None):
    source = json.loads((VENDOR / 'SOURCE.json').read_text())
    targets = json.loads((HERE / 'targets.json').read_text())
    rows = []
    for key, target in targets.items():
        profiles = []
        for path in sorted((VENDOR / 'docs/versions' / target['package']).glob('*.json')):
            profile = json.loads(path.read_text())
            if profile['packageName'] != target['package']:
                raise ValueError('Profile package mismatch')
            profiles.append(profile['versionName'])
        if key == 'microg':
            # The snapshot's pinned compatibility declaration, not a latest-release guess.
            match = re.search(r'app\.revanced\.android\.gms\s+(\d+\.\d+\.\d+)', source['description'])
            if not match:
                raise ValueError('Missing pinned MicroG compatibility declaration')
            profiles = [match.group(1)]
        supported = target['requested'] in profiles
        rows.append(dict(target, id=key, source_profile_versions=profiles,
                         active_target=target['requested'],
                         recommended_for_reference=None,
                         requested_status='in-pinned-source' if supported else 'unverified',
                         upstream_profile_versions=(remote or {}).get('profile_versions', {}).get(key, [])))
    return {'schema_version': 2, 'project': 'gemini-microg', 'target_policy': 'user-pinned', 'source_tag': source['upstream_tag'],
            'source_commit': source['upstream_commit'], 'compiled_gemini_support': False,
            'upstream_discovery': remote, 'apps': rows}


def markdown(data):
    lines = ['# Gemini / Google / MicroG RE version recommendations', '',
             '> Gemini-only project targets. No shared YouTube compatibility or release configuration.',
             '> កំណែគោលដៅមិនមែនជាកំណែដែលបានផ្ទៀងផ្ទាត់ទេ។', '',
             '| App | Active patch target | Verified recommendation | Target status |',
             '| --- | --- | --- | --- |']
    for app in data['apps']:
        lines.append(f"| {app['name']} | `{app['requested']}` | `{app['recommended_for_reference'] or 'pending APK and runtime verification'}` | {app['requested_status']} |")
    lines += ['', 'The active targets are user-pinned and are never replaced with older upstream versions.',
              'Legacy source snapshot `' + data['source_tag'] + '` is reference material, not verification of these targets.',
              'Do not combine independently discovered versions as a verified working set.',
              'New upstream profile filenames are discovery metadata, not compatibility proof.',
              'MicroG release numbers are not auto-promoted: this snapshot declares only its pinned version.', '',
              '## Upstream discovery', '']
    remote = data['upstream_discovery']
    if remote:
        lines.append('Checked upstream commit: `' + remote['commit'] + '`.')
        for app in data['apps']:
            lines.append('- ' + app['name'] + ': ' + (', '.join(app['upstream_profile_versions']) or 'no app profile published'))
    else:
        lines.append('Offline generation; upstream discovery has not been performed.')
    lines += ['', '## Automatic updates', '',
              'GitHub Actions checks every six hours and on manual dispatch. Failures leave the catalog unchanged.',
              'Run `python3 tools/gemini-version-advisor/update.py` online or add `--offline` for local-only generation.',
              'Targets are configured in `tools/gemini-version-advisor/targets.json`.',
              'Updating recommendations requires a reviewed source snapshot, exact APK profiles/hashes and runtime validation.',
              'This job never edits the vendored source, builds Gemini patches, downloads APKs, or claims device testing.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    data = build(None if args.offline else discover())
    (HERE / 'versions.json').write_text(json.dumps(data, indent=2) + '\n')
    (ROOT / 'docs/gemini-versions.md').write_text(markdown(data))


if __name__ == '__main__':
    main()
