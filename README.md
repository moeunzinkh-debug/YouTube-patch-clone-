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

## What's included

- YouTube patch implementations under `patches/src/main/kotlin/app/morphe/patches/youtube/`.
- YouTube extension code under `extensions/youtube/`.
- Common patch and build support needed by YouTube: `patches/.../all`, `patches/.../shared`, `patches/.../util`, and the `extensions/all`, `extensions/shared`, and `extensions/shared-youtube` modules.
- YouTube, shared-YouTube, shared, and SponsorBlock resources/translations required by those patches.
- `patches-list.json`, filtered to 102 entries: 97 targeting YouTube and 5 generic entries without an app-specific target.
- Khmer voice-over synthesis routed directly to the configured Takumi FastAPI Space; its route is discovered from FastAPI's `/openapi.json` at runtime.
- Separate voice-over speed and pitch controls (0.5×–2×). The original YouTube player already has its own speed/pitch controls.
- **Automatic YouTube version updates + phone-model analysis** in [`tools/version-advisor/`](tools/version-advisor/README.md): a catalog that refreshes itself from the upstream patch bundle (GitHub Action + server background refresh) and a bilingual (English/ខ្មែរ) advisor that recommends the YouTube version and APK variant that fit a user's phone. Current data: [`docs/youtube-versions.md`](docs/youtube-versions.md).
- **Release tags + Manager descriptor**: [`patches-bundle.json`](patches-bundle.json), annotated `v1.47.0` / `youtube-*` tags, release badges above, and an automated [release workflow](.github/workflows/release-mpp.yml). See [docs/releases.md](docs/releases.md).

`shared-youtube` is kept because YouTube uses it. Some helper code in that module is reusable by YouTube Music too, but **no separate YouTube Music patch module or patch package is included**. The YouTube app also has a patch that changes its own YouTube Music buttons; that remains part of the YouTube patch set.

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

> ចំណាំ៖ ស្លាក `youtube-*` មិនបន្ថែម patch ថ្មីទេ — ការបន្ថែមកំណែ YouTube ថ្មីត្រូវការ sync កូដ patch ពី upstream មុន។

</details>
<!-- PATCH-LIST:END -->

## Automatic version updates & phone-model analysis / ការធ្វើបច្ចុប្បន្នភាពដោយស្វ័យប្រវត្តិ

**English.** `tools/version-advisor` keeps the supported YouTube version list current without manual edits. It reads this repo's `patches-list.json`, checks the newest upstream Morphe bundle through the GitHub API (ETag-cached), and writes [`data/supported-versions.json`](tools/version-advisor/data/supported-versions.json) plus [`docs/youtube-versions.md`](docs/youtube-versions.md). A GitHub Action runs every 6 hours, and the web server also refreshes itself in the background. It then analyses a phone (Android SDK level, CPU ABI, screen density, RAM) — detected from the browser, ADB, or a 69-model database — and explains which version is suitable, distinguishing the newest *experimental* build from the recommended *stable* one, including which APK variant (`nodpi`, ABI, density) to download.

**ខ្មែរ។** `tools/version-advisor` ធ្វើបច្ចុប្បន្នភាពបញ្ជីកំណែ YouTube ដែលគាំទ្រដោយស្វ័យប្រវត្តិ ដោយអាន `patches-list.json` របស់ repository និងពិនិត្យកញ្ចប់ patch ចុងក្រោយពី upstream តាម GitHub API។ បន្ទាប់មកវាវិភាគទូរសព្ទរបស់អ្នកប្រើប្រាស់ (កម្រិត Android SDK, CPU ABI, ដង់ស៊ីតេអេក្រង់, RAM) ដែលរកឃើញពី browser, ADB ឬមូលដ្ឋានទិន្នន័យម៉ូដែលចំនួន ៦៩ ហើយប្រាប់ថាកំណែណាសាកសម — ដោយបែងចែកកំណែ «ពិសោធន៍» ថ្មីបំផុត និងកំណែ «ស្ថិរភាព» ដែលណែនាំ រួមទាំងប្រភេទ APK ដែលគួរទាញយក។

```bash
python3 tools/version-advisor/run.py update --write-docs
python3 tools/version-advisor/run.py recommend --model "SM-A546B" --lang km
python3 tools/version-advisor/run.py serve --host 0.0.0.0 --port 8000
```

