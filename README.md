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
- **Automatic YouTube version updates + phone-model analysis** in [`tools/version-advisor/`](tools/version-advisor/README.md): a catalog that refreshes itself from the upstream patch bundle (GitHub Action + server background refresh) and a bilingual (English/ខ្មែរ) advisor that recommends the YouTube version and APK variant that fit a user's phone. Current data: [`docs/youtube-versions.md`](docs/youtube-versions.md).

`shared-youtube` is kept because YouTube uses it. Some helper code in that module is reusable by YouTube Music too, but **no separate YouTube Music patch module or patch package is included**. The YouTube app also has a patch that changes its own YouTube Music buttons; that remains part of the YouTube patch set.

## Automatic version updates & phone-model analysis / ការធ្វើបច្ចុប្បន្នភាពដោយស្វ័យប្រវត្តិ

**English.** `tools/version-advisor` keeps the supported YouTube version list current without manual edits. It reads this repo's `patches-list.json`, checks the newest upstream Morphe bundle through the GitHub API (ETag-cached), and writes [`data/supported-versions.json`](tools/version-advisor/data/supported-versions.json) plus [`docs/youtube-versions.md`](docs/youtube-versions.md). A GitHub Action runs every 6 hours, and the web server also refreshes itself in the background. It then analyses a phone (Android SDK level, CPU ABI, screen density, RAM) — detected from the browser, ADB, or a 69-model database — and explains which version is suitable, distinguishing the newest *experimental* build from the recommended *stable* one, including which APK variant (`nodpi`, ABI, density) to download.

**ខ្មែរ។** `tools/version-advisor` ធ្វើបច្ចុប្បន្នភាពបញ្ជីកំណែ YouTube ដែលគាំទ្រដោយស្វ័យប្រវត្តិ ដោយអាន `patches-list.json` របស់ repository និងពិនិត្យកញ្ចប់ patch ចុងក្រោយពី upstream តាម GitHub API។ បន្ទាប់មកវាវិភាគទូរសព្ទរបស់អ្នកប្រើប្រាស់ (កម្រិត Android SDK, CPU ABI, ដង់ស៊ីតេអេក្រង់, RAM) ដែលរកឃើញពី browser, ADB ឬមូលដ្ឋានទិន្នន័យម៉ូដែលចំនួន ៦៩ ហើយប្រាប់ថាកំណែណាសាកសម — ដោយបែងចែកកំណែ «ពិសោធន៍» ថ្មីបំផុត និងកំណែ «ស្ថិរភាព» ដែលណែនាំ រួមទាំងប្រភេទ APK ដែលគួរទាញយក។

```bash
python3 tools/version-advisor/run.py update --write-docs
python3 tools/version-advisor/run.py recommend --model "SM-A546B" --lang km
python3 tools/version-advisor/run.py serve --host 0.0.0.0 --port 8000
```

The tool updates the **catalog**, not the Kotlin patch sources; adding a genuinely new target still needs a reviewed upstream source sync. See the [tool README](tools/version-advisor/README.md) for the full architecture and API.

## What's excluded

- The YouTube Music extension and patch package (`extensions/music/` and `patches/.../music/`).
- The Reddit extension and patch package (`extensions/reddit/` and `patches/.../reddit/`).
- Music- and Reddit-specific localized resource directories, tests for the excluded modules, and the upstream all-app release bundle.

## Upstream and license

This is an **unofficial, filtered derivative** of Morphe patches, based on upstream release **v1.47.0**, commit [`e5464395441e916b643af4e2175c4e253e6df487`](https://github.com/MorpheApp/morphe-patches/commit/e5464395441e916b643af4e2175c4e253e6df487) (2026-10-11). It is not affiliated with or endorsed by MorpheApp, Google, or YouTube.

The upstream project's GPLv3 license and additional notice are preserved in [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE). See [`UPSTREAM.md`](UPSTREAM.md) for the exact source revision and filtering details.
