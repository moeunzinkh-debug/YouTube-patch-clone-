"""Phone-model lookup and device-profile detection.

The advisor needs four facts to judge compatibility: Android SDK level, CPU
ABI, screen density and (optionally) RAM.  They can come from three sources:

1. a model in the bundled device database (``data/devices.json``),
2. automatic detection (browser user agent / ``adb shell getprop``),
3. manual values, which always override the guessed ones.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterable

from . import DEVICES_PATH
from .catalog import ANDROID_NAMES, android_name, load_json

ABI_PRIORITY = ("arm64-v8a", "armeabi-v7a", "x86_64", "x86", "mips64", "mips")
DENSITY_BUCKETS = (
    ("ldpi", 120),
    ("mdpi", 160),
    ("hdpi", 240),
    ("xhdpi", 320),
    ("xxhdpi", 480),
    ("xxxhdpi", 640),
)
ANDROID_TO_SDK = {
    "4.4": 19, "5": 21, "5.0": 21, "5.1": 22, "6": 23, "6.0": 23,
    "7": 24, "7.0": 24, "7.1": 25, "8": 26, "8.0": 26, "8.1": 27,
    "9": 28, "10": 29, "11": 30, "12": 31, "12l": 32, "12.1": 32,
    "13": 33, "14": 34, "15": 35, "16": 36,
}


class DeviceDetectionError(RuntimeError):
    """No usable device information was supplied or detected."""


def load_devices(path: Path | None = None) -> list[dict]:
    payload = load_json(Path(path or DEVICES_PATH))
    return payload.get("devices", [])


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(text or "").lower())


def sdk_from_android(android: str | int | None) -> int | None:
    if android is None or android == "":
        return None
    value = str(android).strip().lower()
    if value.isdigit() and int(value) > 36:  # already an SDK level
        return int(value)
    if value in ANDROID_TO_SDK:  # e.g. "8.1" before splitting to "8"
        return ANDROID_TO_SDK[value]
    match = re.match(r"^(\d+)(?:\.(\d+))?", value)
    if not match:
        return None
    major, minor = match.group(1), match.group(2)
    return ANDROID_TO_SDK.get(f"{major}.{minor}" if minor else None) or ANDROID_TO_SDK.get(major)


def android_from_sdk(sdk: int | None) -> str:
    if sdk is None:
        return "unknown"
    return ANDROID_NAMES.get(sdk, f"SDK {sdk}")


def dpi_bucket(dpi: int | float | None) -> str:
    try:
        value = float(dpi)
    except (TypeError, ValueError):
        return "nodpi"
    if value <= 0:
        return "nodpi"
    for name, maximum in DENSITY_BUCKETS:
        if value <= maximum:
            return name
    return "xxxhdpi"


def primary_abi(abis: Iterable[str] | None) -> str:
    values = [abi for abi in (abis or []) if abi]
    for preferred in ABI_PRIORITY:
        if preferred in values:
            return preferred
    return values[0] if values else "unknown"


def _tokens(text: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", str(text or "").lower()) if len(token) > 1}


def search_devices(query: str, limit: int = 8, devices: list[dict] | None = None) -> list[dict]:
    """Rank device database entries against a free-text model query."""
    devices = devices if devices is not None else load_devices()
    needle = normalize(query)
    if not needle:
        return devices[:limit]
    query_tokens = _tokens(query)
    scored: list[tuple[int, dict]] = []
    for device in devices:
        haystacks = [device["id"], device["name"], device["brand"], *device["models"], *device["aliases"]]
        best = 0
        for candidate in haystacks:
            value = normalize(candidate)
            if not value:
                continue
            if value == needle:
                best = max(best, 120)
            elif needle in value or value in needle:
                best = max(best, 90 + min(len(value), 20))
            elif query_tokens and query_tokens & _tokens(candidate):
                overlap = len(query_tokens & _tokens(candidate)) / max(len(query_tokens), 1)
                best = max(best, int(40 + 40 * overlap))
        if best:
            scored.append((best, device))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["name"]))
    return [device for _, device in scored[:limit]]


def resolve_device(query: str, devices: list[dict] | None = None) -> tuple[dict | None, dict]:
    """Resolve a model name / model code to a database entry and a match report."""
    results = search_devices(query, limit=1, devices=devices)
    if not results:
        return None, {"matched": False, "query": query, "confidence": 0}
    device = results[0]
    candidates = [device["name"], *device["models"], *device["aliases"], device["id"]]
    exact = any(normalize(candidate) == normalize(query) for candidate in candidates)
    return device, {
        "matched": True,
        "query": query,
        "deviceId": device["id"],
        "exact": exact,
        "confidence": 0.98 if exact else 0.72,
        "source": "database",
    }


def parse_user_agent(user_agent: str) -> dict:
    """Extract Android version and model code from a browser user agent."""
    ua = str(user_agent or "")
    info: dict = {"userAgent": ua, "model": None, "android": None, "sdk": None, "webView": "; wv" in ua or "Version/4.0" in ua}
    match = re.search(r"Android\s+([0-9]+(?:\.[0-9]+)?)", ua, re.IGNORECASE)
    if not match:
        return info  # desktop browser: never guess a phone model from "X11; Linux ..."
    info["android"] = match.group(1)
    info["sdk"] = sdk_from_android(match.group(1))
    parenthetical = re.search(r"\(([^)]*)\)", ua)
    if parenthetical:
        for raw in parenthetical.group(1).split(";"):
            segment = raw.strip()
            if not segment or segment.lower() in ("linux", "u", "wv", "android"):
                continue
            if re.search(r"^Android\s", segment, re.IGNORECASE):
                continue
            if re.fullmatch(r"[a-z]{2}([-_][a-zA-Z]{2})?", segment):
                continue  # locale, not a model
            segment = re.split(r"\s+Build[/ ]", segment, flags=re.IGNORECASE)[0].strip()
            if re.fullmatch(r"[A-Za-z0-9_.+\- ]{3,40}", segment) and not segment.lower().startswith("mobile"):
                info["model"] = segment
                break
    return info


def detect_adb(serial: str | None = None) -> dict:
    """Read a connected phone's real properties through ``adb shell getprop``."""
    if not shutil.which("adb"):
        raise DeviceDetectionError("adb was not found on PATH; connect a phone or enter the specs manually.")
    command = ["adb"]
    if serial:
        command += ["-s", serial]
    command += ["shell", "getprop"]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.SubprocessError) as error:
        raise DeviceDetectionError(f"adb failed: {error}") from error
    if completed.returncode != 0 or not completed.stdout.strip():
        raise DeviceDetectionError("adb returned no data. Is one device connected with USB debugging enabled?")
    props: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        match = re.match(r"\[([^]]+)]:\s*\[([^]]*)]", line.strip())
        if match:
            props[match.group(1)] = match.group(2)
    if not props.get("ro.build.version.sdk"):
        raise DeviceDetectionError("adb did not report ro.build.version.sdk.")
    model = props.get("ro.product.model", "")
    abis = [abi for abi in (props.get("ro.product.cpu.abilist") or "").split(",") if abi]
    return {
        "model": model,
        "brand": props.get("ro.product.manufacturer", ""),
        "sdk": int(re.sub(r"\D", "", props["ro.build.version.sdk"]) or 0),
        "android": props.get("ro.build.version.release", ""),
        "abi": abis,
        "dpi": int(re.sub(r"\D", "", props.get("ro.sf.lcd_density", "") or "0") or 0),
        "source": "adb",
    }


