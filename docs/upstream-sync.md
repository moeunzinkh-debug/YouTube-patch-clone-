# Upstream sync report — YouTube only / របាយការណ៍ sync ពី upstream

> Compared on 2026-10-27 against [MorpheApp/morphe-patches](https://github.com/MorpheApp/morphe-patches).
> This report describes **what upstream added**; it does **not** mean the new patch code is already in this repo.

## Current state of this repository

| Item | Value |
| --- | --- |
| Upstream base | **v1.47.0**, commit `e5464395441e916b643af4e2175c4e253e6df487` (2026-10-11) |
| Manifest | `patches-list.json` v1.47.0 — **102 patches** (97 YouTube + 5 generic) |
| YouTube targets | 9 (`21.40.161` … `20.21.37`) |
| Build | `gradle.properties` `version = 1.47.0`, Patcher **1.14.0**, patches-library `1.9.0-dev.4` |
| Bundle | `patch.mpp` declares `Version: 1.47.0`, `Patcher-Version: 1.14.0` |
| Local customisations | Khmer voice-over TTS (`voiceovertranslation/*`, `KhmerTtsClient.java`, `Settings.java`, Khmer strings), YouTube-only resource checker, filtered manifest/settings |

Only the YouTube patch set is kept — the YouTube Music and Reddit modules are excluded. This stays true for any sync.

## Latest upstream releases

| Release | Date | Total patches | YouTube patches | Notes |
| --- | --- | --- | --- | --- |
| **v1.48.0** (latest stable) | 2026-10-22 | 190 | **105** | +9 new YouTube patches, Patcher **2.0.0** |
| v1.49.0-dev.7 (latest pre-release) | 2026-10-26 | 192 | **107** | +2 more patches, YouTube `21.43.523` |
| `main` | — | 190 | 105 | same manifest as v1.48.0 |

## ✨ New YouTube patches in v1.48.0 (9)

| Patch | What it does |
| --- | --- |
| `Ask flyout menu` | Adds a video menu entry that opens Ask for the video and summarizes it (YouTube 21.16.256+). |
| `Custom font` | Use the system font or a custom TTF/OTF font instead of YouTube Sans. **Replaces `Force system font`.** |
| `Feed card layout` | Show/hide the card layout of feed videos that YouTube sends as an A/B test. |
| `Feed video actions` | Watch later button on feed thumbnails; long-press anywhere on a video to open its menu. |
| `Feed view count` | Shows the view count at the bottom left of feed thumbnails. |
| `Force animations` | Force app animations (e.g. player transitions) on or off even when YouTube disables them. |
| `Series tracking` | Series library in History with local progress and episode continuation (YouTube 21.02+). |
| `Skip live Shorts` | Automatically skip live streams appearing in the Shorts feed. |
| `Video delay` | Delay the video to keep it in sync with laggy Bluetooth audio. |

Additional patches in **v1.49.0-dev.7**: `Download post images` (download images/GIFs of posts) and `Search comments` (filter loaded comments by keyword).

**Removed/renamed:** `Force system font` → `Custom font`.

Also new in v1.48.0 but folded into existing patches: Premium-style queue, captions in PiP, extra auto-translate languages, "Force VP9 codec", in-app downloads, Shorts playback speed, feed-thumbnail like count, Series button icons, and dozens of YouTube bug fixes (captions, video quality, navigation bar, miniplayer, Downloads, SponsorBlock…).

## 🎯 Supported YouTube versions

| | v1.47.0 (ours) | v1.48.0 | v1.49.0-dev.7 |
| --- | --- | --- | --- |
| Newest experimental | `21.40.161` | `21.42.241`, `21.41.525` | `21.43.523`, `21.42.241` |
| Recommended stable | `21.20.405` | `21.20.405` | `21.20.405` |
| Dropped targets | — | `21.40.161`, `21.39.522`, `21.38.130` | `21.41.525` |

The advisor catalog is already refreshed: see [youtube-versions.md](youtube-versions.md). It reports `21.42.241` / `21.41.525` as **upstream-only — needs sync** because adding a target without porting the matching Kotlin patch sources does not make it patchable.

## ⚠️ Build-system change: Patcher 2.0

v1.48.0 migrates to `morphe-patcher 2.0.0` / `morphe-patches-library 2.0.0` (from `1.14.0` / `1.9.0-dev.4`), bumps smali, adds the `org.gradle.toolchains.foojay-resolver-convention` plugin and pins a Java 17 toolchain in `patches/build.gradle.kts`. A rebuilt `patch.mpp` would declare `Patcher-Version: 2.0.0`, so users need a Manager/Patcher that supports it. Copying only the new patch files into a v1.47.0 build would **not compile** — the new patches use new Patcher APIs (`Match`, `BytecodePatchContext`, extra `InstructionLocation` values) and updated shared fingerprints.

## Scale of the source sync (YouTube-relevant paths only)

| Change | v1.47.0 → v1.48.0 | v1.48.0 → v1.49.0-dev.7 |
| --- | --- | --- |
| New files | 140 | 90 |
| Modified files | 598 | 412 |
| Deleted files | 7 | 26 |

Our local customisations touch 14 files plus the extra `KhmerTtsClient.java`. A three-way merge (base v1.47.0 / ours / theirs v1.48.0) is automatic for 8 of them and **conflicts in 5**, all around Khmer TTS:

- `voiceovertranslation/TTSPrefetcher.java`
- `voiceovertranslation/VOTBottomSheet.java`
- `voiceovertranslation/VoiceCatalog.java`
- `voiceovertranslation/VoiceOverTranslationPatch.java`
- `patches/build.gradle.kts`

Upstream also rewrote `TTSCache.java` and `TTSEngine.java` (disk sample cache → in-memory preview cache), so the Khmer TTS port needs hands-on review even where text merges cleanly.

## Integration plan (when approved)

1. Re-create the YouTube-only file set from upstream v1.48.0, excluding `music/`, `reddit/` and their resources.
2. Three-way merge the 14 local customisations; resolve the 5 conflicts and re-check the Khmer TTS API against the rewritten upstream TTS classes.
3. Regenerate the filtered `patches-list.json` (105 YouTube + 5 generic), bump `gradle.properties` to `1.48.0`, sync `gradle/libs.versions.toml`, `settings.gradle.kts`, `patches/build.gradle.kts` and `gradle-wrapper.properties`.
4. Merge new upstream strings into `values/youtube/strings.xml`, keeping the Khmer `values-km-rKH/youtube/strings.xml` additions.
5. Rebuild `patch.mpp` with `.github/workflows/build-mpp.yml` (CI only — this sandbox has no JDK/Android SDK), verify with `.github/scripts/verify-mpp.py`, refresh `patch.mpp.sha256`, docs and `patches-bundle.json`.
6. Update README tags/badges and cut a `v1.48.0` release.

**Decision needed:** stable **v1.48.0** (recommended) vs pre-release **v1.49.0-dev.7**, and whether to do the full source sync + CI rebuild now or only keep this report/catalog first.

## Sources

- https://github.com/MorpheApp/morphe-patches/releases/tag/v1.48.0
- https://github.com/MorpheApp/morphe-patches/releases/tag/v1.49.0-dev.7
- https://github.com/MorpheApp/morphe-patches/compare/v1.47.0...v1.48.0
- `patches-list.json` at `v1.48.0` / `v1.49.0-dev.7` / `main`
- Source tarballs compared locally: `v1.47.0`, `v1.48.0`, `v1.49.0-dev.7`
