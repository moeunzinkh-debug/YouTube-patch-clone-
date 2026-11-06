#!/usr/bin/env python3
"""Build the bounded offline Khmerlish dictionary from the attributed MIT dataset.

Ambiguous spellings are deliberately excluded unless explicitly reviewed in
``overrides.tsv``. Unknown words stay unchanged; this is not a language model.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import gzip
import hashlib
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'data/eng_khm_data.txt.gz'
OVERRIDES = ROOT / 'data/overrides.tsv'
OUTPUT = ROOT / 'overlay/patches/src/main/resources/gboard-khmer/dictionary.tsv'
SOURCE_SHA256 = '20158d40982b4860c2072038f751610b22815983d7be445021e2bcbe04501550'
LATIN = re.compile(r'[a-z]{1,32}\Z')


def valid_khmer(value: str) -> bool:
    return bool(value) and any('\u1780' <= c <= '\u17ff' for c in value) and all(
        '\u1780' <= c <= '\u17ff' or c in ' \u200b\u200c\u200d' for c in value
    )


def make_dictionary() -> tuple[bytes, dict[str, int]]:
    source = gzip.decompress(SOURCE.read_bytes())
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA256:
        raise ValueError('Dataset is not the pinned upstream source')
    candidates: dict[str, set[str]] = defaultdict(set)
    for line in source.decode('utf-8').splitlines():
        khmer, sep, roman = line.partition(': ')
        key = roman.strip().lower()
        value = unicodedata.normalize('NFC', khmer.strip())
        if sep and LATIN.fullmatch(key) and valid_khmer(value):
            candidates[key].add(value)
    # Skip single-letter words and ambiguous homophones unless reviewed below.
    result = {key: next(iter(values)) for key, values in candidates.items()
              if len(key) > 1 and len(values) == 1}
    overrides = {}
    for line in OVERRIDES.read_text(encoding='utf-8').splitlines():
        if not line or line.startswith('#'):
            continue
        key, value = line.split('\t')
        if not LATIN.fullmatch(key) or not valid_khmer(value) or key in overrides:
            raise ValueError(f'Invalid or duplicate override: {line!r}')
        overrides[key] = unicodedata.normalize('NFC', value)
    result.update(overrides)
    output = ''.join(f'{key}\t{result[key]}\n' for key in sorted(result)).encode('utf-8')
    return output, {'source_lines': len(source.splitlines()), 'candidate_keys': len(candidates),
                    'excluded_ambiguous_keys': sum(len(v) > 1 for v in candidates.values()),
                    'overrides': len(overrides), 'entries': len(result)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='verify the checked-in output')
    args = parser.parse_args()
    data, stats = make_dictionary()
    if args.check:
        if OUTPUT.read_bytes() != data:
            raise SystemExit('Offline dictionary is stale; regenerate it with build_dictionary.py')
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_bytes(data)
    print(stats)
    print(f'dictionary bytes={len(data)} sha256={hashlib.sha256(data).hexdigest()}')


if __name__ == '__main__':
    main()