def profile_from_payload(payload: dict, devices: list[dict] | None = None) -> dict:
    """Build a normalized device profile from API/CLI input.

    Manual numeric fields always win over database and auto-detected values.
    """
    devices = devices if devices is not None else load_devices()
    payload = payload or {}
    detected = parse_user_agent(payload.get("userAgent", "")) if payload.get("userAgent") else {}
    platform_version = payload.get("platformVersion")
    if platform_version and not payload.get("sdk"):
        detected["sdk"] = sdk_from_android(platform_version) or detected.get("sdk")
        detected["android"] = str(platform_version)

    query = payload.get("deviceId") or payload.get("model") or detected.get("model") or payload.get("modelHint")
    device, match = resolve_device(query, devices) if query else (None, {"matched": False, "query": query, "confidence": 0})

    base = dict(device) if device else {}
    profile: dict = {
        "deviceId": base.get("id"),
        "brand": base.get("brand") or payload.get("brand") or "",
        "name": base.get("name") or (query if match.get("exact") else ""),
        "model": base.get("models", [None])[0] if base.get("models") else (query or ""),
        # A real reading from the current browser/ADB beats a database average
        # (phones get OS upgrades); explicit manual fields below beat both.
        "android": detected.get("android") or base.get("android") or "",
        "sdk": detected.get("sdk") or base.get("sdk"),
        "abi": list(base.get("abi") or []),
        "density": base.get("density") or "",
        "dpi": base.get("dpi"),
        "ramGb": base.get("ramGb"),
        "year": base.get("year"),
        "tags": list(base.get("tags") or []),
        "source": "database" if device else (detected.get("model") and "user-agent" or "manual"),
        "detection": {
            **match,
            "userAgentModel": detected.get("model"),
            "userAgentAndroid": detected.get("android"),
            "autoDetected": bool(detected.get("model") or platform_version),
        },
    }

    # Apply explicit overrides.
    if payload.get("android"):
        profile["android"] = str(payload["android"])
    sdk_value = payload.get("sdk")
    if sdk_value not in (None, ""):
        try:
            profile["sdk"] = int(sdk_value)
        except (TypeError, ValueError):
            profile["sdk"] = sdk_from_android(sdk_value)
    elif profile["android"] and not profile["sdk"]:
        profile["sdk"] = sdk_from_android(profile["android"])
    elif payload.get("platformVersion") and not payload.get("sdk"):
        profile["sdk"] = sdk_from_android(platform_version)

    abi_value = payload.get("abi") or payload.get("architecture")
    if abi_value:
        if isinstance(abi_value, str):
            profile["abi"] = [part.strip() for part in re.split(r"[,; ]+", abi_value) if part.strip()]
        else:
            profile["abi"] = list(abi_value)
        if payload.get("architecture") == "arm" or payload.get("bitness") == "32":
            profile["abi"] = ["armeabi-v7a", *[a for a in profile["abi"] if a != "armeabi-v7a"]]
    if payload.get("density"):
        profile["density"] = str(payload["density"])
    dpi_value = payload.get("dpi")
    if dpi_value not in (None, ""):
        try:
            profile["dpi"] = int(float(dpi_value))
        except (TypeError, ValueError):
            pass
    if payload.get("ramGb") not in (None, ""):
        try:
            profile["ramGb"] = float(payload["ramGb"])
        except (TypeError, ValueError):
            pass
    if isinstance(payload.get("tags"), list):
        profile["tags"] = list(dict.fromkeys([*profile["tags"], *payload["tags"]]))

    if not profile["model"] and query:
        profile["model"] = query
    if not profile["name"]:
        profile["name"] = profile["model"] or "Unknown phone"
    if profile["sdk"] is None:
        raise DeviceDetectionError(
            "Cannot determine the Android SDK level. Choose a phone model or enter the Android version manually."
        )
    if not profile["android"]:
        profile["android"] = android_from_sdk(profile["sdk"])
    if not profile["abi"]:
        profile["abi"] = ["arm64-v8a", "armeabi-v7a"]
    if not profile["density"]:
        profile["density"] = dpi_bucket(profile.get("dpi"))
    if payload.get("source") == "adb":
        profile["source"] = "adb"
    elif payload.get("model") and not device:
        profile["source"] = "manual"
    # Android Go / 32-bit devices declare their ABI order deliberately: respect
    # it instead of promoting arm64-v8a over the armeabi-v7a they actually run.
    if "go32" in profile["tags"] and not abi_value:
        profile["primaryAbi"] = profile["abi"][0] if profile["abi"] else "armeabi-v7a"
    else:
        profile["primaryAbi"] = primary_abi(profile["abi"])
    return profile
