"""YouTube version auto-updater and device-compatibility advisor.

The repository is a patch-source project, not an APK.  This package keeps a
machine-readable catalog of the YouTube versions supported by the checked-in
patch sources, refreshes it from the upstream Morphe patch bundle, and matches
those versions against a phone's Android SDK level, CPU ABI and screen density.
"""

from pathlib import Path

VERSION = "1.0.0"

PACKAGE_DIR = Path(__file__).resolve().parent
TOOL_DIR = PACKAGE_DIR.parent
DATA_DIR = TOOL_DIR / "data"
WEB_DIR = TOOL_DIR / "web"
CATALOG_PATH = DATA_DIR / "supported-versions.json"
DEVICES_PATH = DATA_DIR / "devices.json"


def _find_repo_root() -> Path:
    """Locate the repository root (works from any working directory)."""
    for candidate in (TOOL_DIR, *TOOL_DIR.parents):
        if (candidate / "patches-list.json").is_file() and (candidate / ".git").exists():
            return candidate
    return TOOL_DIR.parents[1]


REPO_ROOT = _find_repo_root()
LOCAL_MANIFEST_PATH = REPO_ROOT / "patches-list.json"
DOCS_DIR = REPO_ROOT / "docs"

__all__ = [
    "VERSION",
    "TOOL_DIR",
    "DATA_DIR",
    "WEB_DIR",
    "CATALOG_PATH",
    "DEVICES_PATH",
    "REPO_ROOT",
    "LOCAL_MANIFEST_PATH",
    "DOCS_DIR",
]
