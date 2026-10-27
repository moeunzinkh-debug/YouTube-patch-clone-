# Upstream sync report — YouTube only / របាយការណ៍ sync ពី upstream

> Compared on 2026-10-27 against [MorpheApp/morphe-patches](https://github.com/MorpheApp/morphe-patches).
> The comparison was done on 2026-10-27 and the 9 new patches are now implemented (see the «Implemented» section below).

## Current state of this repository

| Item | Value |
| --- | --- |
| Upstream base now | **v1.48.0**, commit `a5662d30d3` (2026-10-22); originally v1.47.0 `e5464395` (2026-10-11) |
| Manifest | `patches-list.json` v1.48.1 — **110 patches** (105 YouTube + 5 generic) |
| YouTube targets | 8 (`21.42.241`, `21.41.525`, `21.28.208` experimental; `21.23.492` **recommended**, `21.20.405`, `21.16.256`, `20.51.39`, `20.21.37` stable) |
| Build | `gradle.properties` `version = 1.48.1`, Patcher **2.0.0**, patches-library `2.0.0` |
| Bundle | `patch.mpp` declares `Version: 1.48.1`, `Patcher-Version: 2.0.0` |
| Local customisations preserved | Khmer voice-over TTS (`voiceovertranslation/*`, `KhmerTtsClient.java`, `Settings.java`, Khmer strings), YouTube-only resource checker, fork metadata |

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

| | v1.47.0 (ours, historical) | v1.48.0 stable | v1.49.0-dev.7/8 (upstream prerelease) |
| --- | --- | --- | --- |
| Newest experimental | `21.40.161` | `21.42.241`, `21.41.525` | `21.43.523`, `21.42.241` |
| Recommended stable | `21.20.405` | `21.20.405` | **`21.23.492`** |
| Dropped targets | — | `21.40.161`, `21.39.522`, `21.38.130` | `21.41.525` |

The advisor catalog is refreshed: see [youtube-versions.md](youtube-versions.md). Adding a target without porting the matching Kotlin patch sources does not make it patchable, so we have **not** added the prerelease target `21.43.523`.

## 🎯 Why Manager recommended `21.20.405` for us (fixed in v1.48.1)

Morphe Manager's version picker does **not** read `patches-list.json` or `patches-bundle.json` for the version list. It loads the compiled `patch.mpp` and reads `Compatibility.targets` from `app/morphe/patches/youtube/shared/Constants.kt`:

- [`AppVersionCatalog.kt`](https://github.com/MorpheApp/morphe-manager/blob/main/app/src/main/java/app/morphe/manager/domain/bundles/AppVersionCatalog.kt) → `experimentalVersions()` collects every target with `isExperimental = true`; `offered()` drops those targets unless the user enabled *experimental versions* for that bundle; `recommended()` = `offered().installable().firstOrNull()` — the **newest non-experimental** target.
- [`PatchInfo.kt`](https://github.com/MorpheApp/morphe-manager/blob/main/app/src/main/java/app/morphe/manager/patcher/patch/PatchInfo.kt) builds `experimentalVersions` from the bundle's `Compatibility.targets`.

In upstream v1.48.0, `21.23.492` was still `isExperimental = true`, so our newest stable target was `21.20.405` → Manager showed **Recommended 21.20.405** (screenshot, lower card). Upstream promoted `21.23.492` to stable in v1.49.0-dev.7 / dev.8, so their newest stable — and therefore their recommendation — became **21.23.492** (upper card). That single boolean is the whole difference. The upper card also shows three experimental rows because *experimental versions* is enabled for the upstream bundle in Manager; that is a per-bundle Manager setting (`bundleExperimentalVersionsEnabled` in `PreferencesManager.kt`), not something a patch repo controls.

**Fix applied (v1.48.1):** set `isExperimental = false` for `21.23.492` in `Constants.kt` and in all 105 `patches-list.json` target entries. The compiled bundle now offers `21.23.492` as the newest stable target, so Manager recommends the same version as upstream. Stable list after the fix:

`21.23.492` (Recommended) → `21.20.405` → `21.16.256` → `20.51.39` → `20.21.37`.

Experimental (hidden unless enabled in Manager): `21.42.241`, `21.41.525`, `21.28.208`. Upstream's prerelease additionally has `21.43.523`; we did **not** add it because our v1.48.0 patch implementations do not contain the v1.49.0-dev.8 fingerprints for that build — adding the target alone would offer an APK the patches cannot patch. If you want the experimental list to match too, that requires the full v1.49.0-dev.8 source sync.

To make Manager refresh, the bundle version was bumped `1.48.0` → `1.48.1` in `gradle.properties`, `patches-list.json` and `patches-bundle.json`, a new release/tag was published, and `patches-bundle.json` on the default branch now points at the `v1.48.1` asset.

## ⚠️ Build-system change: Patcher 2.0

v1.48.0 migrates to `morphe-patcher 2.0.0` / `morphe-patches-library 2.0.0` (from `1.14.0` / `1.9.0-dev.4`), bumps smali, adds the `org.gradle.toolchains.foojay-resolver-convention` plugin and pins a Java 17 toolchain in `patches/build.gradle.kts`. **This migration is now applied here**, so `patch.mpp` declares `Patcher-Version: 2.0.0` and users need a Manager/Patcher that supports it. Copying only the 9 new patch files into a v1.47.0 build did **not** compile (CI runs `40481673934`, `40483664233`, `40484525293`): the new patches rely on new Patcher APIs, new library methods, generated protobuf classes and updated shared fingerprints.

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

## ✅ Implemented: YouTube-only sync that adds the 9 new patches

The **9 new YouTube patches** were added. Their Kotlin/Java sources are version-locked to upstream v1.48.0 shared code, so a purely additive file copy did **not** compile: CI runs `40481673934`, `40483664233` and `40484525293` failed one dependency layer at a time (`interfaces`/`isStatic` fingerprint parameters, `listDecodableFiles`, new `morphe-patches-library` APIs, generated protobuf classes…). The fix was to align the **whole YouTube-only source tree** with v1.48.0, which makes every file come from the same upstream revision:

| Item | Result |
| --- | --- |
| YouTube patch Kotlin sources, extension Java/proto/resources | aligned with upstream v1.48.0 (1,898 files considered; 389 updated, 6 added, 5 deleted, **0 merge conflicts**) |
| Music / Reddit patch or extension files | **0** added |
| Net new patches visible to users | exactly the **9** from v1.48.0 (`Force system font` → `Custom font`) |
| Build | `gradle/libs.versions.toml`, `settings.gradle.kts`, `patches/build.gradle.kts` moved to morphe-patcher **2.0.0** / patches-library **2.0.0** (Java 17 toolchain, foojay resolver) |
| `gradle.properties` / `patches-list.json` | `version = 1.48.0`; manifest 110 entries (105 YouTube + 5 generic) |
| Local customisations preserved | Khmer TTS `voiceovertranslation/*` incl. `KhmerTtsClient.java`, Khmer/default YouTube strings, YouTube-only `AddResourcesPatch`/`CheckStringResources`, fork metadata, `Settings.java` Khmer speed/pitch entries |

The compiled `patch.mpp` is rebuilt by `.github/workflows/build-mpp.yml` and declares `Patcher-Version: 2.0.0`, so users need a Manager/Patcher that supports 2.0.

**Not done deliberately:** the v1.49.0-dev.7 patches (`Download post images`, `Search comments`), the YouTube `21.43.523` target, upstream's Edge TTS rewrite of the voice-over client, and the Music/Reddit patch sets. `tools/generate-patch-catalog.py` regenerates the README `<details>` catalogue from the manifest; the version advisor catalog/docs were regenerated too (21 unit tests pass).

## Sources

- https://github.com/MorpheApp/morphe-patches/releases/tag/v1.48.0
- https://github.com/MorpheApp/morphe-patches/releases/tag/v1.49.0-dev.7
- https://github.com/MorpheApp/morphe-patches/compare/v1.47.0...v1.48.0
- `patches-list.json` at `v1.48.0` / `v1.49.0-dev.7` / `main`
- Source tarballs compared locally: `v1.47.0`, `v1.48.0`, `v1.49.0-dev.7`
