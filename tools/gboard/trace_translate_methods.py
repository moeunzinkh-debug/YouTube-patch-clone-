#!/usr/bin/env python3
"""Emit a limited redacted DEX trace for Translate interoperability research.

The trace is ephemeral CI diagnostic output, not an APK, DEX, or user data.
All app string literals are redacted except a small allowlist of protocol words.
"""

import base64
import gzip
import re
import sys
from zipfile import ZipFile

from loguru import logger

logger.remove()
from androguard.core.dex import DEX  # noqa: E402

DEX_NAME = re.compile(r"classes(?:[2-9]|[1-9][0-9]+)?\.dex\Z")
TARGETS = {
    "Lkjx;": {"a", "b"},
    "Lkkp;": {"d", "e", "ho"},
    "Lklo;": {"al", "ap", "aj", "fL", "fN"},
    "Lkli;": {"a"},
    "Lkko;": {"e"},
    "Lklf;": {"a", "b"},
    "Lklg;": {"<init>"},
    "Labxb;": {"<init>"},
    "Lkkq;": {"a"},
    "Lkks;": {"a", "b"},
}
PUBLIC_LITERALS = {"", "auto", "q", "source", "target", "format", "text", "data", "translations", "translatedText", "detectedSourceLanguage"}


def trace(apk_path):
    lines = []
    found = set()
    with ZipFile(apk_path) as archive:
        for filename in sorted(name for name in archive.namelist() if DEX_NAME.fullmatch(name)):
            dex = DEX(archive.read(filename))
            for item in dex.get_classes():
                class_name = item.get_name()
                if class_name not in TARGETS:
                    continue
                found.add(class_name)
                for method in item.get_methods():
                    if method.get_name() not in TARGETS[class_name] or method.get_code() is None:
                        continue
                    lines.append(f"\n{class_name}->{method.get_name()}{method.get_descriptor()} ({filename})")
                    for offset, instruction in method.get_instructions_idx():
                        name = instruction.get_name()
                        output = instruction.get_output()
                        if name in ("const-string", "const-string/jumbo"):
                            value = dex.get_cm_string(instruction.get_ref_kind())
                            rendered = repr(value) if value in PUBLIC_LITERALS else "<redacted>"
                            output = output.split(",", 1)[0] + ", " + rendered
                        elif '"' in output or 'http:' in output.lower() or 'https:' in output.lower():
                            output = "<redacted>"
                        lines.append(f"{offset:04x} {name} {output}")
            del dex
    missing = set(TARGETS) - found
    if missing:
        raise ValueError("Missing target classes: " + ", ".join(sorted(missing)))
    return "\n".join(lines) + "\n"


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: trace_translate_methods.py APK")
    text = trace(sys.argv[1])
    # Annotations are intentionally transient; no copyrighted APK/DEX is checked in.
    encoded = base64.b64encode(gzip.compress(text.encode("utf-8"), mtime=0)).decode("ascii")
    chunks = [encoded[index:index + 6000] for index in range(0, len(encoded), 6000)]
    for index, chunk in enumerate(chunks):
        print(f"::notice title=Redacted Translate trace {index + 1}/{len(chunks)}::{chunk}")


if __name__ == "__main__":
    main()
