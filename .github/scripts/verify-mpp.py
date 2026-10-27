#!/usr/bin/env python3
"""Validate the compiled patch.mpp bundle committed to the repository.

Runs in CI (and locally) without any third-party dependency.
"""

from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "patch.mpp"
CHECKSUM = ROOT / "patch.mpp.sha256"


def check(condition: bool, message: str) -> None:
    status = "OK  " if condition else "FAIL"
    print(f"[{status}] {message}")
    if not condition:
        raise SystemExit(1)


def main() -> None:
    check(BUNDLE.is_file(), f"{BUNDLE.name} exists ({BUNDLE.stat().st_size if BUNDLE.exists() else 0} bytes)")
    check(CHECKSUM.is_file(), f"{CHECKSUM.name} exists")

    expected = CHECKSUM.read_text(encoding="utf-8").split()[0]
    digest = hashlib.sha256(BUNDLE.read_bytes()).hexdigest()
    check(digest == expected, f"SHA-256 matches: {digest}")

    with zipfile.ZipFile(BUNDLE) as archive:
        check(archive.testzip() is None, "ZIP/JAR structure is intact")
        names = archive.namelist()
        check(len(names) > 1000, f"archive has {len(names)} entries")

        manifest = archive.read("META-INF/MANIFEST.MF").decode("utf-8", "replace")
        for field in ("Version:", "Patcher-Version:", "Name:"):
            present = field in manifest
            value = manifest.split(field, 1)[1].splitlines()[0].strip() if present else ""
            check(present, f"MANIFEST.MF declares {field} {value}".strip())

        classes = [n for n in names if n.endswith(".class")]
        youtube = [n for n in classes if n.startswith("app/morphe/patches/youtube/")]
        check(len(classes) > 1000, f"{len(classes)} compiled patch classes")
        check(len(youtube) > 500, f"{len(youtube)} YouTube patch classes")
        check(
            not any(n.startswith(("app/morphe/patches/music/", "app/morphe/patches/reddit/")) for n in classes),
            "no excluded Music/Reddit patch classes",
        )

        extensions = [n for n in names if n.endswith(".mpe")]
        check(len(extensions) >= 3, f"extension DEX files: {', '.join(extensions)}")
        for name in extensions:
            check(archive.read(name).startswith(b"dex\n"), f"{name} is a DEX file")

        youtube_dex = archive.read("extensions/youtube.mpe")
        check(b"KhmerTtsClient" in youtube_dex, "Khmer voice-over client compiled into extensions/youtube.mpe")
        check(b"openapi.json" in youtube_dex, "FastAPI OpenAPI discovery compiled into extensions/youtube.mpe")

    print("\npatch.mpp is a valid Morphe patch bundle.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, zipfile.BadZipFile) as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        raise SystemExit(1) from error
