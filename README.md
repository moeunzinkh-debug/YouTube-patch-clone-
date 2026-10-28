# YouTube Patch Clone (unofficial source subset)

This repository contains a **YouTube-focused source subset** of [MorpheApp/morphe-patches](https://github.com/MorpheApp/morphe-patches), with an additional Khmer voice-over TTS integration. It is a patch-source project, **not** a YouTube app or a ready-to-install APK.

> **Scope:** the compiled `patch.mpp` contains **only the YouTube patch set**. Shared support code is retained where the YouTube patches need it; the separate YouTube Music and Reddit patch sets are not included.
>
> កំណត់សម្គាល់៖ យកតែផ្នែក YouTube ប៉ុណ្ណោះ។ ឯកសារ shared ដែលចាំបាច់សម្រាប់ YouTube នៅតែមាន ប៉ុន្តែមិនបានដាក់ patch set របស់ YouTube Music ឬ Reddit ទេ។

[![Release](https://img.shields.io/badge/release-v1.49.0-e4313c?logo=github)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/v1.49.0)
[![patch.mpp](https://img.shields.io/badge/patch.mpp-9.8%20MiB-3157d5)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/download/v1.49.0/patch.mpp)
[![YouTube stable](https://img.shields.io/badge/YouTube%20stable-21.23.492-14835b)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/tree/youtube-21.23.492)
[![YouTube latest](https://img.shields.io/badge/YouTube%20latest-21.42.241-a8650b)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/tree/youtube-21.42.241)
[![Upstream](https://img.shields.io/badge/upstream-v1.48.0-6a7290)](https://github.com/MorpheApp/morphe-patches/releases/tag/v1.48.0)
[![License](https://img.shields.io/badge/license-GPLv3-blue)](LICENSE)

[![Build patch.mpp](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/build-mpp.yml/badge.svg)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/build-mpp.yml)
[![Verify patch.mpp](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/verify-mpp.yml/badge.svg)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/verify-mpp.yml)
[![Release patch.mpp](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/release-mpp.yml/badge.svg)](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/workflows/release-mpp.yml)

<details>
<summary>🗨️ SimSimi • 5 experimental patches (separate bundle)</summary>

For **SimSimi 9.2.3**, import [`bundles/simsimi/bundle.mpp`](bundles/simsimi/bundle.mpp)
into Morphe Manager. This is separate from the YouTube `patch.mpp`.

- **Disable ad eligibility (experimental)** — shared ad gate, not proven complete SDK removal.
- **Unlock membership UI (client only, experimental)** — local gates only, not server entitlements/items/read receipts.
- **Pull down to restart chat (experimental)** — gesture on the English Conversation list only (not inside chat rooms), requesting React runtime reload, not process termination.
- **Daily bonus without video (client path, experimental)** — opt-in existing non-video flow; original server calls/errors retained, server rewards not guaranteed.
- **MicroG RE service routing (experimental)** — opt-in native routing, not full GMS compatibility.

The actual `.mpp` was successfully applied to the original APK with Morphe's engine
([CI proof](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/actions/runs/40654752231));
output Hermes, native hook, extension, 66 routed literals and manifest checks passed.
**New Conversation-only reload and daily-bonus flow are not yet device-tested.**
Matching splits are required for installation. See the
[full catalog and limitations](bundles/simsimi/README.md). No SimSimi release published.

</details>

<!-- PATCH-LIST:START -->
<details>
<summary>📦 YouTube • 106 patches</summary>

### YouTube Patches

និយាយពីអ្វីដែលមាននៅក្នុង patches ទាំងអស់ / What is inside the whole patch bundle. បញ្ជីពេញខាងក្រោមគឺ 111 patches ពី [`patches-list.json`](patches-list.json) v1.49.0 (106 កំណត់គោលដៅ `com.google.android.youtube` + 5 shared/generic)។

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
<summary>▶️ ការចាក់វីដេអូ / Playback & video • 23</summary>

- `Audio equalizer`
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

## Upstream sync / ការធ្វើបច្ចុប្បន្នភាពពី upstream

This fork is synced to the **YouTube-only source of upstream v1.48.0** (bundle release `v1.49.0`) and includes the **9 new YouTube patches** (Ask flyout menu, Custom font, Feed card layout, Feed video actions, Feed view count, Force animations, Series tracking, Skip live Shorts, Video delay) — see the «New in v1.48.0» group above. Those 9 are the net new features; to compile them the shared YouTube patch/extension sources had to be aligned with v1.48.0 (morphe-patcher 2.0.0), while our Khmer TTS package, Khmer strings, YouTube-only resource checker and fork metadata were preserved. **No YouTube Music or Reddit patches are included.** See [`docs/upstream-sync.md`](docs/upstream-sync.md) for the full comparison, the v1.49.0-dev.7 additions and the supported YouTube versions. **Recommended YouTube target: `21.23.492`** — the same as upstream (Manager recommends the newest non-experimental target; `21.23.492` was promoted to stable upstream in v1.49.0-dev.7).

## New: in-app Audio equalizer (v1.48.2)

The branch's [`patch.mpp`](patch.mpp) includes **Audio equalizer** with device-supported
band sliders, hardware presets, enable/disable and reset to flat. Select the patch,
then open **Morphe settings → Video → Audio equalizer** while a video is playing.
Settings persist across sessions; unsupported audio engines show a status instead
of intentionally stopping playback. It does not process remote/cast audio.

[EQ usage and limitations](docs/youtube-equalizer.md). CI compilation and controller
tests passed; APK/device listening tests remain pending. Release badges and the source descriptor point to **1.49.0**. Refresh your patch
source in Manager or import the release bundle to use EQ.

## v1.49.0: player EQ shortcut and SEA-LION

- Top-player EQ shortcut near CC/settings, using native relative control layout; opens the existing in-app EQ dialog.
- New SEA-LION translation provider: `https://api.sea-lion.ai/v1/`, model `aisingapore/Gemma-SEA-LION-v4-27B-IT`, with a separate masked API-key field.
- Existing translation providers remain available. Exported settings can contain API keys; do not share them.
- Android compilation and offline tests verified; live SEA-LION calls and device layout/spacing remain to be verified.
- Recommended YouTube remains **21.23.492**. This is a fork release, not a claim of a new upstream sync.

See [SEA-LION setup](docs/youtube-sealion-translation.md) and [release notes](docs/releases/v1.49.0.md).
