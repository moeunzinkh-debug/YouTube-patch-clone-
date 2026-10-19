# YouTube Patch Clone (unofficial source subset)

This repository contains a **YouTube-focused source subset** of [MorpheApp/morphe-patches](https://github.com/MorpheApp/morphe-patches), with an additional Khmer voice-over TTS integration. It is a patch-source project, **not** a YouTube app or a ready-to-install APK.

> **Scope:** only the YouTube patch set is included. Shared support code is retained where the YouTube patches need it; the separate YouTube Music and Reddit patch sets are not included.
>
> កំណត់សម្គាល់៖ យកតែផ្នែក YouTube ប៉ុណ្ណោះ។ ឯកសារ shared ដែលចាំបាច់សម្រាប់ YouTube នៅតែមាន ប៉ុន្តែមិនបានដាក់ patch set របស់ YouTube Music ឬ Reddit ទេ។

## What's included

- YouTube patch implementations under `patches/src/main/kotlin/app/morphe/patches/youtube/`.
- YouTube extension code under `extensions/youtube/`.
- Common patch and build support needed by YouTube: `patches/.../all`, `patches/.../shared`, `patches/.../util`, and the `extensions/all`, `extensions/shared`, and `extensions/shared-youtube` modules.
- YouTube, shared-YouTube, shared, and SponsorBlock resources/translations required by those patches.
- `patches-list.json`, filtered to 102 entries: 97 targeting YouTube and 5 generic entries without an app-specific target.
- Khmer voice-over synthesis routed directly to the configured Takumi FastAPI Space; its route is discovered from FastAPI's `/openapi.json` at runtime.
- Separate voice-over speed and pitch controls (0.5×–2×). The original YouTube player already has its own speed/pitch controls.

`shared-youtube` is kept because YouTube uses it. Some helper code in that module is reusable by YouTube Music too, but **no separate YouTube Music patch module or patch package is included**. The YouTube app also has a patch that changes its own YouTube Music buttons; that remains part of the YouTube patch set.

## What's excluded

- The YouTube Music extension and patch package (`extensions/music/` and `patches/.../music/`).
- The Reddit extension and patch package (`extensions/reddit/` and `patches/.../reddit/`).
- Music- and Reddit-specific localized resource directories, tests for the excluded modules, and the upstream all-app release bundle.

## Upstream and license

This is an **unofficial, filtered derivative** of Morphe patches, based on upstream release **v1.47.0**, commit [`e5464395441e916b643af4e2175c4e253e6df487`](https://github.com/MorpheApp/morphe-patches/commit/e5464395441e916b643af4e2175c4e253e6df487) (2026-10-11). It is not affiliated with or endorsed by MorpheApp, Google, or YouTube.

The upstream project's GPLv3 license and additional notice are preserved in [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE). See [`UPSTREAM.md`](UPSTREAM.md) for the exact source revision and filtering details.
