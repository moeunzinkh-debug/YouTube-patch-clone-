#!/usr/bin/env python3
"""Synthetic Android-emulator checks; never reads real user input or publishes an APK."""
from __future__ import annotations

import argparse
import base64
import gzip
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "com.google.android.inputmethod.latin"


def run(*command: str, timeout: int = 60) -> str:
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=timeout, check=False)
    if result.returncode:
        # Surface only a stage and a constrained error code/type; never publish
        # response bodies, emulator logcat, or arbitrary command output.
        program = Path(command[0]).name
        stage = program
        if program == "adb":
            stage += " " + ("app_process" if "app_process" in command else command[1])
        code = re.search(r"\bINSTALL_FAILED_[A-Z0-9_]+\b", result.stdout)
        exception = re.search(r"\b(?:[a-zA-Z_][\w$]*\.)*[a-zA-Z_][\w$]*(?:Exception|Error)\b", result.stdout)
        compile_error = re.search(r"error: ([A-Za-z0-9_ .-]{1,100})", result.stdout) if program in ("javac", "d8") else None
        detail = code.group(0) if code else exception.group(0) if exception else compile_error.group(1) if compile_error else None
        suffix = f" [{detail}]" if detail else ""
        raise RuntimeError(f"{stage} failed (exit {result.returncode}){suffix}")
    return result.stdout.strip()


def dump_ui() -> str:
    run("adb", "shell", "uiautomator", "dump", "/sdcard/gboard-smoke-window.xml", timeout=45)
    return run("adb", "exec-out", "cat", "/sdcard/gboard-smoke-window.xml", timeout=20)


def publish_synthetic_ui(xml: str, label: str) -> None:
    # Fresh emulator, no account or user input. Compress annotations in small
    # chunks for temporary debugging; no APKs or full logcat are uploaded.
    packed = base64.b64encode(gzip.compress(xml.encode("utf-8"))).decode("ascii")
    chunks = [packed[i:i + 2800] for i in range(0, len(packed), 2800)]
    if len(chunks) > 15:
        print(f"::notice::{label}: synthetic UI tree too large to annotate")
        return
    for index, chunk in enumerate(chunks, 1):
        print(f"::notice::{label} {index}/{len(chunks)} {chunk}")


