#!/usr/bin/env python3
"""Compare the published SimSimi APK candidate with the pinned original base.

The report contains only fixed identifiers, hashes and boolean hook findings.
It never executes either APK or records app/user data.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

from androguard.core.apk import APK
from androguard.core.dex import DEX
from loguru import logger

logger.remove()
PACKAGE = "com.ismaker.android.simsimi"
VERSION = "9.2.3"
CODE = "1119001"
ORIGINAL_SHA256 = "f18da384232c8e918e1073fd2e95cde6dda9bda2a34f4f90bb527ca95ea8af70"
ACTIVITY = "Lcom/ismaker/android/simsimi/MainActivity;"
PULL = "Lapp/morphe/extension/simsimi/PullRefresh;"
SCREEN = "Lapp/morphe/extension/simsimi/ConversationScreen;"
QUICK = "Lapp/morphe/extension/simsimi/QuickReturn;"
TAPS = "Lapp/morphe/extension/simsimi/ChatTabDoubleTap;"
HOOK = PULL + "->onTouch("


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect(path: Path) -> dict:
    apk = APK(str(path))
    identity = (apk.get_package(), apk.get_androidversion_name(), apk.get_androidversion_code())
    if identity != (PACKAGE, VERSION, CODE):
        raise ValueError(f"Unexpected APK identity: {identity}")
    result = {
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
        "package": identity[0],
        "version_name": identity[1],
        "version_code": identity[2],
        "main_activity_dispatch_calls_pull_refresh": False,
        "any_method_calls_pull_refresh_on_touch": False,
        "pull_refresh_on_touch_call_count": 0,
        "pull_refresh_class_present": False,
        "conversation_screen_guard_class_present": False,
        "pull_refresh_has_reload_method": False,
        "pull_refresh_calls_reload": False,
        "pull_refresh_fixed_reload_labels_present": False,
        "quick_return_class_present": False,
        "double_tap_class_present": False,
    }
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not re.fullmatch(r"classes\d*\.dex", name):
                continue
            dex = DEX(archive.read(name))
            for cls in dex.get_classes():
                owner = cls.get_name()
                result["pull_refresh_class_present"] |= owner == PULL
                result["conversation_screen_guard_class_present"] |= owner == SCREEN
                result["quick_return_class_present"] |= owner == QUICK
                result["double_tap_class_present"] |= owner == TAPS
                for method in cls.get_methods():
                    if owner == PULL and method.get_name() == "reload":
                        result["pull_refresh_has_reload_method"] = True
                    if not method.get_code():
                        continue
                    outputs = [instruction.get_output() for instruction in method.get_instructions()]
                    calls = sum(HOOK in value for value in outputs)
                    result["pull_refresh_on_touch_call_count"] += calls
                    result["any_method_calls_pull_refresh_on_touch"] |= calls > 0
                    if owner == ACTIVITY and method.get_name() == "dispatchTouchEvent":
                        result["main_activity_dispatch_calls_pull_refresh"] |= calls > 0
                    if owner == PULL:
                        result["pull_refresh_calls_reload"] |= any(PULL + "->reload(" in value for value in outputs)
                        fixed = ("SimSimi pull-to-reload patch", "Reloading Conversation")
                        result["pull_refresh_fixed_reload_labels_present"] |= all(
                            any(label in value for value in outputs) for label in fixed
                        )
    return result


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: inspect_patched_release.py ORIGINAL CANDIDATE REPORT")
    original, candidate, output = map(Path, sys.argv[1:])
    old, new = inspect(original), inspect(candidate)
    if old["sha256"] != ORIGINAL_SHA256:
        raise ValueError("Original release base hash changed")
    hook_keys = (
        "main_activity_dispatch_calls_pull_refresh",
        "any_method_calls_pull_refresh_on_touch",
        "pull_refresh_class_present",
        "conversation_screen_guard_class_present",
        "pull_refresh_has_reload_method",
        "pull_refresh_calls_reload",
    )
    report = {
        "scope": "Static comparison of two public release APK assets; neither APK was installed or executed",
        "original_asset": old,
        "candidate_asset": new,
        "original_has_no_pull_reload_hook": not any(old[key] for key in hook_keys),
        "candidate_has_complete_pull_reload_hook": all(new[key] for key in hook_keys),
        "causality": "A hook can be present statically, but the exact device trigger requires an A/B runtime test",
        "accounts_network_or_private_data_used": False,
    }
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
