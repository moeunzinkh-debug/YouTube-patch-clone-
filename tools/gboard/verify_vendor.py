#!/usr/bin/env python3
"""Verify that the tracked Gboard source is exactly the pinned upstream Git tree."""

import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PREFIX = "extras/gboard-patches/"
EXPECTED_TREE = "b8dc2c76f8a17259c2e3eaa6b9f8565fb19d730b"
EXPECTED_FILES = 913


def git(*args: str, env=None, input_bytes=None) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], env=env, input=input_bytes)


def main() -> None:
    # Tracked files only: running Gradle locally should not make ignored build
    # outputs part of the comparison. The temporary index leaves the user's
    # normal staging area untouched and honors Git's text/eol attributes.
    files = git("ls-files", "-z", "--", PREFIX)
    paths = [path for path in files.split(b"\0") if path]
    if len(paths) != EXPECTED_FILES:
        raise SystemExit(f"Expected {EXPECTED_FILES} tracked Gboard files, got {len(paths)}")
    with tempfile.TemporaryDirectory(prefix="gboard-tree-") as directory:
        env = os.environ.copy()
        env["GIT_INDEX_FILE"] = str(Path(directory) / "index")
        git("read-tree", "--empty", env=env)
        git("add", "-f", "--pathspec-from-file=-", "--pathspec-file-nul", env=env, input_bytes=files)
        actual = git("write-tree", f"--prefix={PREFIX}", env=env).decode().strip()
    if actual != EXPECTED_TREE:
        raise SystemExit(f"Gboard source tree mismatch: expected {EXPECTED_TREE}, got {actual}")
    print(f"Verified {len(paths)} upstream files and Git tree {actual}")


if __name__ == "__main__":
    main()
