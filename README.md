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

## Build `YouTube patch.mpp` តាម GitHub Actions

Workflow ស្ថិតនៅ [`.github/workflows/build.yml`](.github/workflows/build.yml)។ វាប្រើ Java 21,
Android SDK 36 និង Gradle wrapper របស់គម្រោង ដើម្បីដំណើរការ
`./gradlew :patches:buildAndroid --no-daemon --stacktrace`។ Task នេះបង្កើត patch bundle
សម្រាប់ Android ដែលមាន `classes.dex` មិនមែនគ្រាន់តែប្ដូរឈ្មោះឯកសារ JAR ទេ។

### របៀប build និងទាញយក

1. Push កូដដែលមាន workflow នេះទៅ GitHub។ វានឹង build ដោយស្វ័យប្រវត្តិពេល push ទៅ
   `main` ឬ `arena/febd3d83-youtube-patch-clone` និងពេលបើក pull request ទៅ `main`។
2. សម្រាប់ការចាប់ផ្ដើមដោយដៃ៖ ពេល workflow មាននៅលើ default branch រួច ចូលផ្ទាំង
   **Actions → Build YouTube patch → Run workflow** រួចជ្រើស branch និងចុច **Run workflow**។
3. រង់ចាំ job **Build YouTube patch.mpp** បញ្ចប់ដោយជោគជ័យ។
4. ចូល workflow run នោះ រួចទាញយក **YouTube-patch** នៅផ្នែក **Artifacts**។
5. ពន្លាឯកសារ ZIP ដែលបានទាញយក នោះអ្នកនឹងបាន **`YouTube patch.mpp`**។
   Artifact ត្រូវបានរក្សាទុករយៈពេល 14 ថ្ងៃ។

> **សំខាន់៖** `.mpp` ជា Morphe patch bundle សម្រាប់ប្រើជាមួយកម្មវិធី patch ដែលគាំទ្រ
> មិនមែនជា YouTube APK ដែលអាចដំឡើងផ្ទាល់ទេ។

### បើ build បរាជ័យ

- បើជួប `401`, `403` ឬបញ្ហាទាញយក Morphe dependencies ពី GitHub Packages សូមពិនិត្យ
  log របស់ step **Build Android patch bundle**។ Workflow ប្រើ `GITHUB_TOKEN`
  ដែល GitHub បង្កើតដោយស្វ័យប្រវត្តិ និង permission `packages: read`។ Package ខាង upstream
  ក៏ត្រូវអនុញ្ញាតឱ្យ repository នេះអានផងដែរ; permission ក្នុង workflow តែឯងមិនអាចផ្ដល់
  សិទ្ធិទៅ package ដែលបានរឹតបន្តឹងបានទេ។ កុំដាក់ token ឬពាក្យសម្ងាត់ក្នុង source code។
- បើរក dependency ឬ Gradle version មិនឃើញ សូមផ្ទៀងផ្ទាត់ version ក្នុង
  `gradle/libs.versions.toml`, `settings.gradle.kts` និង
  `gradle/wrapper/gradle-wrapper.properties` ជាមួយ upstream មុនប្ដូរ។
- Workflow នឹងមិន upload artifact ទេ ប្រសិនបើ build បរាជ័យ ឬ bundle មិនមាន `classes.dex`។