The tool updates the **catalog**, not the Kotlin patch sources; adding a genuinely new target still needs a reviewed upstream source sync. See the [tool README](tools/version-advisor/README.md) for the full architecture and API.

## Build `patch.mpp`

`patch.mpp` at the repository root is the compiled **Morphe Patch Package** (JAR + extension DEX) built from these sources by `./gradlew :patches:buildAndroid`. It is what Morphe Desktop/Manager imports to patch an original YouTube APK — it is not an APK itself. Its SHA-256 is in `patch.mpp.sha256`.

Because compilation needs JDK 21, Android SDK 36 and the Morphe GitHub Packages plugin, the build runs in [`.github/workflows/build-mpp.yml`](.github/workflows/build-mpp.yml) and publishes the bundle back to the branch. Locally:

```bash
./gradlew :patches:buildAndroid --no-daemon
cp "$(ls patches/build/libs/patches-*.mpp | head -1)" patch.mpp
```

See [docs/building-mpp.md](docs/building-mpp.md) for prerequisites, tokens, CI usage and troubleshooting.

## Release tags / ស្លាកចេញផ្សាយ

All tags: [github.com/moeunzinkh-debug/YouTube-patch-clone-/tags](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/tags). Full policy: [docs/releases.md](docs/releases.md).

| Tag | ប្រភេទ / Type | អត្ថន័យ / Meaning |
| --- | --- | --- |
| [`v1.47.0`](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/releases/tag/v1.47.0) | annotated + **GitHub Release** | Compiled `patch.mpp` bundle (version from `gradle.properties`), plus `patch.mpp.sha256` and [`patches-bundle.json`](patches-bundle.json). |
| [`youtube-21.20.405`](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/tree/youtube-21.20.405) | annotated | Recommended **stable** YouTube target — min Android 9 / SDK 28. |
| [`youtube-21.40.161`](https://github.com/moeunzinkh-debug/YouTube-patch-clone-/tree/youtube-21.40.161) | annotated | Newest **experimental** YouTube target — min Android 10 / SDK 29. |

**Naming / ឈ្មោះស្លាក៖** `v<major.minor.patch>` = patch-bundle release (pushing it creates the GitHub Release automatically via [`release-mpp.yml`](.github/workflows/release-mpp.yml)); `youtube-<version>` = marker for a supported YouTube target. All three tags point to the same source revision — only `v1.47.0` carries release assets.

**Supported YouTube targets (9):** `21.40.161`, `21.39.522`, `21.38.130`, `21.28.208`, `21.23.492` (experimental), `21.20.405`, `21.16.256`, `20.51.39`, `20.21.37` (stable). See [docs/youtube-versions.md](docs/youtube-versions.md) and use the [version advisor](tools/version-advisor/README.md) to match a phone.

```bash
sha256sum -c patch.mpp.sha256                       # verify the downloaded bundle
git tag -a v1.48.0 -m "YouTube patch bundle v1.48.0"
git push origin v1.48.0                             # CI publishes the release
```

> `patches-bundle.json` is the Morphe Manager source descriptor. Add this repo with `https://morphe.software/add-source?github=moeunzinkh-debug/YouTube-patch-clone-`, or import `patch.mpp` directly in Morphe Desktop. A `youtube-*` tag alone does not make a new YouTube version patchable — the Kotlin patch sources must be synced from upstream first.

## What's excluded

- The YouTube Music extension and patch package (`extensions/music/` and `patches/.../music/`).
- The Reddit extension and patch package (`extensions/reddit/` and `patches/.../reddit/`).
- Music- and Reddit-specific localized resource directories, tests for the excluded modules, and the upstream all-app release bundle.

## Upstream and license

This is an **unofficial, filtered derivative** of Morphe patches, based on upstream release **v1.47.0**, commit [`e5464395441e916b643af4e2175c4e253e6df487`](https://github.com/MorpheApp/morphe-patches/commit/e5464395441e916b643af4e2175c4e253e6df487) (2026-10-11). It is not affiliated with or endorsed by MorpheApp, Google, or YouTube.

The upstream project's GPLv3 license and additional notice are preserved in [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE). See [`UPSTREAM.md`](UPSTREAM.md) for the exact source revision and filtering details.
