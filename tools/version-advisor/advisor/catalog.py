"""Automatic refresh of the supported-YouTube-version catalog.

Two channels are tracked:

* ``local``    – targets declared by this repository's ``patches-list.json``.
                 These are the only versions the checked-in patch sources can
                 actually patch, and are the default for recommendations.
* ``upstream`` – targets declared by the newest Morphe patch bundle on GitHub.
                 Used for the "update available" notice and for planning.

The upstream manifest is fetched through the GitHub contents API with an ETag,
so repeated checks are cheap.  A failed/offline fetch never destroys the last
known good catalog.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import CATALOG_PATH, LOCAL_MANIFEST_PATH, REPO_ROOT, VERSION

YOUTUBE_PACKAGE = "com.google.android.youtube"
DEFAULT_OWNER = "MorpheApp"
DEFAULT_REPO = "morphe-patches"
DEFAULT_REF = "main"
API_BASE = "https://api.github.com"

ANDROID_NAMES = {
    21: "5.0", 22: "5.1", 23: "6.0", 24: "7.0", 25: "7.1",
    26: "8.0", 27: "8.1", 28: "9", 29: "10", 30: "11",
    31: "12", 32: "12L", 33: "13", 34: "14", 35: "15", 36: "16",
}


class CatalogSyncError(RuntimeError):
    """The upstream catalog could not be fetched or parsed."""


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def android_name(sdk: int) -> str:
    if sdk in ANDROID_NAMES:
        return ANDROID_NAMES[sdk]
    if sdk < 21:
        return f"SDK {sdk}"
    return f"SDK {sdk}+"


def version_key(version: str) -> tuple[int, ...]:
    """Sortable numeric key for dotted YouTube versions (21.9.3 < 21.40.161)."""
    parts = []
    for chunk in str(version).split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts + [0] * (4 - len(parts)))[:4]


def load_json(path: Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, payload: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def extract_versions(manifest: dict) -> list[dict]:
    """Collect YouTube targets from a patches-list.json style manifest."""
    found: dict[str, dict] = {}
    for patch in manifest.get("patches", []) or []:
        for package in patch.get("compatiblePackages") or []:
            if package.get("packageName") != YOUTUBE_PACKAGE:
                continue
            for target in package.get("targets") or []:
                version = target.get("version")
                if not version:
                    continue
                entry = found.setdefault(
                    version,
                    {"version": version, "minSdk": 0, "experimental": False, "patchCount": 0},
                )
                entry["minSdk"] = max(entry["minSdk"], int(target.get("minSdk") or 0))
                entry["experimental"] = bool(entry["experimental"] or target.get("isExperimental"))
                entry["patchCount"] += 1
    versions = sorted(found.values(), key=lambda item: version_key(item["version"]), reverse=True)
    for entry in versions:
        entry["androidMin"] = android_name(entry["minSdk"])
    return versions


def _github_get(path: str, etag: str | None = None, timeout: float = 20) -> tuple[dict | list, dict]:
    url = f"{API_BASE}{path}"
    headers = {
        "User-Agent": f"youtube-version-advisor/{VERSION}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if etag:
        headers["If-None-Match"] = etag
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            meta = {
                "etag": response.headers.get("etag"),
                "status": response.status,
                "rateRemaining": response.headers.get("x-ratelimit-remaining"),
            }
            return json.loads(body.decode("utf-8")), meta
    except urllib.error.HTTPError as error:
        if error.code == 304:
            return {}, {"status": 304, "etag": etag, "notModified": True}
        raise CatalogSyncError(f"GitHub API returned HTTP {error.code} for {url}") from error
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        raise CatalogSyncError(f"Cannot reach GitHub API ({error})") from error


def fetch_upstream(previous: dict, timeout: float = 20) -> tuple[dict | None, dict]:
    """Fetch the upstream manifest. Returns (None, meta) when nothing changed."""
    owner = os.environ.get("ADVISOR_UPSTREAM_OWNER", DEFAULT_OWNER)
    repo = os.environ.get("ADVISOR_UPSTREAM_REPO", DEFAULT_REPO)
    ref = os.environ.get("ADVISOR_UPSTREAM_REF", DEFAULT_REF)
    upstream = previous.get("upstream", {}) or {}
    query = urllib.parse.urlencode({"ref": ref})
    path = f"/repos/{owner}/{repo}/contents/patches-list.json?{query}"

    data, meta = _github_get(path, upstream.get("etag"), timeout)
    meta.update({"owner": owner, "repo": repo, "ref": ref, "checkedAt": utcnow()})
    if meta.get("notModified"):
        return None, meta

    try:
        raw = base64.b64decode(data["content"], validate=False)
        manifest = json.loads(raw.decode("utf-8"))
        if not isinstance(manifest.get("patches"), list):
            raise ValueError("missing 'patches' list")
    except (KeyError, TypeError, ValueError, UnicodeDecodeError) as error:
        raise CatalogSyncError(f"Upstream patches-list.json is invalid ({error})") from error

    meta["sha"] = data.get("sha")
    meta["url"] = data.get("html_url") or f"https://github.com/{owner}/{repo}/blob/{ref}/patches-list.json"
    return manifest, meta


def fetch_release(previous: dict, timeout: float = 20) -> dict:
    """Best-effort lookup of the newest upstream release metadata."""
    owner = os.environ.get("ADVISOR_UPSTREAM_OWNER", DEFAULT_OWNER)
    repo = os.environ.get("ADVISOR_UPSTREAM_REPO", DEFAULT_REPO)
    old = (previous.get("upstream", {}) or {}).get("release", {}) or {}
    try:
        data, meta = _github_get(
            f"/repos/{owner}/{repo}/releases/latest",
            old.get("etag"),
            timeout=min(timeout, 10),
        )
        if meta.get("notModified"):
            return old
        return {
            "tag": data.get("tag_name"),
            "name": data.get("name"),
            "publishedAt": data.get("published_at"),
            "url": data.get("html_url"),
            "etag": meta.get("etag"),
        }
    except CatalogSyncError:
        return old


def compare_channels(local: list[dict], upstream: list[dict]) -> dict:
    """Diff the two version lists so an update can report what changed."""
    local_by_version = {item["version"]: item for item in local}
    upstream_by_version = {item["version"]: item for item in upstream}
    added = [upstream_by_version[v] for v in upstream_by_version if v not in local_by_version]
    removed = [local_by_version[v] for v in local_by_version if v not in upstream_by_version]
    modified = []
    for version, current in local_by_version.items():
        latest = upstream_by_version.get(version)
        if not latest:
            continue
        if (current["minSdk"], current["experimental"]) != (latest["minSdk"], latest["experimental"]):
            modified.append({"version": version, "local": current, "upstream": latest})
    key = lambda item: version_key(item["version"])
    return {
        "added": sorted(added, key=key, reverse=True),
        "removed": sorted(removed, key=key, reverse=True),
        "modified": sorted(modified, key=lambda item: version_key(item["version"]), reverse=True),
    }


def _channel(manifest: dict, label: str, source: str) -> dict:
    return {
        "label": label,
        "source": source,
        "patchVersion": manifest.get("version"),
        "patchCount": len(manifest.get("patches", []) or []),
        "versions": extract_versions(manifest),
    }


def fingerprint(catalog: dict) -> str:
    """Stable representation used to decide whether a refresh changed anything."""
    relevant = {
        "local": {k: v for k, v in catalog.get("local", {}).items() if k != "checkedAt"},
        "upstream": {
            k: v
            for k, v in catalog.get("upstream", {}).items()
            if k not in ("checkedAt", "etag", "syncError", "rateRemaining", "release")
        },
        "release": (catalog.get("upstream", {}) or {}).get("release", {}).get("tag"),
    }
    return json.dumps(relevant, sort_keys=True, ensure_ascii=False)


def build_catalog(
    local_manifest: dict,
    upstream_manifest: dict | None = None,
    previous: dict | None = None,
    meta: dict | None = None,
    sync_error: str | None = None,
) -> dict:
    """Build a full catalog, preserving upstream data when a fetch is skipped."""
    previous = previous or {}
    meta = meta or {}
    old_upstream = dict(previous.get("upstream", {}) or {})
    local = _channel(local_manifest, "This repository (checked-in patch sources)", "patches-list.json")
    local["checkedAt"] = utcnow()

    if upstream_manifest is not None:
        upstream = _channel(
            upstream_manifest,
            "Upstream Morphe patch bundle (latest)",
            f"{meta.get('owner', DEFAULT_OWNER)}/{meta.get('repo', DEFAULT_REPO)}@{meta.get('ref', DEFAULT_REF)}",
        )
        upstream["checkedAt"] = meta.get("checkedAt") or utcnow()
        upstream["commitSha"] = meta.get("sha")
        upstream["url"] = meta.get("url")
        upstream["etag"] = meta.get("etag") or old_upstream.get("etag")
        upstream["synced"] = True
        upstream["release"] = old_upstream.get("release", {})
        upstream.pop("syncError", None)
    else:
        upstream = old_upstream or _channel(local_manifest, "Upstream (not yet synced)", "local fallback")
        upstream["label"] = "Upstream Morphe patch bundle (latest)"
        upstream.setdefault("source", f"{DEFAULT_OWNER}/{DEFAULT_REPO}@{DEFAULT_REF}")
        upstream.setdefault("versions", local["versions"])
        upstream.setdefault("synced", False)
        upstream["checkedAt"] = meta.get("checkedAt") or upstream.get("checkedAt") or utcnow()
        if meta.get("etag"):
            upstream["etag"] = meta["etag"]
    if sync_error:
        upstream["syncError"] = sync_error

    changes = compare_channels(local["versions"], upstream.get("versions", []))
    return {
        "schemaVersion": 1,
        "generatedAt": utcnow(),
        "generator": f"youtube-version-advisor/{VERSION}",
        "youtubePackage": YOUTUBE_PACKAGE,
        "local": local,
        "upstream": upstream,
        "changes": changes,
    }


def load_catalog(path: Path | None = None) -> dict:
    """Load the catalog, or build a local-only one if it does not exist yet."""
    path = Path(path or CATALOG_PATH)
    if path.is_file():
        return load_json(path)
    return build_catalog(load_json(LOCAL_MANIFEST_PATH))


def sync_catalog(
    catalog_path: Path | None = None,
    local_manifest_path: Path | None = None,
    *,
    online: bool = True,
    write: bool = True,
    timeout: float = 20,
    with_release: bool = True,
) -> dict:
    """Refresh the catalog from upstream and optionally persist it.

    Returns a result dict; a network failure is reported, never raised to the
    CLI or web caller, and the previous upstream data is kept.
    """
    catalog_path = Path(catalog_path or CATALOG_PATH)
    local_manifest_path = Path(local_manifest_path or LOCAL_MANIFEST_PATH)
    local_manifest = load_json(local_manifest_path)
    # When no catalog exists yet, seed it from the manifest we were given
    # instead of the repository default (important for tests/custom paths).
    previous = load_json(catalog_path) if catalog_path.is_file() else build_catalog(local_manifest)
    upstream_manifest = None
    meta: dict = {"checkedAt": utcnow()}
    error = None

    if online:
        try:
            upstream_manifest, meta = fetch_upstream(previous, timeout)
        except CatalogSyncError as caught:
            error = str(caught)
            meta = {"checkedAt": utcnow()}
    else:
        error = "Offline mode: catalog rebuilt from the local manifest only."

    catalog = build_catalog(local_manifest, upstream_manifest, previous, meta, error)
    if with_release and upstream_manifest is not None:
        catalog["upstream"]["release"] = fetch_release(previous, timeout)
    elif with_release and previous.get("upstream", {}).get("release"):
        catalog["upstream"]["release"] = previous["upstream"]["release"]

    changed = fingerprint(catalog) != fingerprint(previous)
    if write and (changed or not catalog_path.is_file()):
        save_json(catalog_path, catalog)
    elif not changed and catalog_path.is_file():
        # Nothing new upstream: keep the exact previous object so that
        # generatedAt/checkedAt timestamps do not churn the file (and the
        # scheduled workflow only commits real changes).
        catalog = previous

    return {
        "catalog": catalog,
        "changed": changed,
        "checkedAt": meta.get("checkedAt"),
        "notModified": bool(meta.get("notModified")),
        "added": catalog["changes"]["added"],
        "removed": catalog["changes"]["removed"],
        "error": error,
        "written": bool(write and (changed or not catalog_path.is_file())),
    }


def channel(catalog: dict, name: str = "local") -> dict:
    if name not in ("local", "upstream"):
        raise ValueError(f"Unknown catalog channel: {name}")
    return catalog[name]


def render_markdown(catalog: dict) -> str:
    """Render docs/youtube-versions.md from the catalog."""
    local = catalog["local"]
    upstream = catalog["upstream"]
    changes = catalog["changes"]
    release = upstream.get("release") or {}
    lines = [
        "# Supported YouTube versions",
        "",
        "> Generated by `tools/version-advisor` — do not edit by hand.",
        f"> Catalog generated: {catalog.get('generatedAt', 'unknown')}",
        "",
        "The advisor pulls the YouTube targets out of `patches-list.json`, compares them with",
        "the newest upstream bundle, then matches a phone by Android SDK level, CPU ABI and",
        "screen density. See [the tool README](../tools/version-advisor/README.md).",
        "",
        f"## This repository — patch bundle v{local.get('patchVersion', '?')}",
        "",
        f"{local.get('patchCount', 0)} patches, {len(local['versions'])} supported YouTube versions.",
        "",
        "| YouTube version | Min Android | Min SDK | Status |",
        "| --- | --- | --- | --- |",
    ]
    for item in local["versions"]:
        status = "Experimental" if item["experimental"] else "Stable"
        lines.append(
            f"| `{item['version']}` | {item['androidMin']} | {item['minSdk']} | {status} |"
        )
    lines += [
        "",
        f"## Upstream — {upstream.get('source', DEFAULT_REPO)}",
        "",
        f"Patch bundle v{upstream.get('patchVersion', '?')}"
        + (f" (release {release['tag']}, {release.get('publishedAt', '')})" if release.get("tag") else "")
        + (f", commit `{upstream['commitSha'][:10]}`" if upstream.get("commitSha") else "")
        + ".",
        "",
        "| YouTube version | Min Android | Min SDK | Status | In this repo |",
        "| --- | --- | --- | --- | --- |",
    ]
    local_versions = {item["version"] for item in local["versions"]}
    for item in upstream.get("versions", []):
        status = "Experimental" if item["experimental"] else "Stable"
        present = "yes" if item["version"] in local_versions else "no — needs sync"
        lines.append(
            f"| `{item['version']}` | {item.get('androidMin', android_name(item['minSdk']))} "
            f"| {item['minSdk']} | {status} | {present} |"
        )
    added = ", ".join(f"`{item['version']}`" for item in changes["added"]) or "none"
    removed = ", ".join(f"`{item['version']}`" for item in changes["removed"]) or "none"
    lines += [
        "",
        "## Update status",
        "",
        f"- New upstream versions not yet in this repo: {added}",
        f"- Local versions no longer upstream: {removed}",
        f"- Upstream last checked: {upstream.get('checkedAt', 'never')}",
    ]
    if upstream.get("syncError"):
        lines.append(f"- Last sync warning: {upstream['syncError']}")
    lines += [
        "",
        "**Important:** this tool updates the *catalog*, not the Kotlin patch sources.",
        "Adding a target to `patches-list.json` without porting the matching upstream patch",
        "code would produce broken patches, so a source sync must be reviewed separately.",
        "",
    ]
    return "\n".join(lines)


def write_docs(catalog: dict, path: Path | None = None) -> Path:
    from . import DOCS_DIR

    path = Path(path or DOCS_DIR / "youtube-versions.md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(catalog), encoding="utf-8")
    return path
