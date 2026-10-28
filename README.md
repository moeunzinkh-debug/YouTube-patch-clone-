# YouTube Patch Clone (unofficial source subset)


## Active Google / Gemini bundle

Use [`bundles/gemini/bundle.mpp`](bundles/gemini/bundle.mpp), local **0.2.0**.
The new process identity patch replaces the old process-name spoofing patch in
this build. Old 0.1.x binaries and the duplicate experimental workflow have been
removed. The upstream catalog below is **legacy reference material**, not the
active bundle's compatibility list. Supporting GMS/manifest patches are retained;
this is not an entirely rewritten GMS implementation. Google/Gemini APK patch and
rebuild tests pass, but device launch/login/chat are **not verified**.
See [current bundle instructions](bundles/gemini/README.md). YouTube is separate.


This repository contains a **YouTube-focused source subset** of [MorpheApp/morphe-patches](https://github.com/MorpheApp/morphe-patches), with an additional Khmer voice-over TTS integration. It is a patch-source project, **not** a YouTube app or a ready-to-install APK.

> **Scope:** the compiled `patch.mpp` contains **only the YouTube patch set**. Shared support code is retained where the YouTube patches need it; the separate YouTube Music and Reddit patch sets are not included. A **separate, non-compiled** Gemini/MicroG RE patch source is vendored under `extras/gemini-microg-patches/` for reference (see the Gemini patch tags below).
>
> កំណត់សម្គាល់៖ យកតែផ្នែក YouTube ប៉ុណ្ណោះ។ ឯកសារ shared ដែលចាំបាច់សម្រាប់ YouTube នៅតែមាន ប៉ុន្តែមិនបានដាក់ patch set របស់ YouTube Music ឬ Reddit ទេ។

[![Release](https://img.shields.io/badge/release-v1.48.1-e4313c?logo=github)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/v1.48.1)
[![patch.mpp](https://img.shields.io/badge/patch.mpp-9.8%20MiB-3157d5)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/download/v1.48.1/patch.mpp)
[![YouTube stable](https://img.shields.io/badge/YouTube%20stable-21.23.492-14835b)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/tree/youtube-21.23.492)
[![YouTube latest](https://img.shields.io/badge/YouTube%20latest-21.42.241-a8650b)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/tree/youtube-21.42.241)
[![Upstream](https://img.shields.io/badge/upstream-v1.48.0-6a7290)](https://github.com/MorpheApp/morphe-patches/releases/tag/v1.48.0)
[![License](https://img.shields.io/badge/license-GPLv3-blue)](LICENSE)
[![Gemini patches](https://img.shields.io/badge/Gemini%20patches-13-6a5acd)](docs/gemini-microg-patches.md)
[![MicroG RE](https://img.shields.io/badge/MicroG%20RE-7.0.0-2e7d32)](docs/gemini-microg-patches.md)

[![Build patch.mpp](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/build-mpp.yml/badge.svg)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/build-mpp.yml)
[![Verify patch.mpp](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/verify-mpp.yml/badge.svg)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/verify-mpp.yml)
[![Release patch.mpp](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/release-mpp.yml/badge.svg)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/release-mpp.yml)


<!-- PATCH-LIST:START -->
<details>
<summary>📦 YouTube • 105 patches</summary>

### YouTube Patches

និយាយពីអ្វីដែលមាននៅក្នុង patches ទាំងអស់ / What is inside the whole patch bundle. បញ្ជីពេញខាងក្រោមគឺ 110 patches ពី [`patches-list.json`](patches-list.json) v1.48.1 (105 កំណត់គោលដៅ `com.google.android.youtube` + 5 shared/generic)។

**ឧទាហរណ៍ / Highlights**

- Remove Ads
- Background Playback
- Hide Shorts
- Custom Theme

ទាំងនេះត្រូវគ្នាជាមួយ `Hide ads`, `Remove background playback restrictions`, `Hide Shorts components` និង `Theme`។ ក្រៅពីនោះនៅមាន SponsorBlock, Return YouTube Dislike, DeArrow, Picture-in-Picture, Playback speed, Video quality, Loop video, Swipe controls, Seekbar, Downloads, Save to Watch later, Copy/share links, Spoof app version/signature, GmsCore support និង **Voice over translation** (Khmer TTS) ជាដើម។

បើកក្រុមខាងក្រោមដើម្បីមើលគ្រប់ patch / Expand a group to see every patch name:

<details>
<summary>✨ ថ្មីពី v1.48.0 / New in v1.48.0 • 9</summary>

- `Ask flyout menu`
- `Custom font`
- `Feed card layout`
- `Feed video actions`
- `Feed view count`
- `Force animations`
- `Series tracking`
- `Skip live Shorts`
- `Video delay`

</details>

<details>
<summary>🚫 ពាណិជ្ជកម្ម & ការរំខាន / Ads & distractions • 20</summary>

- `AI channel filter`
- `Channel whitelist`
- `DeArrow`
- `Hide ads`
- `Hide autoplay preview`
- `Hide end screen cards`
- `Hide end screen suggested video`
- `Hide info cards`
- `Hide layout components`
- `Hide player flyout menu components`
- `Hide player overlay buttons`
- `Hide related video overlay`
- `Hide related videos`
- `Hide status bar`
- `Hide timestamp`
- `Hide video action buttons`
- `Remove viewer discretion dialog`
- `Restore original titles`
- `Return YouTube Dislike`
- `SponsorBlock`

</details>

<details>
<summary>▶️ ការចាក់វីដេអូ / Playback & video • 22</summary>

- `Captions`
- `Double tap to seek`
- `Exit fullscreen mode`
- `Force fullscreen landscape`
- `Force original audio`
- `Fullscreen video scale`
- `Loop video`
- `Media notification controls`
- `Miniplayer`
- `Mute button`
- `Open videos fullscreen`
- `Picture-in-picture button`
- `Play all`
- `Playback buffer`
- `Playback in feeds`
- `Playback speed`
- `Reload video`
- `Remember live stream playback position`
- `Remove background playback restrictions`
- `Seekbar`
- `Skip silence`
- `Video quality`

</details>

<details>
<summary>📱 Shorts • 5</summary>

- `Disable Shorts resuming on startup`
- `Hide Shorts components`
- `Open Shorts in regular player`
- `Shorts autoplay`
- `Shorts icon style`

</details>

<details>
<summary>🎨 រូបរាង & អេក្រង់ / Theme, layout & player UI • 14</summary>

- `Ambient mode`
- `App refresh rate`
- `Change form factor`
- `Change header`
- `Change start page`
- `Custom branding`
- `Custom player overlay opacity`
- `Navigation bar`
- `Override YouTube Music buttons`
- `Player icon style`
- `Settings menu filter`
- `Swipe controls`
- `Theme`
- `Wide search bar`

</details>

<details>
<summary>⚙️ បិទ/បើកមុខងារ / Behaviour toggles • 15</summary>

- `Disable auto feed refresh`
- `Disable continue watching prompt`
- `Disable double tap actions`
- `Disable DRC audio`
- `Disable fullscreen gestures`
- `Disable haptic feedback`
- `Disable layout updates`
- `Disable Play Store updates`
- `Disable player popup panels`
- `Disable playlist autoplay`
- `Disable QUIC protocol`
- `Disable rolling number animations`
- `Disable scrolling speed limit`
- `Disable sign in to TV popup`
- `Disable video codecs`

</details>

<details>
<summary>🌐 បណ្តាញ & គណនី / Network, spoofing & account • 13</summary>

- `Bypass image region restrictions`
- `Bypass link redirects`
- `Change installer source`
- `Check watch history domain name resolution`
- `Enable debugging`
- `GmsCore support`
- `Network proxy`
- `Override certificate pinning`
- `PoToken provider`
- `Spoof app version`
- `Spoof device dimensions`
- `Spoof signature`
- `Spoof video streams`

</details>

<details>
<summary>🧰 ចែករំលែក & ឧបករណ៍ / Sharing & tools • 12</summary>

- `Add to queue`
- `Channel search`
- `Clone app`
- `Copy text`
- `Copy video link`
- `Downloads`
- `Open channel of live avatar`
- `Open links externally`
- `Open system share sheet`
- `Sanitize sharing links`
- `Save to Watch later`
- `Voice over translation`

</details>

> ចំណាំ៖ ក្រុម «ថ្មីពី v1.48.0» គឺជា patches ដែលបានបន្ថែមពី upstream v1.48.0។ ស្លាក `youtube-*` មិនបន្ថែម patch ថ្មីទេ — ការបន្ថែមកំណែ YouTube ថ្មីត្រូវការ sync កូដ patch ពី upstream មុន។

</details>
<!-- PATCH-LIST:END -->

<!-- GEMINI-PATCH-LIST:START -->
<details>
<summary>🤖 Gemini / MicroG RE • 13 patches (vendored v0.1.1, separate source)</summary>

### Gemini patch tags / ស្លាក patch សម្រាប់ Gemini

Cloned from [ryuya0124/gemini-microg-patches](https://github.com/ryuya0124/gemini-microg-patches) tag `v0.1.1`. These patches make **Gemini** work with **microG RE** (`app.revanced.android.gms` 7.0.0), including Samsung Secure Folder / work profile (user 150). They target the Google app and Gemini launcher — **not YouTube**.

[![MicroG RE](https://img.shields.io/badge/MicroG%20RE-7.0.0-2e7d32)](docs/gemini-microg-patches.md) [![Google App](https://img.shields.io/badge/Google-17.54.18.ve.arm64-4285F4)](docs/gemini-microg-patches.md) [![Gemini](https://img.shields.io/badge/Gemini-1.0.958859967-6a5acd)](docs/gemini-microg-patches.md)

> ⚠️ **Reference source only** — this directory is outside the Gradle source sets, so it is **not compiled into `patch.mpp`**. To use these patches, add the upstream repo as a separate Manager source or import its `.mpp`. See [`docs/gemini-microg-patches.md`](docs/gemini-microg-patches.md) and the vendored [`README`](extras/gemini-microg-patches/README.md).

| Target | Package | Version |
| --- | --- | --- |
| Google App (AGSA) | `com.google.android.googlequicksearchbox` | `17.54.18.ve.arm64` |
| Gemini launcher | `com.google.android.apps.bard` | `1.0.958859967` |
| microG RE | `app.revanced.android.gms` | `7.0.0` |

បើកក្រុមខាងក្រោមដើម្បីមើល patches ទាំងអស់ / Expand a group to see every patch:

<details>
<summary>🔐 MicroG RE / GmsCore • 4</summary>

- `GmsCore Bytecode Redirect (MicroG RE 7.0.0)`
- `GmsCore Signature and Availability Bypass`
- `Google App Manifest Tweaks`
- `MicroG Account Permissions`

</details>

<details>
<summary>🤖 Gemini launcher • 2</summary>

- `Gemini Redirect to Cloned Google App`
- `Gemini Standalone Support`

</details>

<details>
<summary>📦 Google App clone • 2</summary>

- `Google App Package Clone Support`
- `Process Name Spoofing for Clone Support`

</details>

<details>
<summary>💼 Work profile / Secure Folder • 2</summary>

- `Allow Work Profile Gemini Eligibility`
- `Bypass Work Profile Gemini Restriction`

</details>

<details>
<summary>👤 Account sync (off by default) • 3</summary>

- `Account ID Fallback for Clone` — *disabled by default*
- `Account Switch Lock Bypass` — *disabled by default*
- `Account Sync Binder Loop Fix` — *disabled by default*

</details>

> ចំណាំ៖ ស្លាក `gemini-*`, `google-*` និង `microg-re-*` ជា tags សម្រាប់សម្គាល់ កំណែដែលបានផ្ទៀងផ្ទាត់ (verified targets) — វាមិនបន្ថែម patch ថ្មីទេ។ Do not apply YouTube patches to Google/Gemini. Upstream requires its Gemini patches plus the official `Clone app` patch; follow that specific combination, not two overlapping full patch sets.

</details>
<!-- GEMINI-PATCH-LIST:END -->

## Upstream sync / ការធ្វើបច្ចុប្បន្នភាពពី upstream

This fork is synced to the **YouTube-only source of upstream v1.48.0** (bundle release `v1.48.1`) and includes the **9 new YouTube patches** (Ask flyout menu, Custom font, Feed card layout, Feed video actions, Feed view count, Force animations, Series tracking, Skip live Shorts, Video delay) — see the «New in v1.48.0» group above. Those 9 are the net new features; to compile them the shared YouTube patch/extension sources had to be aligned with v1.48.0 (morphe-patcher 2.0.0), while our Khmer TTS package, Khmer strings, YouTube-only resource checker and fork metadata were preserved. **No YouTube Music or Reddit patches are included.** See [`docs/upstream-sync.md`](docs/upstream-sync.md) for the full comparison, the v1.49.0-dev.7 additions and the supported YouTube versions. **Recommended YouTube target: `21.23.492`** — the same as upstream (Manager recommends the newest non-experimental target; `21.23.492` was promoted to stable upstream in v1.49.0-dev.7).

## Gemini / MicroG RE patches (separate source)

The Gemini patch tags above document **13 cloned patches** from [ryuya0124/gemini-microg-patches](https://github.com/ryuya0124/gemini-microg-patches) `v0.1.1`, vendored under [`extras/gemini-microg-patches/`](extras/gemini-microg-patches/README.md). They add **Gemini + microG RE (`app.revanced.android.gms` 7.0.0) support**, including Samsung Secure Folder, for Google App `17.54.18.ve.arm64` and Gemini `1.0.958859967`. **They are reference source only — not compiled into `patch.mpp`.** Add the upstream repo as a separate Manager source, using the specific upstream-required combination with the official `Clone app` patch, not the YouTube patch set. Proposed Git tag names (not published): `gemini-v0.1.1`, `gemini-1.0.958859967`, `google-17.54.18.ve.arm64`, `microg-re-7.0.0`. Full guide: [`docs/gemini-microg-patches.md`](docs/gemini-microg-patches.md).

## Automatic Gemini version recommendations

[Google / Gemini / MicroG RE version catalog](docs/gemini-versions.md) — checked every six hours by GitHub Actions once the workflow is on the default branch.
Requested targets: **Google 17.6.59.ve.arm64**, **Gemini 1.0.995038376**, **MicroG RE 7.3.0**.
These targets are **unverified**, not supported-version declarations. Recommendations stay pinned to reviewed source profiles; upstream discovery never silently enables unsupported APKs. The compiled YouTube bundle is unchanged.
