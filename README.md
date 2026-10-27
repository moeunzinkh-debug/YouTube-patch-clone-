# YouTube Patch Clone (unofficial source subset)

This repository contains a **YouTube-focused source subset** of [MorpheApp/morphe-patches](https://github.com/MorpheApp/morphe-patches), with an additional Khmer voice-over TTS integration. It is a patch-source project, **not** a YouTube app or a ready-to-install APK.

> **Scope:** only the YouTube patch set is included. Shared support code is retained where the YouTube patches need it; the separate YouTube Music and Reddit patch sets are not included.
>
> កំណត់សម្គាល់៖ យកតែផ្នែក YouTube ប៉ុណ្ណោះ។ ឯកសារ shared ដែលចាំបាច់សម្រាប់ YouTube នៅតែមាន ប៉ុន្តែមិនបានដាក់ patch set របស់ YouTube Music ឬ Reddit ទេ។

[![Release](https://img.shields.io/badge/release-v1.47.0-e4313c?logo=github)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/v1.47.0)
[![patch.mpp](https://img.shields.io/badge/patch.mpp-8.8%20MiB-3157d5)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/download/v1.47.0/patch.mpp)
[![YouTube stable](https://img.shields.io/badge/YouTube%20stable-21.20.405-14835b)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/tree/youtube-21.20.405)
[![YouTube latest](https://img.shields.io/badge/YouTube%20latest-21.40.161-a8650b)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/tree/youtube-21.40.161)
[![Upstream](https://img.shields.io/badge/upstream-v1.47.0-6a7290)](https://github.com/MorpheApp/morphe-patches/releases/tag/v1.47.0)
[![License](https://img.shields.io/badge/license-GPLv3-blue)](LICENSE)

[![Build patch.mpp](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/build-mpp.yml/badge.svg)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/build-mpp.yml)
[![Verify patch.mpp](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/verify-mpp.yml/badge.svg)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/verify-mpp.yml)
[![Release patch.mpp](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/release-mpp.yml/badge.svg)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/release-mpp.yml)


<!-- PATCH-LIST:START -->
<details>
<summary>📦 YouTube • 105 patches</summary>

### YouTube Patches

និយាយពីអ្វីដែលមាននៅក្នុង patches ទាំងអស់ / What is inside the whole patch bundle. បញ្ជីពេញខាងក្រោមគឺ ១០២ patches ដែលបានកត់ត្រាក្នុង [`patches-list.json`](patches-list.json) v1.47.0 (៩៧ កំណត់គោលដៅ `com.google.android.youtube` + ៥ shared/generic)។

**ឧទាហរណ៍ / Highlights**

- Remove Ads
- Background Playback
- Hide Shorts
- Custom Theme

ទាំងនេះត្រូវគ្នាជាមួយ `Hide ads`, `Remove background playback restrictions`, `Hide Shorts components` និង `Theme`។ ក្រៅពីនោះនៅមាន SponsorBlock, Return YouTube Dislike, DeArrow, Picture-in-Picture, Playback speed, Video quality, Loop video, Swipe controls, Seekbar, Downloads, Save to Watch later, Copy/share links, Spoof app version/signature, GmsCore support និង **Voice over translation** (Khmer TTS) ជាដើម។

បើកក្រុមខាងក្រោមដើម្បីមើលគ្រប់ patch / Expand a group to see every patch name:

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
<summary>▶️ ការចាក់វីដេអូ / Playback & video • 21</summary>

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
<summary>🎨 រូបរាង & អេក្រង់ / Theme, layout & player UI • 16</summary>

- `Ambient mode`
- `App refresh rate`
- `Change form factor`
- `Change header`
- `Change start page`
- `Custom branding`
- `Custom player overlay opacity`
- `Force system font`
- `Navigation bar`
- `Override YouTube Music buttons`
- `Player icon style`
- `Seekbar`
- `Settings menu filter`
- `Swipe controls`
- `Theme`
- `Wide search bar`

</details>

<details>
<summary>⚙️ បិទ/បើកមុខងារ / Behaviour toggles • 15</summary>

- `Disable DRC audio`
- `Disable Play Store updates`
- `Disable QUIC protocol`
- `Disable auto feed refresh`
- `Disable continue watching prompt`
- `Disable double tap actions`
- `Disable fullscreen gestures`
- `Disable haptic feedback`
- `Disable layout updates`
- `Disable player popup panels`
- `Disable playlist autoplay`
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

</details>
<!-- PATCH-LIST:END -->

## Upstream sync / ការធ្វើបច្ចុប្បន្នភាពពី upstream

This fork is based on v1.47.0. See [`docs/upstream-sync.md`](docs/upstream-sync.md) for what [MorpheApp/morphe-patches](https://github.com/MorpheApp/morphe-patches) added in **v1.48.0** (9 new YouTube patches incl. Ask flyout menu, Custom font, Feed card layout, Series tracking, Video delay…) and **v1.49.0-dev.7** (+2), the new YouTube versions, the Patcher 2.0 migration, and the plan to port them while keeping only YouTube patches and our Khmer TTS.
