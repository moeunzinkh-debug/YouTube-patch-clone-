#!/usr/bin/env python3
"""Expose part of a sanitized read-only scan as check-run annotations."""
import base64
import gzip
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        raise SystemExit('usage: emit_current_report.py REPORT PART')
    report, part = Path(sys.argv[1]), int(sys.argv[2])
    encoded = base64.b64encode(gzip.compress(report.read_bytes(), mtime=0)).decode()
    chunks = [encoded[i:i+3500] for i in range(0, len(encoded), 3500)]
    if len(chunks) > 56 or not 0 <= part < 8:
        raise SystemExit('Sanitized report exceeds available annotation slots')
    for index in range(part * 7, min((part + 1) * 7, len(chunks))):
        print(f'::notice::INSTANT_CURRENT_SCAN {index+1}/{len(chunks)} {chunks[index]}')


if __name__ == '__main__': main()
