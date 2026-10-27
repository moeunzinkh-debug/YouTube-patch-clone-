"""Compatibility analysis: which supported YouTube version fits this phone?

The score is intentionally transparent and explainable instead of pretending
to be machine learning.  Every option carries bilingual reason codes so users
can see *why* a version was (or was not) recommended.
"""

from __future__ import annotations

from .catalog import android_name, channel as get_channel, version_key
from .devices import android_from_sdk
from .i18n import reason


def _option(entry: dict, profile: dict, rank: int, total_compatible_rank: int) -> dict:
    sdk = int(profile["sdk"])
    min_sdk = int(entry.get("minSdk") or 0)
    compatible = sdk >= min_sdk
    experimental = bool(entry.get("experimental"))
    score = max(0, 100 - rank * 4)
    reasons = []

    if experimental:
        # A stable build must outrank a newer experimental build, even when
        # several experimental releases are ahead of it in the catalog.
        score -= 25
        reasons.append(reason("experimental"))
    else:
        score += 6
        reasons.append(reason("stable"))

    if compatible:
        reasons.append(
            reason(
                "sdk_ok",
                android=entry.get("androidMin", android_name(min_sdk)),
                sdk=min_sdk,
                deviceAndroid=profile.get("android") or android_from_sdk(sdk),
                deviceSdk=sdk,
            )
        )
        if sdk - min_sdk >= 3:
            score += 2
            reasons.append(reason("headroom", n=sdk - min_sdk))
        elif sdk == min_sdk:
            score -= 2
            reasons.append(reason("sdk_exact"))
    else:
        score = -100
        reasons.append(
            reason(
                "sdk_fail",
                android=entry.get("androidMin", android_name(min_sdk)),
                sdk=min_sdk,
                deviceSdk=sdk,
            )
        )

    if rank == total_compatible_rank and compatible:
        score += 3
        reasons.append(reason("newest"))
    elif compatible and total_compatible_rank >= 0:
        reasons.append(reason("older", n=max(0, rank - total_compatible_rank)))

    ram = profile.get("ramGb")
    if compatible and ram is not None and ram < 3 and version_key(entry["version"])[0] >= 21:
        score -= 5
        reasons.append(reason("low_ram", ram=ram))

    return {
        "version": entry["version"],
        "minSdk": min_sdk,
        "androidMin": entry.get("androidMin", android_name(min_sdk)),
        "experimental": experimental,
        "patchCount": entry.get("patchCount", 0),
        "compatible": compatible,
        "score": round(score, 1),
        "reasons": reasons,
    }


def analyze(profile: dict, catalog: dict, channel_name: str = "local") -> dict:
    """Return a full bilingual recommendation for a normalized device profile."""
    source = get_channel(catalog, channel_name)
    entries = sorted(source.get("versions", []), key=lambda item: version_key(item["version"]), reverse=True)
    sdk = int(profile["sdk"])
    compatible_count = sum(1 for item in entries if sdk >= int(item.get("minSdk") or 0))
    newest_rank = next(
        (rank for rank, item in enumerate(entries) if sdk >= int(item.get("minSdk") or 0)),
        -1,
    )
    options = [_option(entry, profile, rank, newest_rank) for rank, entry in enumerate(entries)]

    compatible = [item for item in options if item["compatible"]]
    stable = [item for item in compatible if not item["experimental"]]
    best = max(stable or compatible, key=lambda item: item["score"], default=None)
    newest = max(compatible, key=lambda item: version_key(item["version"]), default=None)

    notes: list[dict] = [
        reason("channel_local" if channel_name == "local" else "channel_upstream", version=source.get("patchVersion", "?"))
    ]
    added = catalog.get("changes", {}).get("added", [])
    if added:
        notes.append(
            reason(
                "update_available",
                n=len(added),
                versions=", ".join(item["version"] for item in added[:5]),
            )
        )
    else:
        notes.append(reason("no_update"))
    if profile.get("detection", {}).get("autoDetected"):
        notes.append(reason("detect_guess"))

    apk = {
        "variant": "nodpi",
        "abi": profile.get("primaryAbi", "arm64-v8a"),
        "density": profile.get("density") or "nodpi",
        "advice": [
            reason("apk_nodpi"),
            reason("apk_abi", abi=profile.get("primaryAbi", "arm64-v8a")),
            reason("apk_density", density=profile.get("density") or "nodpi"),
        ],
    }
    tags = profile.get("tags", []) or []
    if "go32" in tags:
        apk["advice"].append(reason("apk_go"))
    if "no-gms" in tags:
        apk["advice"].append(reason("apk_gms"))

    result: dict = {
        "device": profile,
        "channel": channel_name,
        "patchVersion": source.get("patchVersion"),
        "catalogVersion": catalog.get("generatedAt"),
        "recommendation": best,
        "newestCompatible": newest,
        "options": options,
        "compatibleCount": compatible_count,
        "apk": apk,
        "notes": notes,
        "updateAvailable": len(added),
        "noCompatibleReason": None,
    }
    if best is None:
        lowest = min((item["minSdk"] for item in entries), default=0)
        result["noCompatibleReason"] = reason("no_compatible", minSdk=lowest)
        result["notes"].insert(0, result["noCompatibleReason"])
    return result