def center(bounds: str) -> tuple[int, int] | None:
    match = re.fullmatch(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds or "")
    if not match:
        return None
    x1, y1, x2, y2 = map(int, match.groups())
    return ((x1 + x2) // 2, (y1 + y2) // 2) if x2 > x1 and y2 > y1 else None


def tap_search(xml: str) -> bool:
    nodes = list(ET.fromstring(xml).iter("node"))
    for node in nodes:
        description = (node.get("content-desc", "") + " " + node.get("text", "")).lower()
        identifier = node.get("resource-id", "").lower()
        if "search" not in description and "search" not in identifier:
            continue
        position = center(node.get("bounds", ""))
        if position:
            run("adb", "shell", "input", "tap", str(position[0]), str(position[1]))
            return True
    return False


def synthetic_http_probe() -> None:
    sdk = Path(os.environ["ANDROID_HOME"])
    android_jar = sdk / "platforms/android-35/android.jar"
    tools = sorted((sdk / "build-tools").glob("*/d8"), reverse=True)
    if not android_jar.is_file() or not tools:
        raise RuntimeError("Required Android SDK platform or D8 not found")
    with tempfile.TemporaryDirectory(prefix="gboard-android-probe-") as directory:
        tmp = Path(directory)
        classes, dex = tmp / "classes", tmp / "dex"
        classes.mkdir()
        dex.mkdir()
        source = ROOT / "tools/gboard-translate/overlay/extensions/extension/src/main/java/dev/jason/gboardpatches/extension/directtranslate"
        run("javac", "-source", "8", "-target", "8", "-encoding", "UTF-8", "-cp", str(android_jar),
            "-d", str(classes), str(source / "GtxClient.java"), str(source / "TranslateCoordinator.java"),
            str(ROOT / "tools/gboard-translate/AndroidSyntheticProbe.java"), timeout=90)
        class_files = sorted(map(str, classes.rglob("*.class")))
        if not class_files:
            raise RuntimeError("Probe compilation generated no classes")
        run(str(tools[0]), "--min-api", "26", "--lib", str(android_jar), "--output", str(dex),
            *class_files, timeout=90)
        jar = tmp / "synthetic-probe.jar"
        with zipfile.ZipFile(jar, "w") as archive:
            archive.write(dex / "classes.dex", "classes.dex")
        run("adb", "push", str(jar), "/data/local/tmp/gboard-synthetic-probe.jar")
        output = run("adb", "shell", "CLASSPATH=/data/local/tmp/gboard-synthetic-probe.jar",
                     "app_process", "/system/bin",
                     "dev.jason.gboardpatches.extension.directtranslate.AndroidSyntheticProbe", timeout=90)
        expected = {"PASS synthetic Android POST en-to-km", "PASS synthetic Android POST km-to-en",
                    "PASS synthetic Android POST auto-to-km"}
        if set(output.splitlines()) != expected:
            raise RuntimeError("Android synthetic probe did not report all three checks")
        print("::notice::Android emulator Java client passed synthetic POST in both directions and auto mode.")


def gboard_ime_smoke(apk: Path, report: dict) -> None:
    run("adb", "install", "-r", str(apk), timeout=180)
    report["fixture_install"] = "passed"
    methods = run("adb", "shell", "ime", "list", "-s", "-a")
    candidates = [line.strip() for line in methods.splitlines() if line.strip().startswith(PACKAGE + "/")]
    if len(candidates) != 1:
        raise RuntimeError("Expected one Gboard IME component in the emulator")
    ime = candidates[0]
    run("adb", "shell", "ime", "enable", ime)
    run("adb", "shell", "ime", "set", ime)
    run("adb", "shell", "settings", "put", "secure", "show_ime_with_hard_keyboard", "1")
    if run("adb", "shell", "settings", "get", "secure", "default_input_method") != ime:
        raise RuntimeError("Gboard was not selected as the emulator IME")
    report["ime_enable_and_select"] = "passed"
    run("adb", "shell", "am", "start", "-a", "android.settings.SETTINGS")
    time.sleep(4)
    first = dump_ui()
    if not tap_search(first):
        publish_synthetic_ui(first, "GBOARD_SETTINGS_UI")
        raise RuntimeError("Could not locate the emulator Settings search control")
    time.sleep(5)
    pid = run("adb", "shell", "pidof", PACKAGE)
    if not re.fullmatch(r"[0-9 ]+", pid):
        raise RuntimeError("Gboard process did not start")
    report["ime_process_started"] = "passed"
    dump = run("adb", "shell", "dumpsys", "input_method", timeout=30)
    visible = any(marker in dump for marker in ("mInputShown=true", "isInputViewShown=true", "mShowRequested=true"))
    report["keyboard_visibility_signal"] = "passed" if visible else "not confirmed"
    ui = dump_ui()
    publish_synthetic_ui(ui, "GBOARD_KEYBOARD_UI")
    # Opening the Translate UI is attempted only by a visible accessibility
    # label; failure here is not treated as a successful Translate test.
    for node in ET.fromstring(ui).iter("node"):
        label = (node.get("content-desc", "") + " " + node.get("text", "")).lower()
        if "translate" not in label:
            continue
        position = center(node.get("bounds", ""))
        if position:
            run("adb", "shell", "input", "tap", str(position[0]), str(position[1]))
            time.sleep(3)
            publish_synthetic_ui(dump_ui(), "GBOARD_TRANSLATE_UI")
            report["translate_button_tapped"] = "attempted; translation not yet asserted"
            break
    print("::notice::Third-party-derived Gboard fixture installed and its IME process started in an emulator.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture_apk", type=Path)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    report = {
        "environment": "Android emulator only, not the user's device or network",
        "apk": "third-party prepatched fixture with test-only manifest package change; not stock",
        "synthetic_android_java_https": "not run", "fixture_install": "not run",
        "ime_enable_and_select": "not run", "ime_process_started": "not run",
        "keyboard_visibility_signal": "not run", "translate_ui_functionality": "not tested",
        "translate_button_tapped": "not located",
    }
    failed = False
    try:
        report["android_api"] = run("adb", "shell", "getprop", "ro.build.version.sdk")
        report["android_abi_list"] = run("adb", "shell", "getprop", "ro.product.cpu.abilist")
        try:
            synthetic_http_probe()
            report["synthetic_android_java_https"] = "passed"
        except (RuntimeError, subprocess.TimeoutExpired, OSError) as error:
            report["synthetic_android_java_https"] = "failed or unavailable"
            report["synthetic_error"] = str(error)
            print(f"::warning::Android synthetic client probe failed: {type(error).__name__}: {error}")
            failed = True
        try:
            gboard_ime_smoke(args.fixture_apk, report)
        except (RuntimeError, subprocess.TimeoutExpired, OSError, ET.ParseError) as error:
            report["ime_smoke_error"] = str(error)
            print(f"::warning::Android fixture IME smoke could not complete: {type(error).__name__}: {error}")
            failed = True
    finally:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
