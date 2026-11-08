#!/usr/bin/env python3
"""Find a successful branch workflow run with identical source paths to HEAD."""
from __future__ import annotations
import json
import subprocess
import sys


def main() -> None:
    if len(sys.argv) < 4:
        raise SystemExit('Usage: find_successful_run.py BRANCH WORKFLOW PATH [PATH ...]')
    branch, workflow, *paths = sys.argv[1:]
    rows = json.loads(subprocess.check_output([
        'gh', 'run', 'list', '--workflow', workflow, '--branch', branch,
        '--limit', '60', '--json', 'databaseId,status,conclusion,headSha',
    ], text=True))
    def tree(commit: str, path: str) -> str:
        return subprocess.check_output(['git', 'rev-parse', f'{commit}:{path}'], text=True, stderr=subprocess.DEVNULL).strip()
    expected = [tree('HEAD', path) for path in paths]
    for row in rows:
        if row['status'] != 'completed' or row['conclusion'] != 'success':
            continue
        try:
            if [tree(row['headSha'], path) for path in paths] == expected:
                print(row['databaseId'])
                return
        except subprocess.CalledProcessError:
            continue
    raise SystemExit(f'No successful {workflow} run matches the current source')

if __name__ == '__main__':
    main()
