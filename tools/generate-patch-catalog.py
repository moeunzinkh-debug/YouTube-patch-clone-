#!/usr/bin/env python3
"""Regenerate the collapsible patch catalog in README.md from patches-list.json.

The grouping is kept in `GROUPS`; patches backported from upstream v1.48.0 are
listed separately so it is obvious which ones are new. Run from the repo root:

    python3 tools/generate-patch-catalog.py

The README section between <!-- PATCH-LIST:START --> and <!-- PATCH-LIST:END -->
is replaced in place; everything else in the README is left untouched.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "patches-list.json"
README = ROOT / "README.md"
START = "<!-- PATCH-LIST:START -->"
END = "<!-- PATCH-LIST:END -->"
YOUTUBE_PACKAGE = "com.google.android.youtube"

# Patches added from upstream v1.48.0 (stable). Kept in their own group.
NEW_IN_V148 = [
    "Ask flyout menu",
    "Custom font",
    "Feed card layout",
    "Feed video actions",
    "Feed view count",
    "Force animations",
    "Series tracking",
    "Skip live Shorts",
    "Video delay",
]

# Existing groups, in display order. Any manifest patch not listed here is
# reported as an error so a new upstream patch never silently disappears.
GROUPS: list[tuple[str, list[str]]] = [
    ("✨ ថ្មីពី v1.48.0 / New in v1.48.0", NEW_IN_V148),
    (
        "🚫 ពាណិជ្ជកម្ម & ការរំខាន / Ads & distractions",
        [
            "AI channel filter", "Channel whitelist", "DeArrow", "Hide ads",
            "Hide autoplay preview", "Hide end screen cards",
            "Hide end screen suggested video", "Hide info cards",
            "Hide layout components", "Hide player flyout menu components",
            "Hide player overlay buttons", "Hide related video overlay",
            "Hide related videos", "Hide status bar", "Hide timestamp",
            "Hide video action buttons", "Remove viewer discretion dialog",
            "Restore original titles", "Return YouTube Dislike", "SponsorBlock",
        ],
    ),
    (
        "▶️ ការចាក់វីដេអូ / Playback & video",
        [
            "Audio equalizer", "Captions", "Double tap to seek", "Exit fullscreen mode",
            "Force fullscreen landscape", "Force original audio",
            "Fullscreen video scale", "Loop video", "Media notification controls",
            "Miniplayer", "Mute button", "Open videos fullscreen",
            "Picture-in-picture button", "Play all", "Playback buffer",
            "Playback in feeds", "Playback speed", "Reload video",
            "Remember live stream playback position",
            "Remove background playback restrictions", "Seekbar", "Skip silence",
            "Video quality",
        ],
    ),
    ("📱 Shorts", ["Disable Shorts resuming on startup", "Hide Shorts components",
                   "Open Shorts in regular player", "Shorts autoplay", "Shorts icon style"]),
    (
        "🎨 រូបរាង & អេក្រង់ / Theme, layout & player UI",
        [
            "Ambient mode", "App refresh rate", "Change form factor", "Change header",
            "Change start page", "Custom branding", "Custom player overlay opacity",
            "Navigation bar", "Override YouTube Music buttons",
            "Player icon style", "Settings menu filter", "Swipe controls", "Theme",
            "Wide search bar",
        ],
    ),
    (
        "⚙️ បិទ/បើកមុខងារ / Behaviour toggles",
        [
            "Disable DRC audio", "Disable Play Store updates", "Disable QUIC protocol",
            "Disable auto feed refresh", "Disable continue watching prompt",
            "Disable double tap actions", "Disable fullscreen gestures",
            "Disable haptic feedback", "Disable layout updates",
            "Disable player popup panels", "Disable playlist autoplay",
            "Disable rolling number animations", "Disable scrolling speed limit",
            "Disable sign in to TV popup", "Disable video codecs",
        ],
    ),
    (
        "🌐 បណ្តាញ & គណនី / Network, spoofing & account",
        [
            "Bypass image region restrictions", "Bypass link redirects",
            "Change installer source", "Check watch history domain name resolution",
            "Enable debugging", "GmsCore support", "Network proxy",
            "Override certificate pinning", "PoToken provider", "Spoof app version",
            "Spoof device dimensions", "Spoof signature", "Spoof video streams",
        ],
    ),
    (
        "🧰 ចែករំលែក & ឧបករណ៍ / Sharing & tools",
        [
            "Add to queue", "Channel search", "Clone app", "Copy text",
            "Copy video link", "Downloads", "Open channel of live avatar",
            "Open links externally", "Open system share sheet",
            "Sanitize sharing links", "Save to Watch later",
            "Voice over translation",
        ],
    ),
]


def main() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    patches = data["patches"]
    names = [p["name"] for p in patches]
    youtube = [
        p["name"] for p in patches
        if any(c.get("packageName") == YOUTUBE_PACKAGE
               for c in (p.get("compatiblePackages") or []))
    ]
    generic = [p["name"] for p in patches if not (p.get("compatiblePackages") or [])]

    mapped = {n: title for title, members in GROUPS for n in members}
    stale = [n for n in mapped if n not in names]
    unmapped = [n for n in names if n not in mapped]
    if stale:
        raise SystemExit(f"Grouped patches no longer in manifest: {stale}")
    if unmapped:
        raise SystemExit(f"Manifest patches missing from groups: {unmapped}")

    lines: list[str] = [START, "<details>",
                        f"<summary>📦 YouTube • {len(youtube)} patches</summary>", "",
                        "### YouTube Patches", "",
                        "និយាយពីអ្វីដែលមាននៅក្នុង patches ទាំងអស់ / What is inside the whole patch bundle. "
                        f"បញ្ជីពេញខាងក្រោមគឺ {len(patches)} patches ពី "
                        f"[`patches-list.json`](patches-list.json) v{data['version']} "
                        f"({len(youtube)} កំណត់គោលដៅ `{YOUTUBE_PACKAGE}` + {len(generic)} shared/generic)។", "",
                        "**ឧទាហរណ៍ / Highlights**", "",
                        "- Remove Ads", "- Background Playback", "- Hide Shorts", "- Custom Theme", "",
                        "ទាំងនេះត្រូវគ្នាជាមួយ `Hide ads`, `Remove background playback restrictions`, "
                        "`Hide Shorts components` និង `Theme`។ ក្រៅពីនោះនៅមាន SponsorBlock, "
                        "Return YouTube Dislike, DeArrow, Picture-in-Picture, Playback speed, Video quality, "
                        "Loop video, Swipe controls, Seekbar, Downloads, Save to Watch later, Copy/share links, "
                        "Spoof app version/signature, GmsCore support និង **Voice over translation** (Khmer TTS) ជាដើម។", "",
                        "បើកក្រុមខាងក្រោមដើម្បីមើលគ្រប់ patch / Expand a group to see every patch name:", ""]

    for title, members in GROUPS:
        present = [n for n in members if n in names]
        if not present:
            continue
        lines += ["<details>", f"<summary>{title} • {len(present)}</summary>", ""]
        lines += [f"- `{n}`" for n in sorted(present, key=str.lower)]
        lines += ["", "</details>", ""]

    lines += ["> ចំណាំ៖ ក្រុម «ថ្មីពី v1.48.0» គឺជា patches ដែលបានបន្ថែមពី upstream v1.48.0។ "
              "ស្លាក `youtube-*` មិនបន្ថែម patch ថ្មីទេ — ការបន្ថែមកំណែ YouTube ថ្មីត្រូវការ sync កូដ patch ពី upstream មុន។",
              "", "</details>", END]
    block = "\n".join(lines) + "\n"

    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        raise SystemExit("README patch-list markers not found")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    README.write_text(pattern.sub(lambda _: block.rstrip("\n"), text, count=1), encoding="utf-8")
    print(f"README catalog updated: {len(patches)} patches, {len(youtube)} YouTube, {len(generic)} generic")


if __name__ == "__main__":
    main()
