#!/usr/bin/env python3
"""Verify injected DEX calls in the rebuilt third-party-derived fixture, not an Android runtime test."""
from __future__ import annotations
import argparse
from pathlib import Path
from loguru import logger
from androguard.core.apk import APK
from androguard.core.dex import DEX

logger.remove()
RUNTIME = "Ldev/jason/gboardpatches/extension/directtranslate/GboardDirectTranslateRuntime;"
CLIENT = "Ldev/jason/gboardpatches/extension/directtranslate/GtxClient;"
TARGETS = {
    ("Lkkp;", "e", "(Lklg;Lkkc;)V"),
    ("Lkka;", "d", "(Lklg;Lkkc;)V"),
    ("Lklo;", "ap", "()Z"),
    ("Lklo;", "al", "(Ljava/lang/String;)V"),
    ("Lklo;", "fL", "()V"),
    ("Lklo;", "fN", "()V"),
    ("Lphr;", "onFinishInputView", "(Z)V"),
    ("Lphr;", "onFinishInput", "()V"),
    ("Lphr;", "onWindowHidden", "()V"),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    parser.add_argument("--package", default="com.google.android.inputmethod.latin")
    args = parser.parse_args()
    apk = APK(str(args.apk))
    if apk.get_package() != args.package or apk.get_androidversion_code() != "176049702":
        raise SystemExit("Unexpected test fixture metadata")
    if apk.get_androidversion_name() != "18.5.4.993608717-release-arm64-v8a":
        raise SystemExit("Unexpected fixture version")
    bodies: dict[tuple[str, str, str], str] = {}
    classes: set[str] = set()
    wrapper_field_access: str | None = None
    for dex_bytes in apk.get_all_dex():
        dex = DEX(dex_bytes)
        for cls in dex.get_classes():
            owner = cls.get_name()
            if owner in {RUNTIME, CLIENT}:
                classes.add(owner)
            if owner == "Lkka;":
                matches = [field for field in cls.get_fields() if field.get_name() == "f" and field.get_descriptor() == "Lkkd;"]
                if len(matches) != 1:
                    raise SystemExit("Expected exactly one cloud-provider wrapper field")
                wrapper_field_access = matches[0].get_access_flags_string()
            if owner not in {target[0] for target in TARGETS}:
                continue
            for method in cls.get_methods():
                key = (owner, method.get_name(), method.get_descriptor().replace(" ", ""))
                if key in TARGETS:
                    if key in bodies or method.get_code() is None:
                        raise SystemExit(f"Duplicate or missing method body: {key}")
                    bodies[key] = "\n".join(
                        ins.get_name() + " " + ins.get_output().replace(" ", "")
                        for ins in method.get_code().get_bc().get_instructions()
                    )
    if set(bodies) != TARGETS or classes != {RUNTIME, CLIENT}:
        raise SystemExit("Expected patched methods or extension classes are missing")
    print(f"::notice::Reviewed native wrapper cloud field access: {wrapper_field_access or 'package-private'}")
    if wrapper_field_access is None or "private" in wrapper_field_access.split():
        raise SystemExit("Cloud-provider field cannot be accessed from the native readiness hook")
    checks = {
        ("Lkkp;", "e", "(Lklg;Lkkc;)V"): [RUNTIME + "->tryDispatch(", "Lkkp;->a(Lklg;)Lxqp;"],
        ("Lkka;", "d", "(Lklg;Lkkc;)V"): ["Lkli;", "Lkka;->fLkkd;", "Lkjx;", "Lkkd;->d(Lklg;Lkkc;)V"],
        ("Lklo;", "ap", "()Z"): ["Lkko;->cZ", "Lklo;->pLkkd;", "Lkjx;", "Lkko;->a(I)I"],
    }
    for key, markers in checks.items():
        if not all(marker in bodies[key] for marker in markers):
            raise SystemExit(f"Patched control flow marker missing for {key}")
    for key in TARGETS - set(checks):
        if RUNTIME + "->cancel()V" not in bodies[key]:
            raise SystemExit(f"Missing lifecycle/input cancellation for {key}")
    if RUNTIME + "->prepare(" not in bodies[("Lklo;", "al", "(Ljava/lang/String;)V")]:
        raise SystemExit("Missing exact request/callback preparation hook")
    print("Verified fork calls and guarded routing in the rebuilt third-party-derived DEX fixture.")
    print("This is not an original stock APK, a device test, or evidence that Translate works on Android.")


if __name__ == "__main__":
    main()
