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
- Khmer voice-over synthesis routed directly to Takumi's `POST /api/process-multi` using the multipart contract verified in MST-DUBBERS (Piseth and Sreymom voices); no OpenAPI discovery is required.
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
Android SDK 36 ដែលមានស្រាប់លើ runner `ubuntu-24.04` និង Gradle wrapper របស់គម្រោង ដើម្បីដំណើរការ
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

### Manager error: `MORPHE_BRANDING.TXT` already exists

This is a branding/license dependency failure, not evidence that **Feed video actions**
itself is broken. The marker can already be present in a previously patched input APK,
or an overlapping patch source can have written it in the current session. A log listing
both sources is a reason to check the selected patches, but does not by itself prove
that both sources executed.

**Recovery / របៀបដោះស្រាយ៖**

1. ចាប់ផ្ដើម patching session ថ្មី។ ជ្រើសឯកសារ YouTube APK ដើម ដែលមិនទាន់បាន patch
   (`com.google.android.youtube`) មិនមែន APK output ពីការធ្វើ patch មុន ឬ APK ដែលបានដកពី
   កម្មវិធី Morphe ដែលបានដំឡើងរួចទេ។
2. សម្រាប់ Khmer TTS សូមជ្រើស patches ពី **YouTube Patch Clone (unofficial Morphe subset)**
   តែមួយប៉ុណ្ណោះ។ ដោះជម្រើស patches ពី **Morphe Patches** ដើម សម្រាប់ session នេះ។
   Clone មាន YouTube patches និង shared dependencies ចាំបាច់រួចហើយ មិនមែនជា add-on
   សម្រាប់ដាក់ពីលើ source ដើមទេ។ ចំនួន patches ដែលបានជ្រើសមិនអាចបញ្ជាក់ថាគ្មានការត្រួតគ្នាទេ។
3. បើមិនអាចបែងចែក source ក្នុងការជ្រើស patches បាន សូមបិទ source ដែលមិនប្រើជាបណ្ដោះអាសន្ន
   រួចជ្រើស patches ឡើងវិញ។ កុំលុបទិន្នន័យ Manager ឬលុបកម្មវិធី YouTube ដើម្បីដោះស្រាយ error នេះ។
4. YouTube **21.20.405** មានក្នុងបញ្ជី compatibility របស់ clone ហើយ Android 10 (API 29)
   ខ្ពស់ជាង minimum API 28 សម្រាប់ version នេះ។ ប៉ុន្តែ log នេះមិនទាន់បញ្ជាក់ថា patches
   ផ្សេងៗនឹងដំណើរការជាមួយ Manager/Patcher dev versions ដែលបានប្រើទេ។
5. បើនៅតែបរាជ័យ សូមផ្ញើ log ថ្មី បញ្ជាក់ថាបានប្រើ APK ដើម និងជ្រើស source តែមួយ
   រួមជាមួយ versions របស់ Manager, Patcher និង patch bundle។

Do **not** delete `MORPHE_BRANDING.TXT`, skip the license dependency, or force overwriting
license files. That does not undo earlier bytecode/resource modifications and can lead
to a broken APK. The collision check and all bundled license notices remain enabled.

### Voice-over / Khmer TTS troubleshooting

- Khmer (`km` / `km-KH`) uses the configured Takumi HTTPS service, not the phone's
  Android TTS engine. An installed Android voice cannot repair a server-side failure.
- Select Khmer as the Voice-over caption/target language, enable Voice-over for the
  current video, and check that translation volume is above zero. Try the voice test
  button separately from a video: a successful test with silent video narration points
  toward captions/translation/scheduling rather than synthesis alone.
- A synthesis failure or empty response now releases the playback busy flag and restores
  original video volume; later segments are no longer blocked indefinitely. Stale failures
  after a seek/video change cannot cancel the new playback session.
- The Khmer client expects audio bytes directly, rejects empty/text responses, bounds
  response size, and does not follow redirects or guess other endpoints.
- These changes do not prove the external service is online. If speech still fails, provide the runtime Voice-over error log (not just
  the patching log), selected target language, and whether the voice test succeeds.

Run local JVM regression tests with Java 21 and the Android SDK configured:
`./gradlew :tts-tests:test`.
The standalone JVM test module compiles the actual production HTTP client and exercises
its multipart request and response handling with a local HTTP server, not the live TTS service.


### Khmer TTS request contract

The integration follows [MST-DUBBERS `EdgeTtsClient.kt`](https://github.com/moeunzinkh-debug/MST-DUBBERS-/blob/42ae8de6cd37b5214974592bbc798c4474b94fc4/app/src/main/java/com/example/data/api/EdgeTtsClient.kt):

```text
POST https://takumi0002-tts-kh.hf.space/api/process-multi
Content-Type: multipart/form-data; boundary=<generated boundary>

data=[{"text":"សួស្តី","voiceName":"piseth","speed":1.0,"pitch":0}]
autoSpeed=false
```

- ជ្រើសភាសា Khmer ក្នុង Voice-over រួចជ្រើស **Piseth** ឬ **Sreymom** នៅបញ្ជីសំឡេង។
  ប៊ូតុងសាកសំឡេង ការអាន captions និង prefetch ប្រើ server និង voice ដែលបានជ្រើសដូចគ្នា។
- `voiceName` ជា `piseth` ឬ `sreymom` មិនមែនជា Edge voice ID ពេញទេ។
- Server បង្កើតសំឡេងនៅ speed `1.0` និង pitch `0`; ការកំណត់ speed/pitch របស់អ្នក
  ត្រូវបានអនុវត្តពេលចាក់សំឡេង ដើម្បីកុំឱ្យបង្កើនល្បឿនពីរដង។
- ចម្លើយដែលរំពឹងទុកគឺ audio bytes ដោយផ្ទាល់។ HTTP errors ឬ JSON/HTML មិនត្រូវបានចាក់ជាសំឡេងទេ។
- គ្មានការហៅ `/openapi.json` និងគ្មានការប្ដូរទៅ Edge/Android/Gemini ដោយស្វ័យប្រវត្តិ
  សម្រាប់ភាសាខ្មែរទេ។ Server នៅតែត្រូវមានអ៊ីនធឺណិត និងដំណើរការបាន។
