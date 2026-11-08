#!/usr/bin/env python3
"""Publish one small, sanitized JSON report as retrievable CI annotations."""
import argparse
import base64
import gzip
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path)
    parser.add_argument('prefix', choices=('KING_INVENTORY', 'KING_MENU_TRACE', 'KING_API_TRACE'))
    args = parser.parse_args()
    data = base64.b64encode(gzip.compress(args.path.read_bytes())).decode('ascii')
    chunks = [data[index:index + 3900] for index in range(0, len(data), 3900)]
    if not chunks or len(chunks) > 10:
        raise SystemExit('One CI step may emit at most ten annotation chunks')
    for number, chunk in enumerate(chunks, 1):
        print(f'::notice::{args.prefix} {number}/{len(chunks)} {chunk}')


if __name__ == '__main__':
    main()
